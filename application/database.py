import os
import json
import socket
import shutil
from datetime import datetime, date
from typing import Any, Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json
from dotenv import load_dotenv

from supabase import create_client, Client


load_dotenv()

# ENV

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

LOCAL_DB_HOST = os.getenv("LOCAL_DB_HOST", "localhost")
LOCAL_DB_NAME = os.getenv("LOCAL_DB_NAME")
LOCAL_DB_USER = os.getenv("LOCAL_DB_USER")
LOCAL_DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD")
LOCAL_DB_PORT = os.getenv("LOCAL_DB_PORT", "5432")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

LOCAL_IMAGE_ROOT = os.getenv("LOCAL_IMAGE_ROOT", "local_filestore")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "filestore")

if not LOCAL_DB_NAME or not LOCAL_DB_USER or not LOCAL_DB_PASSWORD:
    raise ValueError("Missing LOCAL_DB_NAME / LOCAL_DB_USER / LOCAL_DB_PASSWORD in .env")


# SUPABASE CLIENT

supabase: Optional[Client] = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print("Supabase client init failed:", e)
        supabase = None


# CONNECTIONS

def get_pg_connection():
    return psycopg2.connect(
        host=LOCAL_DB_HOST,
        database=LOCAL_DB_NAME,
        user=LOCAL_DB_USER,
        password=LOCAL_DB_PASSWORD,
        port=LOCAL_DB_PORT
    )


def get_cloud_pg_connection():
    if not DB_HOST or not DB_NAME or not DB_USER or not DB_PASSWORD:
        raise ValueError("Missing DB_HOST / DB_NAME / DB_USER / DB_PASSWORD in .env")
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


# BASIC HELPERS

def load_qss_file(widget, qss_file):
    try:
        with open(qss_file, "r", encoding="utf-8") as file:
            widget.setStyleSheet(file.read())
    except Exception as e:
        print(f"Failed to load stylesheet {qss_file}: {e}")


def is_internet_available(host="8.8.8.8", port=53, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def is_supabase_available():
    if supabase is None:
        return False

    if not is_internet_available():
        return False

    try:
        supabase.table("colleges").select("id").limit(1).execute()
        return True
    except Exception:
        return False


def is_cloud_pg_available():
    if not is_internet_available():
        return False

    try:
        conn = get_cloud_pg_connection()
        conn.close()
        return True
    except Exception:
        return False


def parse_slot_data(slot_value):
    if not slot_value:
        return []

    if isinstance(slot_value, list):
        return slot_value

    if isinstance(slot_value, dict):
        return [slot_value]

    if isinstance(slot_value, str):
        try:
            parsed = json.loads(slot_value)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except Exception:
            return []

    return []


def normalize_slot_value(slot_value):
    return parse_slot_data(slot_value)


def make_json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def make_payload_json_safe(payload):
    safe = {}
    for k, v in payload.items():
        safe[k] = make_json_safe(v)
    return safe


def make_slot_column_name(start_time: str, end_time: str) -> str:
    safe_start = str(start_time).strip().replace(":", "_")
    safe_end = str(end_time).strip().replace(":", "_")
    return f"slot_{safe_start}_{safe_end}"


def get_current_active_slot(slots):
    parsed_slots = parse_slot_data(slots)
    if not parsed_slots:
        return None, None

    now = datetime.now().time()

    for slot in parsed_slots:
        try:
            start_time = datetime.strptime(slot["start"], "%H:%M").time()
            end_time = datetime.strptime(slot["end"], "%H:%M").time()
            if start_time <= now <= end_time:
                return slot, make_slot_column_name(slot["start"], slot["end"])
        except Exception as e:
            print("Invalid slot format:", e)

    return None, None


def table_exists_in_connection(conn, table_name):
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = %s
            )
        """, (table_name,))
        row = cur.fetchone()
        return bool(row[0]) if row else False
    finally:
        if cur:
            cur.close()

def get_sync_status():
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT COUNT(*) 
            FROM public.sync_queue 
            WHERE status IN ('pending', 'failed')
        """)

        count = cur.fetchone()[0]

        cur.close()
        conn.close()

        return count

    except Exception as e:
        print("Error getting sync status:", e)
        return -1


