import os
import re
import uuid
from dotenv import load_dotenv
from supabase import create_client, Client
from fastapi import APIRouter, HTTPException, UploadFile
import bcrypt

load_dotenv()

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY missing in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def is_valid_table_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name))

def encrypt_password(password):
    return bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

def check_password(entered_password, hashed_password):
    return bcrypt.checkpw(entered_password.encode('utf-8') , hashed_password.encode('utf-8'))

def student_login(name: str, email: str, password: str, college_id, classroom_id):
    try:
        if not str(college_id).strip().isdigit() or not str(classroom_id).strip().isdigit():
            return None

        college_id = int(college_id)
        classroom_id = int(classroom_id)

        classroom = get_classroom_by_id(classroom_id)
        if not classroom:
            return None

        if classroom["college_id"] != college_id:
            return None

        classroom_table = classroom["classroom_table"]
        if not is_valid_table_name(classroom_table):
            raise HTTPException(status_code=400, detail="Invalid classroom table name")

        response = (
            supabase
            .table(classroom_table)
            .select("id, student_name, email, prn, classroom_id, college_id , password")
            .eq("college_id", college_id)
            .eq("classroom_id", classroom_id)
            .eq("student_name", name)
            .eq("email", email)
            # .eq("password", password)
            .limit(1)
            .execute()
        )

        data = response.data or []

        if not data:
            return None

        user = data[0]

        if check_password(password, user["password"]):
            print(user)
            return user

        return None

    except Exception as e:
        print("Error in student login:", e)
        return None


def teacher_login(college_id, teacher_name: str, email: str, password: str):
    try:
        if not str(college_id).strip().isdigit():
            return None

        response = (
            supabase
            .table("teachers")
            .select("id, college_id, teacher_name, email, role , password")
            .eq("college_id", int(college_id))
            .eq("teacher_name", teacher_name)
            .eq("email", email)
            # .eq("password", password)
            .eq("role", "teacher")
            .limit(1)
            .execute()
        )

        data = response.data or []

        if not data:
            return None

        user = data[0]

        if check_password(password, user["password"]):
            print(user)
            return user

        return None

    except Exception as e:
        print("Error in teacher login:", e)
        return None


def hod_login(name: str, college_name: str, email: str, password: str):
    try:
        response = (
            supabase
            .table("colleges")
            .select("id, college_name, creator, creator_email , password")
            .eq("creator", name)
            .eq("creator_email", email)
            .eq("college_name", college_name)
            # .eq("password", password)
            .limit(1)
            .execute()
        )

        data = response.data or []

        if not data:
            return None

        user = data[0]

        if check_password(password, user["password"]):
            print(user)
            return user

        return None

    except Exception as e:
        print("Error in HOD login:", e)
        return None


def hod_signup(name: str, college_name: str, email: str, password: str):
    try:
        existing_college = (
            supabase
            .table("colleges")
            .select("id")
            .eq("college_name", college_name)
            .limit(1)
            .execute()
        )

        if existing_college.data:
            return None

        existing_user = (
            supabase
            .table("teachers")
            .select("id")
            .eq("email", email)
            .limit(1)
            .execute()
        )

        if existing_user.data:
            return None
        password = encrypt_password(password).decode('utf-8')
        college_insert = (
            supabase
            .table("colleges")
            .insert({
                "college_name": college_name,
                "creator": name,
                "creator_email": email,
                "password": password
            })
            .execute()
        )

        college_data = college_insert.data or []
        if not college_data:
            return None

        college_id = college_data[0]["id"]

        teacher_insert = (
            supabase
            .table("teachers")
            .insert({
                "college_id": college_id,
                "teacher_name": name,
                "email": email,
                "role": "hod",
                "password": password
            })
            .execute()
        )

        teacher_data = teacher_insert.data or []
        if not teacher_data:
            return None

        return {
            "college": college_data[0],
            "teacher": teacher_data[0]
        }

    except Exception as e:
        print("Error in HOD signup:", e)
        return None


def get_college_by_id(college_id: int):
    try:
        response = (
            supabase
            .table("colleges")
            .select("id, college_name, creator, creator_email")
            .eq("id", college_id)
            .limit(1)
            .execute()
        )

        data = response.data or []
        return data[0] if data else None

    except Exception as e:
        print("Error fetching college by id:", e)
        return None


def get_teachers_by_college(college_id: int):
    try:
        response = (
            supabase
            .table("teachers")
            .select("id, college_id, teacher_name, email, role")
            .eq("college_id", college_id)
            .order("teacher_name")
            .execute()
        )

        return response.data or []

    except Exception as e:
        print("Error fetching teachers:", e)
        return []


def get_classrooms_by_college(college_id: int):
    try:
        response = (
            supabase
            .table("classrooms")
            .select(
                "id, college_id, classroom_name, classroom_table, "
                "classroom_faces, camera_input, slot, attendance_table"
            )
            .eq("college_id", college_id)
            .order("classroom_name")
            .execute()
        )

        return response.data or []

    except Exception as e:
        print("Error fetching classrooms:", e)
        return []


