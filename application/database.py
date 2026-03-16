import os
import json
import psycopg2
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, date

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "6543")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file")

if not DB_HOST or not DB_NAME or not DB_USER or not DB_PASSWORD:
    raise ValueError("Missing DB credentials in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --------------------------------------------------
# CONNECTION
# --------------------------------------------------

def get_pg_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def parse_slot_data(slot_value):
    if not slot_value:
        return []

    if isinstance(slot_value, list):
        return slot_value

    if isinstance(slot_value, str):
        try:
            return json.loads(slot_value)
        except Exception:
            return []

    return []

def load_qss_file(widget, qss_file):
    try:
        with open(qss_file, "r", encoding="utf-8") as file:
            widget.setStyleSheet(file.read())
    except Exception as e:
        print(f"Failed to load stylesheet {qss_file}: {e}")
        
def make_slot_column_name(start_time: str, end_time: str) -> str:
    safe_start = start_time.strip().replace(":", "_")
    safe_end = end_time.strip().replace(":", "_")
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
                column_name = make_slot_column_name(slot["start"], slot["end"])
                return slot, column_name

        except Exception as e:
            print("Invalid slot format:", e)

    return None, None


# --------------------------------------------------
# AUTH / COLLEGE
# --------------------------------------------------

def check_college_login(name, email, college_name, password):
    try:
        response = (
            supabase.table("colleges")
            .select("id, college_name, creator, creator_email")
            .eq("creator", name)
            .eq("creator_email", email)
            .eq("college_name", college_name)
            .eq("password", password)
            .execute()
        )

        data = response.data or []

        if data:
            row = data[0]
            return {
                "id": row["id"],
                "college_name": row["college_name"],
                "creator": row["creator"],
                "creator_email": row["creator_email"]
            }

        return None

    except Exception as e:
        print("Database error:", e)
        return None


def get_college_names():
    try:
        response = supabase.table("colleges").select("college_name").execute()
        data = response.data or []

        names = sorted(
            list({
                row.get("college_name")
                for row in data
                if row.get("college_name")
            })
        )
        return names

    except Exception as e:
        print("Error fetching college names:", e)
        return []


# --------------------------------------------------
# CLASSROOM TABLE CREATION
# --------------------------------------------------

def create_dynamic_student_table(table_name, slots):
    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # This is student master table, not attendance history
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS public.{table_name} (
            id SERIAL PRIMARY KEY,
            college_id INTEGER NOT NULL,
            classroom_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            prn TEXT NOT NULL UNIQUE,
            img_url TEXT,
            password TEXT,
            email TEXT
        );
        """)

        conn.commit()
        return True

    except Exception as e:
        print("Error creating student table:", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def create_dynamic_attendance_table(table_name, slots):
    conn = None
    cur = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS public.{table_name} (
            id SERIAL PRIMARY KEY,
            college_id INTEGER NOT NULL,
            classroom_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            prn TEXT NOT NULL,
            attendance_date DATE NOT NULL
        );
        """)

        parsed_slots = parse_slot_data(slots)

        for slot_item in parsed_slots:
            start_time = str(slot_item.get("start", "")).strip()
            end_time = str(slot_item.get("end", "")).strip()

            if not start_time or not end_time:
                continue

            column_name = make_slot_column_name(start_time, end_time)

            cur.execute(f"""
            ALTER TABLE public.{table_name}
            ADD COLUMN IF NOT EXISTS {column_name} TEXT;
            """)

        cur.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS {table_name}_prn_date_idx
        ON public.{table_name} (prn, attendance_date);
        """)

        conn.commit()
        return True

    except Exception as e:
        print("Error creating attendance table:", e)
        if conn:
            conn.rollback()
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# --------------------------------------------------
# CLASSROOM CRUD
# --------------------------------------------------

def add_classroom(college_id, classroom_name, camera_input, slots):
    try:
        classroom_name = classroom_name.strip().lower()
        safe_name = classroom_name.replace(" ", "_")

        classroom_table = f"{safe_name}_table"
        classroom_faces = f"{safe_name}_faces"
        attendance_table = f"{safe_name}_attendance"

        existing = (
            supabase.table("classrooms")
            .select("id")
            .eq("college_id", college_id)
            .eq("classroom_name", classroom_name)
            .execute()
        )

        if existing.data:
            return {"error": "Classroom already exists"}

        response = (
            supabase.table("classrooms")
            .insert({
                "college_id": college_id,
                "classroom_name": classroom_name,
                "classroom_table": classroom_table,
                "classroom_faces": classroom_faces,
                "attendance_table": attendance_table,
                "camera_input": str(camera_input),
                "slot": slots
            })
            .execute()
        )

        created_row = response.data[0] if response.data else None

        if created_row:
            create_dynamic_student_table(classroom_table, slots)
            create_dynamic_attendance_table(attendance_table, slots)

        return created_row

    except Exception as e:
        print("Error adding classroom:", e)
        return None


def get_classroom_data_by_name(class_name):
    try:
        response = (
            supabase.table("classrooms")
            .select("id, college_id, classroom_name, classroom_table, classroom_faces, attendance_table, slot, camera_input")
            .eq("classroom_name", class_name.strip().lower())
            .limit(1)
            .execute()
        )

        data = response.data or []
        return data[0] if data else None

    except Exception as e:
        print("Error fetching classroom data:", e)
        return None


def get_classroom_full_data_by_name(class_name):
    try:
        response = (
            supabase.table("classrooms")
            .select("id, college_id, classroom_name, classroom_table, classroom_faces, attendance_table, camera_input, slot")
            .eq("classroom_name", class_name.strip().lower())
            .limit(1)
            .execute()
        )

        data = response.data or []
        return data[0] if data else None

    except Exception as e:
        print("Error fetching classroom:", e)
        return None


def get_classrooms_by_college_id(college_id):
    try:
        response = (
            supabase.table("classrooms")
            .select("id, college_id, classroom_name, classroom_table, classroom_faces, attendance_table, camera_input, slot")
            .eq("college_id", college_id)
            .execute()
        )

        return response.data if response.data else []

    except Exception as e:
        print("Error fetching classrooms:", e)
        return []


def update_classroom(classroom_id, classroom_name, camera_input, slots):
    try:
        classroom_name = classroom_name.strip().lower()

        existing = (
            supabase.table("classrooms")
            .select("id, classroom_table, classroom_faces, attendance_table")
            .eq("id", classroom_id)
            .limit(1)
            .execute()
        )

        data = existing.data or []
        if not data:
            return None

        old_row = data[0]
        classroom_table = old_row["classroom_table"]
        attendance_table = old_row["attendance_table"]

        response = (
            supabase.table("classrooms")
            .update({
                "classroom_name": classroom_name,
                "camera_input": str(camera_input),
                "slot": slots
            })
            .eq("id", classroom_id)
            .execute()
        )

        if response.data:
            create_dynamic_student_table(classroom_table, slots)
            create_dynamic_attendance_table(attendance_table, slots)

        return response.data[0] if response.data else None

    except Exception as e:
        print("Error updating classroom:", e)
        return None


# --------------------------------------------------
# STUDENT IMAGE / STUDENT INSERT
# --------------------------------------------------

def upload_student_image(folder_name, student_prn, file_path):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if not ext:
            ext = ".jpg"

        safe_student_prn = student_prn.strip().lower().replace(" ", "_")
        file_name = f"{safe_student_prn}{ext}"
        storage_path = f"{folder_name}/{file_name}"

        content_type = "image/png" if ext == ".png" else "image/jpeg"

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        supabase.storage.from_("filestore").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )

        public_url = supabase.storage.from_("filestore").get_public_url(storage_path)

        return public_url, file_name

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
    try:
        # check duplicate prn first
        existing = (
            supabase.table(table_name)
            .select("id")
            .eq("prn", student_prn)
            .execute()
        )

        if existing.data:
            print("Student with same PRN already exists")
            return None

        response = (
            supabase.table(table_name)
            .insert({
                "college_id": college_id,
                "classroom_id": classroom_id,
                "student_name": student_name,
                "img_url": img_url,
                "prn": student_prn,
                "password": password,
                "email": email
            })
            .execute()
        )

        return response.data[0] if response.data else None

    except Exception as e:
        print("Error inserting student:", e)
        return None


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
        slots = classroom_data.get("slot", [])

        created_students = create_dynamic_student_table(classroom_table, slots)
        if not created_students:
            return None

        img_url, file_name = upload_student_image(
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


# --------------------------------------------------
# ATTENDANCE
# --------------------------------------------------

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

        students_response = (
            supabase.table(classroom_table)
            .select("student_name, prn")
            .execute()
        )

        students = students_response.data if students_response.data else []
        if not students:
            print("No students found")
            return False

        today = date.today()

        # recognized_people should ideally be PRNs
        recognized_set = {str(x).strip().lower() for x in recognized_people if x}

        conn = get_pg_connection()
        cur = conn.cursor()

        for student in students:
            student_name = student["student_name"]
            prn = str(student["prn"]).strip().lower()

            status = "present" if prn in recognized_set else "absent"

            cur.execute(f"""
                INSERT INTO public.{attendance_table}
                (college_id, classroom_id, student_name, prn, attendance_date, {slot_column})
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (prn, attendance_date)
                DO UPDATE SET {slot_column} = EXCLUDED.{slot_column};
            """, (
                college_id,
                classroom_id,
                student_name,
                prn,
                today,
                status
            ))

        conn.commit()
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
    try:
        classroom_data = get_classroom_full_data_by_name(class_name)

        if not classroom_data:
            return []

        attendance_table = classroom_data["attendance_table"]

        if attendance_date is None:
            attendance_date = str(date.today())

        response = (
            supabase.table(attendance_table)
            .select("*")
            .eq("attendance_date", attendance_date)
            .execute()
        )

        return response.data if response.data else []

    except Exception as e:
        print("Error fetching attendance:", e)
        return []