def set_camera_status(classroom_name, camera_input, is_open):
    conn = None
    cur = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO public.camera_status (classroom_name, camera_input, is_open)
            VALUES (%s, %s, %s)
            ON CONFLICT (classroom_name)
            DO UPDATE SET
                camera_input = EXCLUDED.camera_input,
                is_open = EXCLUDED.is_open
        """, (classroom_name, str(camera_input), is_open))

        conn.commit()
        return True

    except Exception as e:
        print("Error saving camera status:", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            
def get_camera_status(classroom_name):
    conn = None
    cur = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT is_open
            FROM public.camera_status
            WHERE classroom_name = %s
            LIMIT 1
        """, (classroom_name,))

        row = cur.fetchone()

        if row:
            return row[0]

        return True  

    except Exception as e:
        print("Error fetching camera status:", e)
        return True

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            

# LOCAL DATABASE INIT

def init_local_database():
    conn = None
    cur = None

    try:
        os.makedirs(LOCAL_IMAGE_ROOT, exist_ok=True)

        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS public.colleges (
            id INTEGER PRIMARY KEY,
            college_name TEXT NOT NULL,
            creator TEXT,
            creator_email TEXT,
            password TEXT
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS public.classrooms (
            id INTEGER PRIMARY KEY,
            college_id INTEGER NOT NULL,
            classroom_name TEXT NOT NULL,
            classroom_table TEXT NOT NULL,
            classroom_faces TEXT NOT NULL,
            camera_input TEXT,
            slot JSONB,
            attendance_table TEXT NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS public.local_id_counters (
            table_name TEXT PRIMARY KEY,
            last_id INTEGER NOT NULL DEFAULT 0
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS public.sync_queue (
            id SERIAL PRIMARY KEY,
            entity_type TEXT NOT NULL,
            operation TEXT NOT NULL,
            target_name TEXT NOT NULL,
            payload TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS sync_queue_status_idx
        ON public.sync_queue(status);
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS public.camera_status (
            id SERIAL PRIMARY KEY,
            classroom_name TEXT UNIQUE,
            camera_input TEXT,
            is_open BOOLEAN DEFAULT TRUE
        );
        """)

        conn.commit()
        return True

    except Exception as e:
        print("Error initializing local database:", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ID COUNTER

def get_next_local_id(table_name):
    conn = None
    cur = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO public.local_id_counters (table_name, last_id)
            VALUES (%s, 1)
            ON CONFLICT (table_name)
            DO UPDATE SET last_id = public.local_id_counters.last_id + 1
            RETURNING last_id;
        """, (table_name,))

        row = cur.fetchone()
        conn.commit()
        return row[0]

    except Exception as e:
        print("Error generating local id:", e)
        if conn:
            conn.rollback()
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# SYNC QUEUE

def enqueue_sync(entity_type, operation, target_name, payload):
    conn = None
    cur = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO public.sync_queue (entity_type, operation, target_name, payload, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """, (
            entity_type,
            operation,
            target_name,
            json.dumps(payload, default=str)
        ))

        conn.commit()
        return True

    except Exception as e:
        print("Error enqueueing sync:", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_pending_sync_jobs(limit=100):
    conn = None
    cur = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, entity_type, operation, target_name, payload
            FROM public.sync_queue
            WHERE status IN ('pending', 'failed')
            ORDER BY id ASC
            LIMIT %s
        """, (limit,))

        return cur.fetchall()

    except Exception as e:
        print("Error fetching sync jobs:", e)
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def mark_sync_done(sync_id):
    conn = None
    cur = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE public.sync_queue
            SET status = 'synced',
                updated_at = NOW(),
                error_message = NULL
            WHERE id = %s
        """, (sync_id,))

        conn.commit()

    except Exception as e:
        print("Error marking sync done:", e)
        if conn:
            conn.rollback()

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def mark_sync_failed(sync_id, error_message):
    conn = None
    cur = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE public.sync_queue
            SET status = 'failed',
                retry_count = retry_count + 1,
                error_message = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (str(error_message), sync_id))

        conn.commit()

    except Exception as e:
        print("Error marking sync failed:", e)
        if conn:
            conn.rollback()

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# DYNAMIC TABLE CREATION

def create_dynamic_student_table_in_connection(conn, table_name):
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS public.{} (
            id SERIAL PRIMARY KEY,
            college_id INTEGER NOT NULL,
            classroom_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            prn TEXT NOT NULL UNIQUE,
            img_url TEXT,
            password TEXT,
            email TEXT
        );
        """).format(sql.Identifier(table_name)))
        conn.commit()
        return True

    except Exception as e:
        print(f"Error creating student table '{table_name}':", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()


def create_dynamic_attendance_table_in_connection(conn, table_name, slots):
    cur = None
    try:
        cur = conn.cursor()

        cur.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS public.{} (
            id SERIAL PRIMARY KEY,
            college_id INTEGER NOT NULL,
            classroom_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            prn TEXT NOT NULL,
            attendance_date DATE NOT NULL
        );
        """).format(sql.Identifier(table_name)))

        parsed_slots = parse_slot_data(slots)
        for slot_item in parsed_slots:
            start_time = str(slot_item.get("start", "")).strip()
            end_time = str(slot_item.get("end", "")).strip()

            if not start_time or not end_time:
                continue

            column_name = make_slot_column_name(start_time, end_time)

            cur.execute(sql.SQL("""
                ALTER TABLE public.{}
                ADD COLUMN IF NOT EXISTS {} TEXT;
            """).format(
                sql.Identifier(table_name),
                sql.Identifier(column_name)
            ))

        index_name = f"{table_name}_prn_date_idx"
        cur.execute(sql.SQL("""
            CREATE UNIQUE INDEX IF NOT EXISTS {} ON public.{} (prn, attendance_date);
        """).format(
            sql.Identifier(index_name),
            sql.Identifier(table_name)
        ))

        conn.commit()
        return True

    except Exception as e:
        print(f"Error creating attendance table '{table_name}':", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()


def create_dynamic_student_table(table_name, slots=None):
    
    local_ok = False

    try:
        with get_pg_connection() as conn:
            local_ok = create_dynamic_student_table_in_connection(conn, table_name)
    except Exception as e:
        print("Local student table creation failed:", e)

    if is_cloud_pg_available():
        try:
            with get_cloud_pg_connection() as conn:
                create_dynamic_student_table_in_connection(conn, table_name)
        except Exception as e:
            print("Cloud student table creation failed:", e)

    return local_ok


def create_dynamic_attendance_table(table_name, slots):
    
    local_ok = False

    try:
        with get_pg_connection() as conn:
            local_ok = create_dynamic_attendance_table_in_connection(conn, table_name, slots)
    except Exception as e:
        print("Local attendance table creation failed:", e)

    if is_cloud_pg_available():
        try:
            with get_cloud_pg_connection() as conn:
                create_dynamic_attendance_table_in_connection(conn, table_name, slots)
        except Exception as e:
            print("Cloud attendance table creation failed:", e)

    return local_ok


# CLOUD -> LOCAL BASE SYNC

def pull_cloud_base_to_local():
    if not is_supabase_available():
        return False

    conn = None
    cur = None

    try:
        colleges_resp = supabase.table("colleges").select("*").execute()
        classrooms_resp = supabase.table("classrooms").select("*").execute()

        colleges = colleges_resp.data or []
        classrooms = classrooms_resp.data or []

        conn = get_pg_connection()
        cur = conn.cursor()

        for row in colleges:
            cur.execute("""
                INSERT INTO public.colleges (id, college_name, creator, creator_email, password)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id)
                DO UPDATE SET
                    college_name = EXCLUDED.college_name,
                    creator = EXCLUDED.creator,
                    creator_email = EXCLUDED.creator_email,
                    password = EXCLUDED.password
            """, (
                row["id"],
                row.get("college_name"),
                row.get("creator"),
                row.get("creator_email"),
                row.get("password")
            ))

        for row in classrooms:
            slot_value = normalize_slot_value(row.get("slot"))

            cur.execute("""
                INSERT INTO public.classrooms
                (id, college_id, classroom_name, classroom_table, classroom_faces, camera_input, slot, attendance_table)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id)
                DO UPDATE SET
                    college_id = EXCLUDED.college_id,
                    classroom_name = EXCLUDED.classroom_name,
                    classroom_table = EXCLUDED.classroom_table,
                    classroom_faces = EXCLUDED.classroom_faces,
                    camera_input = EXCLUDED.camera_input,
                    slot = EXCLUDED.slot,
                    attendance_table = EXCLUDED.attendance_table
            """, (
                row["id"],
                row.get("college_id"),
                row.get("classroom_name"),
                row.get("classroom_table"),
                row.get("classroom_faces"),
                row.get("camera_input"),
                Json(slot_value),
                row.get("attendance_table")
            ))

            create_dynamic_student_table(row["classroom_table"])
            create_dynamic_attendance_table(row["attendance_table"], slot_value)

        conn.commit()
        return True

    except Exception as e:
        print("Error pulling cloud base data:", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# CLOUD ATTENDANCE SYNC

def sync_attendance_date_to_cloud(attendance_table, attendance_date):
    if not is_supabase_available():
        return False

    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute(
            sql.SQL("SELECT * FROM public.{} WHERE attendance_date = %s").format(
                sql.Identifier(attendance_table)
            ),
            (attendance_date,)
        )

        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        for row in rows:
            payload = dict(zip(columns, row))
            payload = make_payload_json_safe(payload)
            supabase.table(attendance_table).upsert(payload).execute()

        return True

    except Exception as e:
        print("Error syncing attendance date:", e)
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# PROCESS PENDING SYNC QUEUE

def process_sync_queue():
    if not is_supabase_available():
        return False

    jobs = get_pending_sync_jobs(200)
    if not jobs:
        return True

    for job in jobs:
        sync_id, entity_type, operation, target_name, payload_text = job

        try:
            payload = json.loads(payload_text) if payload_text else {}

            if entity_type == "classrooms" and operation == "insert":
                existing = (
                    supabase.table("classrooms")
                    .select("id")
                    .eq("college_id", payload["college_id"])
                    .eq("classroom_name", payload["classroom_name"])
                    .limit(1)
                    .execute()
                )

                if existing.data:
                    supabase.table("classrooms").update(payload).eq("id", existing.data[0]["id"]).execute()
                else:
                    supabase.table("classrooms").insert(payload).execute()

            elif entity_type == "classrooms" and operation == "update":
                cloud_id = payload.get("id")
                update_payload = payload.copy()
                update_payload.pop("id", None)

                if cloud_id:
                    supabase.table("classrooms").update(update_payload).eq("id", cloud_id).execute()
                else:
                    existing = (
                        supabase.table("classrooms")
                        .select("id")
                        .eq("college_id", payload["college_id"])
                        .eq("classroom_name", payload["classroom_name"])
                        .limit(1)
                        .execute()
                    )
                    if existing.data:
                        supabase.table("classrooms").update(update_payload).eq("id", existing.data[0]["id"]).execute()
                    else:
                        supabase.table("classrooms").insert(update_payload).execute()

            elif entity_type == "dynamic_table" and operation == "insert":
                supabase.table(target_name).insert(payload).execute()

            elif entity_type == "dynamic_table" and operation == "upsert":
                supabase.table(target_name).upsert(payload).execute()

            elif entity_type == "storage_upload" and operation == "upload_file":
                folder_name = payload["folder_name"]
                local_path = payload["local_path"]
                file_name = payload["file_name"]

                ext = os.path.splitext(local_path)[1].lower()
                content_type = "image/png" if ext == ".png" else "image/jpeg"
                storage_path = f"{folder_name}/{file_name}"

                with open(local_path, "rb") as f:
                    file_bytes = f.read()

                supabase.storage.from_(SUPABASE_BUCKET).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": content_type}
                )

            elif entity_type == "attendance_sync" and operation == "sync_date":
                ok = sync_attendance_date_to_cloud(target_name, payload["attendance_date"])
                if not ok:
                    raise Exception("Attendance sync failed")

            else:
                raise Exception(f"Unknown sync job: {entity_type} / {operation}")

            mark_sync_done(sync_id)

        except Exception as e:
            print("Sync failed:", e)
            mark_sync_failed(sync_id, str(e))

    return True


# AUTH / COLLEGE

def check_college_login(name, email, college_name, password):
    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, college_name, creator, creator_email
            FROM public.colleges
            WHERE creator = %s
              AND creator_email = %s
              AND college_name = %s
              AND password = %s
            LIMIT 1
        """, (name, email, college_name, password))

        row = cur.fetchone()

        if row:
            return {
                "id": row[0],
                "college_name": row[1],
                "creator": row[2],
                "creator_email": row[3]
            }

        return None

    except Exception as e:
        print("Database error:", e)
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_college_names():
    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("SELECT college_name FROM public.colleges")
        rows = cur.fetchall()

        return sorted(list({row[0] for row in rows if row[0]}))

    except Exception as e:
        print("Error fetching college names:", e)
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# CLASSROOM CRUD