def get_classroom_by_id(classroom_id: int):
    try:
        response = (
            supabase
            .table("classrooms")
            .select(
                "id, college_id, classroom_name, classroom_table, "
                "classroom_faces, camera_input, slot, attendance_table"
            )
            .eq("id", classroom_id)
            .limit(1)
            .execute()
        )

        data = response.data or []
        return data[0] if data else None

    except Exception as e:
        print("Error fetching classroom by id:", e)
        return None


def format_slot_label(column_name: str) -> str:
    if not column_name.startswith("slot_"):
        return column_name

    raw = column_name.replace("slot_", "", 1)
    parts = raw.split("_")

    if len(parts) >= 4:
        start_time = f"{parts[0]}:{parts[1]}"
        end_time = f"{parts[2]}:{parts[3]}"
        return f"{start_time} - {end_time}"

    return column_name


def get_student_dashboard_data(student_name: str, student_email: str, college_id: int, classroom_id: int):
    try:
        classroom = get_classroom_by_id(classroom_id)
        if not classroom:
            return None

        if classroom["college_id"] != college_id:
            return None

        classroom_table = classroom.get("classroom_table")
        attendance_table = classroom.get("attendance_table")

        if not classroom_table or not attendance_table:
            return None

        if not is_valid_table_name(classroom_table):
            raise HTTPException(status_code=400, detail="Invalid classroom table name")

        if not is_valid_table_name(attendance_table):
            raise HTTPException(status_code=400, detail="Invalid attendance table name")

        student_response = (
            supabase
            .table(classroom_table)
            .select("id, student_name, email, prn, college_id, classroom_id, img_url")
            .eq("college_id", college_id)
            .eq("classroom_id", classroom_id)
            .eq("student_name", student_name)
            .eq("email", student_email)
            .limit(1)
            .execute()
        )

        student_rows = student_response.data or []
        if not student_rows:
            return None

        student_row = student_rows[0]

        attendance_response = (
            supabase
            .table(attendance_table)
            .select("*")
            .eq("college_id", college_id)
            .eq("classroom_id", classroom_id)
            .eq("prn", student_row["prn"])
            .order("attendance_date", desc=True)
            .execute()
        )

        attendance_rows = attendance_response.data or []

        attendance = {}
        present_count = 0
        absent_count = 0
        pending_count = 0

        for row in attendance_rows:
            row_date = row.get("attendance_date")
            row_date = str(row_date) if row_date else "Not marked yet"

            day_slots = []

            for key, value in row.items():
                if key.startswith("slot_"):
                    normalized = str(value).strip().lower() if value is not None else ""

                    if normalized == "present":
                        status = "present"
                        present_count += 1
                    elif normalized == "absent":
                        status = "absent"
                        absent_count += 1
                    else:
                        status = "pending"
                        pending_count += 1

                    day_slots.append({
                        "slot_label": format_slot_label(key),
                        "status": status
                    })

            day_slots.sort(key=lambda x: x["slot_label"])
            attendance[row_date] = day_slots

        marked_total = present_count + absent_count
        attendance_percent = round((present_count / marked_total) * 100, 2) if marked_total > 0 else 0

        return {
            "student_name": student_row.get("student_name", ""),
            "student_email": student_row.get("email", ""),
            "student_prn": student_row.get("prn", ""),
            "student_image": student_row.get("img_url", ""),
            "college_id": student_row.get("college_id", ""),
            "classroom_id": student_row.get("classroom_id", ""),
            "classroom_name": classroom.get("classroom_name", ""),
            "present_count": present_count,
            "absent_count": absent_count,
            "pending_count": pending_count,
            "attendance_percent": attendance_percent,
            "attendance": attendance,
        }

    except Exception as e:
        print("Error building student dashboard:", e)
        return None