def ensure_base_classrooms_table_local():
    conn = None
    cur = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS public.classrooms (
            id INTEGER PRIMARY KEY,
            college_id INTEGER NOT NULL,
            classroom_name TEXT NOT NULL,
            classroom_table TEXT NOT NULL,
            classroom_faces TEXT NOT NULL,
            camera_input TEXT,
            slot JSONB,
            attendance_table TEXT NOT NULL
        );
        """)

        conn.commit()
        return True

    except Exception as e:
        print("Error ensuring local classrooms table:", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def add_classroom(college_id, classroom_name, camera_input, slots):
    conn = None
    cur = None

    try:
        ensure_base_classrooms_table_local()

        classroom_name = classroom_name.strip().lower()
        safe_name = classroom_name.replace(" ", "_")

        classroom_table = f"{safe_name}_table"
        classroom_faces = f"{safe_name}_faces"
        attendance_table = f"{safe_name}_attendance"
        slot_value = normalize_slot_value(slots)

        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id
            FROM public.classrooms
            WHERE college_id = %s
              AND classroom_name = %s
            LIMIT 1
        """, (college_id, classroom_name))

        if cur.fetchone():
            return {"error": "Classroom already exists"}

        local_id = get_next_local_id("classrooms")
        if local_id is None:
            return None

        cur.execute("""
            INSERT INTO public.classrooms
            (id, college_id, classroom_name, classroom_table, classroom_faces, camera_input, slot, attendance_table)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            local_id,
            college_id,
            classroom_name,
            classroom_table,
            classroom_faces,
            str(camera_input),
            Json(slot_value),
            attendance_table
        ))

        conn.commit()

        students_ok = create_dynamic_student_table(classroom_table)
        attendance_ok = create_dynamic_attendance_table(attendance_table, slot_value)

        if not students_ok or not attendance_ok:
            print("Warning: dynamic table creation incomplete")

        created_row = {
            "id": local_id,
            "college_id": college_id,
            "classroom_name": classroom_name,
            "classroom_table": classroom_table,
            "classroom_faces": classroom_faces,
            "camera_input": str(camera_input),
            "slot": slot_value,
            "attendance_table": attendance_table
        }

        payload = {
            "id": local_id,
            "college_id": college_id,
            "classroom_name": classroom_name,
            "classroom_table": classroom_table,
            "classroom_faces": classroom_faces,
            "camera_input": str(camera_input),
            "slot": slot_value,
            "attendance_table": attendance_table
        }

        if is_supabase_available():
            try:
                supabase.table("classrooms").upsert(payload).execute()
            except Exception as cloud_error:
                print("Cloud classroom insert failed, queued:", cloud_error)
                enqueue_sync("classrooms", "insert", "classrooms", payload)
        else:
            enqueue_sync("classrooms", "insert", "classrooms", payload)

        return created_row

    except Exception as e:
        print("Error adding classroom:", e)
        if conn:
            conn.rollback()
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_classroom_full_data_by_name_by_id(classroom_id):
    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, classroom_table, attendance_table
            FROM public.classrooms
            WHERE id = %s
            LIMIT 1
        """, (classroom_id,))

        row = cur.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "classroom_table": row[1],
            "attendance_table": row[2]
        }

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_classroom_data_by_name(class_name):
    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, college_id, classroom_name, classroom_table, classroom_faces,
                   attendance_table, slot, camera_input
            FROM public.classrooms
            WHERE classroom_name = %s
            LIMIT 1
        """, (class_name.strip().lower(),))

        row = cur.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "college_id": row[1],
            "classroom_name": row[2],
            "classroom_table": row[3],
            "classroom_faces": row[4],
            "attendance_table": row[5],
            "slot": row[6],
            "camera_input": row[7]
        }

    except Exception as e:
        print("Error fetching classroom data:", e)
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_classroom_full_data_by_name(class_name):
    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, college_id, classroom_name, classroom_table, classroom_faces,
                   attendance_table, camera_input, slot
            FROM public.classrooms
            WHERE classroom_name = %s
            LIMIT 1
        """, (class_name.strip().lower(),))

        row = cur.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "college_id": row[1],
            "classroom_name": row[2],
            "classroom_table": row[3],
            "classroom_faces": row[4],
            "attendance_table": row[5],
            "camera_input": row[6],
            "slot": row[7]
        }

    except Exception as e:
        print("Error fetching classroom:", e)
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_classrooms_by_college_id(college_id):
    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, college_id, classroom_name, classroom_table, classroom_faces,
                   attendance_table, camera_input, slot
            FROM public.classrooms
            WHERE college_id = %s
            ORDER BY id ASC
        """, (college_id,))

        rows = cur.fetchall()

        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "college_id": row[1],
                "classroom_name": row[2],
                "classroom_table": row[3],
                "classroom_faces": row[4],
                "attendance_table": row[5],
                "camera_input": row[6],
                "slot": row[7]
            })

        return result

    except Exception as e:
        print("Error fetching classrooms:", e)
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def delete_classroom(classroom_id):
    conn = None
    cur = None

    try:
        if not is_supabase_available():
            print("Supabase not available — abort delete")
            return False, "No internet / Cloud Storage unavailable"

        data = get_classroom_full_data_by_name_by_id(classroom_id)
        if not data:
            return False, "Classroom not found"

        classroom_table = data["classroom_table"]
        attendance_table = data["attendance_table"]

        try:
            cloud_conn = get_cloud_pg_connection()
            cloud_cur = cloud_conn.cursor()

            cloud_cur.execute(sql.SQL(
                "DROP TABLE IF EXISTS public.{} CASCADE"
            ).format(sql.Identifier(classroom_table)))

            cloud_cur.execute(sql.SQL(
                "DROP TABLE IF EXISTS public.{} CASCADE"
            ).format(sql.Identifier(attendance_table)))

            cloud_cur.execute("""
                DELETE FROM public.classrooms
                WHERE id = %s
            """, (classroom_id,))

            cloud_conn.commit()

        except Exception as e:
            print("Cloud delete failed:", e)
            return False, "Cloud delete failed"

        finally:
            if cloud_cur:
                cloud_cur.close()
            if cloud_conn:
                cloud_conn.close()

        
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute(sql.SQL("DROP TABLE IF EXISTS public.{} CASCADE").format(
            sql.Identifier(classroom_table)
        ))

        cur.execute(sql.SQL("DROP TABLE IF EXISTS public.{} CASCADE").format(
            sql.Identifier(attendance_table)
        ))

        cur.execute("""
            DELETE FROM public.classrooms
            WHERE id = %s
        """, (classroom_id,))

        conn.commit()

        return True, "Deleted successfully"

    except Exception as e:
        print("Delete error:", e)
        if conn:
            conn.rollback()
        return False, str(e)

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def update_classroom(classroom_id, classroom_name, camera_input, slots):
    conn = None
    cur = None

    try:
        classroom_name = classroom_name.strip().lower()
        slot_value = normalize_slot_value(slots)

        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, college_id, classroom_table, classroom_faces, attendance_table
            FROM public.classrooms
            WHERE id = %s
            LIMIT 1
        """, (classroom_id,))

        old_row = cur.fetchone()
        if not old_row:
            return None

        old_id, college_id, classroom_table, classroom_faces, attendance_table = old_row

        cur.execute("""
            UPDATE public.classrooms
            SET classroom_name = %s,
                camera_input = %s,
                slot = %s
            WHERE id = %s
        """, (
            classroom_name,
            str(camera_input),
            Json(slot_value),
            classroom_id
        ))

        conn.commit()

        create_dynamic_student_table(classroom_table)
        create_dynamic_attendance_table(attendance_table, slot_value)

        result = {
            "id": classroom_id,
            "college_id": college_id,
            "classroom_name": classroom_name,
            "classroom_table": classroom_table,
            "classroom_faces": classroom_faces,
            "attendance_table": attendance_table,
            "camera_input": str(camera_input),
            "slot": slot_value
        }

        if is_supabase_available():
            try:
                supabase.table("classrooms").upsert(result).execute()
            except Exception as cloud_error:
                print("Cloud classroom update failed, queued:", cloud_error)
                enqueue_sync("classrooms", "update", "classrooms", result)
        else:
            enqueue_sync("classrooms", "update", "classrooms", result)

        return result

    except Exception as e:
        print("Error updating classroom:", e)
        if conn:
            conn.rollback()
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# STUDENT IMAGE / STUDENT INSERT

def upload_student_image(folder_name, student_prn, file_path):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if not ext:
            ext = ".jpg"

        safe_student_prn = student_prn.strip().lower().replace(" ", "_")
        file_name = f"{safe_student_prn}{ext}"

        local_folder = os.path.join(LOCAL_IMAGE_ROOT, folder_name)
        os.makedirs(local_folder, exist_ok=True)

        local_path = os.path.join(local_folder, file_name)
        shutil.copyfile(file_path, local_path)

        if is_supabase_available():
            try:
                content_type = "image/png" if ext == ".png" else "image/jpeg"
                storage_path = f"{folder_name}/{file_name}"

                with open(local_path, "rb") as f:
                    file_bytes = f.read()

                try:
                    supabase.storage.from_(SUPABASE_BUCKET).upload(
                        path=storage_path,
                        file=file_bytes,
                        file_options={"content-type": content_type}
                    )
                except Exception:
                    
                    pass

                public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)

                if public_url:
                    return public_url, file_name

            except Exception as e:
                print("Cloud upload failed, keeping local file:", e)

        enqueue_sync("storage_upload", "upload_file", folder_name, {
            "folder_name": folder_name,
            "student_prn": student_prn,
            "local_path": local_path,
            "file_name": file_name
        })
        return local_path, file_name

    except Exception as e:
        print("Error uploading image:", e)
        return None, None