def get_student_dashboard_data_by_prn(college_id: int, classroom_id: int, prn: str):
    try:
        classroom = get_classroom_by_id(classroom_id)
        if not classroom:
            return None

        if classroom["college_id"] != college_id:
            return None

        classroom_table = classroom.get("classroom_table")
        attendance_table = classroom.get("attendance_table")

        if not classroom_table or not attendance_table:
            return None

        if not is_valid_table_name(classroom_table):
            raise HTTPException(status_code=400, detail="Invalid classroom table name")

        if not is_valid_table_name(attendance_table):
            raise HTTPException(status_code=400, detail="Invalid attendance table name")

        student_response = (
            supabase
            .table(classroom_table)
            .select("id, student_name, email, prn, college_id, classroom_id, img_url")
            .eq("college_id", college_id)
            .eq("classroom_id", classroom_id)
            .eq("prn", prn)
            .limit(1)
            .execute()
        )

        student_rows = student_response.data or []
        if not student_rows:
            return None

        student_row = student_rows[0]

        attendance_response = (
            supabase
            .table(attendance_table)
            .select("*")
            .eq("college_id", college_id)
            .eq("classroom_id", classroom_id)
            .eq("prn", prn)
            .order("attendance_date", desc=True)
            .execute()
        )

        attendance_rows = attendance_response.data or []

        attendance = {}
        present_count = 0
        absent_count = 0
        pending_count = 0

        for row in attendance_rows:
            row_date = str(row.get("attendance_date")) if row.get("attendance_date") else "Not marked yet"
            day_slots = []

            for key, value in row.items():
                if key.startswith("slot_"):
                    normalized = str(value).strip().lower() if value is not None else ""

                    if normalized == "present":
                        status = "present"
                        present_count += 1
                    elif normalized == "absent":
                        status = "absent"
                        absent_count += 1
                    else:
                        status = "pending"
                        pending_count += 1

                    day_slots.append({
                        "slot_label": format_slot_label(key),
                        "status": status
                    })

            day_slots.sort(key=lambda x: x["slot_label"])
            attendance[row_date] = day_slots

        marked_total = present_count + absent_count
        attendance_percent = round((present_count / marked_total) * 100, 2) if marked_total > 0 else 0

        return {
            "student_name": student_row.get("student_name", ""),
            "student_email": student_row.get("email", ""),
            "student_prn": student_row.get("prn", ""),
            "student_image": student_row.get("img_url", ""),
            "college_id": student_row.get("college_id", ""),
            "classroom_id": student_row.get("classroom_id", ""),
            "classroom_name": classroom.get("classroom_name", ""),
            "present_count": present_count,
            "absent_count": absent_count,
            "pending_count": pending_count,
            "attendance_percent": attendance_percent,
            "attendance": attendance,
        }

    except Exception as e:
        print("Error building student dashboard by PRN:", e)
        return None


def get_students_from_classroom_table(classroom_table: str):
    try:
        if not is_valid_table_name(classroom_table):
            raise HTTPException(status_code=400, detail="Invalid classroom table name")

        response = (
            supabase
            .table(classroom_table)
            .select("id, college_id, classroom_id, student_name, prn, email, img_url")
            .order("student_name")
            .execute()
        )

        return response.data or []

    except Exception as e:
        print("Error fetching students:", e)
        return []


def upload_student_image_bytes(folder_name: str, student_prn: str, file_name: str, file_bytes: bytes):
    try:
        ext = os.path.splitext(file_name)[1].lower()

        if ext not in [".png", ".jpg", ".jpeg"]:
            return None, None

        safe_student_prn = student_prn.strip().lower().replace(" ", "_")
        final_file_name = f"{safe_student_prn}{ext}"
        storage_path = f"{folder_name}/{final_file_name}"

        content_type = "image/png" if ext == ".png" else "image/jpeg"

        supabase.storage.from_("filestore").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )

        public_url = supabase.storage.from_("filestore").get_public_url(storage_path)

        return public_url, final_file_name

    except Exception as e:
        print("Error uploading image:", e)
        return None, None



def insert_student_into_dynamic_table(
    table_name: str,
    college_id: int,
    classroom_id: int,
    student_name: str,
    img_url: str,
    student_prn: str,
    password: str,
    email: str
):
    try:
        if not is_valid_table_name(table_name):
            raise HTTPException(status_code=400, detail="Invalid classroom table name")

        response = (
            supabase
            .table(table_name)
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


async def add_student_to_classroom_web(
    classroom: dict,
    student_name: str,
    student_prn: str,
    email: str,
    password: str,
    upload_file: UploadFile
):
    try:
        classroom_id = classroom["id"]
        college_id = classroom["college_id"]
        classroom_table = classroom["classroom_table"]
        classroom_faces = classroom["classroom_faces"]

        if not is_valid_table_name(classroom_table):
            raise HTTPException(status_code=400, detail="Invalid classroom table name")

        file_bytes = await upload_file.read()
        if not file_bytes:
            return None

        img_url, _ = upload_student_image_bytes(
            folder_name=classroom_faces,
            student_prn=student_prn,
            file_name=upload_file.filename,
            file_bytes=file_bytes
        )

        if not img_url:
            return None
        password = encrypt_password(password).decode('utf-8')
        inserted = insert_student_into_dynamic_table(
            table_name=classroom_table,
            college_id=college_id,
            classroom_id=classroom_id,
            student_name=student_name,
            img_url=img_url,
            student_prn=student_prn,
            password=password,
            email=email
        )

        return inserted

    except Exception as e:
        print("Error in add_student_to_classroom_web:", e)
        return None
    
def add_teacher_by_invite(college_id: int, teacher_name: str, email: str, password: str):
    try:
        if not str(college_id).strip().isdigit():
            return None

        college_id = int(college_id)

        college_check = (
            supabase
            .table("colleges")
            .select("id")
            .eq("id", college_id)
            .limit(1)
            .execute()
        )

        if not college_check.data:
            return None

        existing_teacher = (
            supabase
            .table("teachers")
            .select("id")
            .eq("email", email)
            .limit(1)
            .execute()
        )

        if existing_teacher.data:
            return None
        password = encrypt_password(password).decode('utf-8')
        response = (
            supabase
            .table("teachers")
            .insert({
                "college_id": college_id,
                "teacher_name": teacher_name,
                "email": email,
                "password": password,
                "role": "teacher"
            })
            .execute()
        )

        return response.data[0] if response.data else None

    except Exception as e:
        print("Error adding teacher by invite:", e)
        return None