def insert_student_into_dynamic_table(
    table_name,
    college_id,
    classroom_id,
    student_name,
    img_url,
    student_prn,
    password,
    email
):
    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute(
            sql.SQL("SELECT id FROM public.{} WHERE prn = %s LIMIT 1").format(
                sql.Identifier(table_name)
            ),
            (student_prn,)
        )

        if cur.fetchone():
            print("Student with same PRN already exists")
            return None

        cur.execute(
            sql.SQL("""
                INSERT INTO public.{}
                (college_id, classroom_id, student_name, img_url, prn, password, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, college_id, classroom_id, student_name, img_url, prn, password, email
            """).format(sql.Identifier(table_name)),
            (college_id, classroom_id, student_name, img_url, student_prn, password, email)
        )

        row = cur.fetchone()
        conn.commit()

        result = {
            "id": row[0],
            "college_id": row[1],
            "classroom_id": row[2],
            "student_name": row[3],
            "img_url": row[4],
            "prn": row[5],
            "password": row[6],
            "email": row[7]
        }

        payload = make_payload_json_safe(result.copy())

        if is_supabase_available():
            try:
                supabase.table(table_name).insert(payload).execute()
            except Exception as cloud_error:
                print("Cloud student insert failed, queued:", cloud_error)
                enqueue_sync("dynamic_table", "insert", table_name, payload)
        else:
            enqueue_sync("dynamic_table", "insert", table_name, payload)

        return result

    except Exception as e:
        print("Error inserting student:", e)
        if conn:
            conn.rollback()
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def add_student_to_classroom(class_name, student_name, file_path, student_prn, password, email):
    try:
        classroom_data = get_classroom_data_by_name(class_name)

        if not classroom_data:
            print("Classroom not found")
            return None

        classroom_id = classroom_data["id"]
        college_id = classroom_data["college_id"]
        classroom_table = classroom_data["classroom_table"]
        classroom_faces = classroom_data["classroom_faces"]

        created_students = create_dynamic_student_table(classroom_table)
        if not created_students:
            return None

        img_url, _ = upload_student_image(
            classroom_faces,
            student_prn,
            file_path
        )

        if not img_url:
            return None

        inserted = insert_student_into_dynamic_table(
            classroom_table,
            college_id,
            classroom_id,
            student_name,
            img_url,
            student_prn,
            password,
            email
        )

        return inserted

    except Exception as e:
        print("Error in add_student_to_classroom:", e)
        return None


# ATTENDANCE

def mark_attendance_for_slot(class_name, recognized_people):
    conn = None
    cur = None

    try:
        classroom_data = get_classroom_full_data_by_name(class_name)
        if not classroom_data:
            print("Classroom not found")
            return False

        classroom_table = classroom_data["classroom_table"]
        attendance_table = classroom_data["attendance_table"]
        classroom_id = classroom_data["id"]
        college_id = classroom_data["college_id"]
        slots = classroom_data.get("slot", [])

        created = create_dynamic_attendance_table(attendance_table, slots)
        if not created:
            return False

        _, slot_column = get_current_active_slot(slots)
        if not slot_column:
            print("No active slot right now")
            return False

        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute(
            sql.SQL("SELECT student_name, prn FROM public.{}").format(
                sql.Identifier(classroom_table)
            )
        )

        students = cur.fetchall()
        if not students:
            print("No students found")
            return False

        today = date.today()
        recognized_set = {str(x).strip().lower() for x in recognized_people if x}

        for student_name, prn_raw in students:
            prn = str(prn_raw).strip().lower()
            status = "present" if prn in recognized_set else "absent"

            cur.execute(
                sql.SQL("""
                    INSERT INTO public.{}
                    (college_id, classroom_id, student_name, prn, attendance_date, {})
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (prn, attendance_date)
                    DO UPDATE SET {} = EXCLUDED.{}
                """).format(
                    sql.Identifier(attendance_table),
                    sql.Identifier(slot_column),
                    sql.Identifier(slot_column),
                    sql.Identifier(slot_column)
                ),
                (college_id, classroom_id, student_name, prn, today, status)
            )

        conn.commit()

        if is_supabase_available():
            try:
                ok = sync_attendance_date_to_cloud(attendance_table, str(today))
                if not ok:
                    enqueue_sync("attendance_sync", "sync_date", attendance_table, {
                        "attendance_date": str(today)
                    })
            except Exception as cloud_error:
                print("Cloud attendance sync failed, queued:", cloud_error)
                enqueue_sync("attendance_sync", "sync_date", attendance_table, {
                    "attendance_date": str(today)
                })
        else:
            enqueue_sync("attendance_sync", "sync_date", attendance_table, {
                "attendance_date": str(today)
            })

        return True

    except Exception as e:
        print("Error marking attendance:", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_attendance_by_date(class_name, attendance_date=None):
    conn = None
    cur = None

    try:
        classroom_data = get_classroom_full_data_by_name(class_name)
        if not classroom_data:
            return []

        attendance_table = classroom_data["attendance_table"]

        if attendance_date is None:
            attendance_date = str(date.today())

        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute(
            sql.SQL("SELECT * FROM public.{} WHERE attendance_date = %s ORDER BY id ASC").format(
                sql.Identifier(attendance_table)
            ),
            (attendance_date,)
        )

        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))

        return result

    except Exception as e:
        print("Error fetching attendance:", e)
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# STARTUP

def startup_sync():
    try:
        init_local_database()
        pull_cloud_base_to_local()
        process_sync_queue()
    except Exception as e:
        print("Startup sync error:", e)