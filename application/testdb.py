# import os
# import json
# from datetime import date

# from database import (
#     startup_sync,
#     init_local_database,
#     is_internet_available,
#     is_supabase_available,
#     process_sync_queue,
#     get_pending_sync_jobs,
#     add_classroom,
#     get_classroom_data_by_name,
#     get_classroom_full_data_by_name,
#     get_classrooms_by_college_id,
#     update_classroom,
#     add_student_to_classroom,
#     mark_attendance_for_slot,
#     get_attendance_by_date,
# )


# # ============================================================
# # CONFIG - CHANGE THESE BEFORE RUNNING
# # ============================================================

# TEST_COLLEGE_ID = 1
# TEST_CLASSROOM_NAME = "class_d"
# UPDATED_CAMERA_INPUT = "1"

# # Put a real image path here
# TEST_STUDENT_IMAGE = r"pilli.jpg"

# TEST_STUDENT_NAME = "Test Student D"
# TEST_STUDENT_PRN = "PRN_CLASS_D_001"
# TEST_STUDENT_PASSWORD = "1234"
# TEST_STUDENT_EMAIL = "studentd@test.com"

# INITIAL_SLOTS = [
#     {"start": "00:00", "end": "23:59"}
# ]

# UPDATED_SLOTS = [
#     {"start": "00:00", "end": "23:59"}
# ]


# # ============================================================
# # HELPERS
# # ============================================================

# def line():
#     print("=" * 70)


# def section(title):
#     line()
#     print(title)
#     line()


# def ok(label, value=None):
#     if value is None:
#         print(f"[OK] {label}")
#     else:
#         print(f"[OK] {label}: {value}")


# def fail(label, value=None):
#     if value is None:
#         print(f"[FAIL] {label}")
#     else:
#         print(f"[FAIL] {label}: {value}")


# def show_json(label, data):
#     print(f"{label}:")
#     try:
#         print(json.dumps(data, indent=2, default=str))
#     except Exception:
#         print(data)


# def safe_run(label, func):
#     try:
#         result = func()
#         ok(label)
#         return result
#     except Exception as e:
#         fail(label, str(e))
#         return None


# # ============================================================
# # TEST STEPS
# # ============================================================

# def test_environment():
#     section("1. ENV / CONNECTIVITY CHECK")

#     internet = is_internet_available()
#     supabase_live = is_supabase_available()

#     print(f"Internet Available : {internet}")
#     print(f"Supabase Available : {supabase_live}")

#     return internet, supabase_live


# def test_startup():
#     section("2. STARTUP SYNC")

#     init_ok = init_local_database()
#     print(f"init_local_database() -> {init_ok}")

#     try:
#         startup_sync()
#         ok("startup_sync() completed")
#     except Exception as e:
#         fail("startup_sync()", str(e))


# def test_add_classroom():
#     section("3. ADD CLASSROOM")

#     result = add_classroom(
#         college_id=TEST_COLLEGE_ID,
#         classroom_name=TEST_CLASSROOM_NAME,
#         camera_input="0",
#         slots=INITIAL_SLOTS
#     )

#     if result is None:
#         fail("add_classroom returned None")
#         return None

#     if isinstance(result, dict) and result.get("error"):
#         print(f"[INFO] add_classroom says: {result['error']}")
#         return get_classroom_data_by_name(TEST_CLASSROOM_NAME)

#     ok("add_classroom returned data")
#     show_json("Created Classroom", result)
#     return result


# def test_get_classroom():
#     section("4. GET CLASSROOM BY NAME")

#     data = get_classroom_data_by_name(TEST_CLASSROOM_NAME)
#     if not data:
#         fail("get_classroom_data_by_name failed")
#         return None

#     ok("get_classroom_data_by_name")
#     show_json("Classroom Data", data)

#     full_data = get_classroom_full_data_by_name(TEST_CLASSROOM_NAME)
#     if not full_data:
#         fail("get_classroom_full_data_by_name failed")
#         return data

#     ok("get_classroom_full_data_by_name")
#     show_json("Full Classroom Data", full_data)
#     return full_data


# def test_list_classrooms():
#     section("5. GET CLASSROOMS BY COLLEGE ID")

#     rows = get_classrooms_by_college_id(TEST_COLLEGE_ID)

#     if rows is None:
#         fail("get_classrooms_by_college_id returned None")
#         return []

#     ok("get_classrooms_by_college_id", f"{len(rows)} classrooms found")
#     show_json("Classrooms", rows)
#     return rows


# def test_update_classroom(classroom_data):
#     section("6. UPDATE CLASSROOM")

#     if not classroom_data:
#         fail("No classroom data available for update")
#         return None

#     classroom_id = classroom_data["id"]

#     result = update_classroom(
#         classroom_id=classroom_id,
#         classroom_name=TEST_CLASSROOM_NAME,
#         camera_input=UPDATED_CAMERA_INPUT,
#         slots=UPDATED_SLOTS
#     )

#     if not result:
#         fail("update_classroom failed")
#         return None

#     ok("update_classroom")
#     show_json("Updated Classroom", result)
#     return result


# def test_add_student():
#     section("7. ADD STUDENT")

#     if not os.path.exists(TEST_STUDENT_IMAGE):
#         fail("Student image file not found", TEST_STUDENT_IMAGE)
#         print("Put a valid image file path in TEST_STUDENT_IMAGE before testing this step.")
#         return None

#     result = add_student_to_classroom(
#         class_name=TEST_CLASSROOM_NAME,
#         student_name=TEST_STUDENT_NAME,
#         file_path=TEST_STUDENT_IMAGE,
#         student_prn=TEST_STUDENT_PRN,
#         password=TEST_STUDENT_PASSWORD,
#         email=TEST_STUDENT_EMAIL
#     )

#     if not result:
#         fail("add_student_to_classroom failed")
#         return None

#     ok("add_student_to_classroom")
#     show_json("Added Student", result)
#     return result


# def test_mark_attendance():
#     section("8. MARK ATTENDANCE")

#     recognized_people = [TEST_STUDENT_PRN]

#     result = mark_attendance_for_slot(
#         class_name=TEST_CLASSROOM_NAME,
#         recognized_people=recognized_people
#     )

#     print(f"mark_attendance_for_slot() -> {result}")
#     if result:
#         ok("Attendance marked")
#     else:
#         fail("Attendance marking failed")

#     return result


# def test_get_attendance():
#     section("9. GET ATTENDANCE")

#     today = str(date.today())
#     rows = get_attendance_by_date(TEST_CLASSROOM_NAME, today)

#     if rows is None:
#         fail("get_attendance_by_date returned None")
#         return []

#     ok("get_attendance_by_date", f"{len(rows)} records found")
#     show_json("Attendance Rows", rows)
#     return rows


# def test_sync_queue():
#     section("10. SYNC QUEUE STATUS")

#     pending_before = get_pending_sync_jobs(200)
#     ok("Fetched pending sync jobs before processing", len(pending_before))
#     show_json("Pending Jobs Before", pending_before)

#     process_result = process_sync_queue()
#     print(f"process_sync_queue() -> {process_result}")

#     pending_after = get_pending_sync_jobs(200)
#     ok("Fetched pending sync jobs after processing", len(pending_after))
#     show_json("Pending Jobs After", pending_after)

#     return pending_before, pending_after


# # ============================================================
# # MAIN RUNNER
# # ============================================================

# def main():
#     section("DATABASE FLOW TEST START")

#     print("Test classroom name:", TEST_CLASSROOM_NAME)
#     print("Test college id    :", TEST_COLLEGE_ID)
#     print("Today              :", str(date.today()))
#     print("Student image path :", TEST_STUDENT_IMAGE)

#     internet, supabase_live = test_environment()
#     test_startup()

#     created = test_add_classroom()
#     fetched = test_get_classroom()
#     test_list_classrooms()
#     updated = test_update_classroom(fetched or created)
#     student = test_add_student()
#     attendance_marked = test_mark_attendance()
#     attendance_rows = test_get_attendance()
#     pending_before, pending_after = test_sync_queue()

#     section("FINAL SUMMARY")

#     print(f"Internet Available          : {internet}")
#     print(f"Supabase Available          : {supabase_live}")
#     print(f"Classroom Created/Fetched   : {bool(created or fetched)}")
#     print(f"Classroom Updated           : {bool(updated)}")
#     print(f"Student Added               : {bool(student)}")
#     print(f"Attendance Marked           : {bool(attendance_marked)}")
#     print(f"Attendance Rows Found       : {len(attendance_rows) if attendance_rows is not None else 0}")
#     print(f"Pending Jobs Before Sync    : {len(pending_before) if pending_before is not None else 0}")
#     print(f"Pending Jobs After Sync     : {len(pending_after) if pending_after is not None else 0}")

#     line()
#     print("DONE")
#     line()


# if __name__ == "__main__":
#     main()



# # bcrypt

# import bcrypt

# password = "123"

# hashed = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
# print(hashed)
# print(hashed.decode('utf-8'))

# correct_pass = "demo"
# incorrect_pass = "demo1"

# if bcrypt.checkpw(correct_pass.encode('utf-8'),hashed):
#     print("correct")

# if bcrypt.checkpw(incorrect_pass.encode('utf-8'),hashed):
#     print("correct")
# else:
#     print("incorrect")


import json
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

attendance_json = '''
                [
  {"attendance_date":"2026-03-02","slot_12_00_01_00_teacher":"alice","slot_01_00_02_00_teacher":"bob","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"present","s2":"absent"},
    {"student_name":"test","prn":"123456","s1":"absent","s2":"present"}
  ]},
  {"attendance_date":"2026-03-03","slot_12_00_01_00_teacher":"bob","slot_01_00_02_00_teacher":"omkart","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"absent","s2":"present"},
    {"student_name":"test","prn":"123456","s1":"present","s2":"absent"}
  ]},
  {"attendance_date":"2026-03-04","slot_12_00_01_00_teacher":"omkart","slot_01_00_02_00_teacher":"alice","records":[
    {"student_name":"demo","prn":"1234","s1":"absent","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"present","s2":"present"},
    {"student_name":"test","prn":"123456","s1":"present","s2":"absent"}
  ]},
  {"attendance_date":"2026-03-05","slot_12_00_01_00_teacher":"alice","slot_01_00_02_00_teacher":"bob","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"absent"},
    {"student_name":"omkar","prn":"1567657","s1":"present","s2":"present"},
    {"student_name":"test","prn":"123456","s1":"absent","s2":"present"}
  ]},
  {"attendance_date":"2026-03-06","slot_12_00_01_00_teacher":"bob","slot_01_00_02_00_teacher":"alice","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"absent","s2":"absent"},
    {"student_name":"test","prn":"123456","s1":"present","s2":"present"}
  ]},

  {"attendance_date":"2026-03-09","slot_12_00_01_00_teacher":"omkart","slot_01_00_02_00_teacher":"bob","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"present","s2":"absent"},
    {"student_name":"test","prn":"123456","s1":"absent","s2":"present"}
  ]},
  {"attendance_date":"2026-03-10","slot_12_00_01_00_teacher":"alice","slot_01_00_02_00_teacher":"omkart","records":[
    {"student_name":"demo","prn":"1234","s1":"absent","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"present","s2":"present"},
    {"student_name":"test","prn":"123456","s1":"present","s2":"absent"}
  ]},
  {"attendance_date":"2026-03-11","slot_12_00_01_00_teacher":"bob","slot_01_00_02_00_teacher":"alice","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"absent"},
    {"student_name":"omkar","prn":"1567657","s1":"present","s2":"present"},
    {"student_name":"test","prn":"123456","s1":"absent","s2":"present"}
  ]},
  {"attendance_date":"2026-03-12","slot_12_00_01_00_teacher":"omkart","slot_01_00_02_00_teacher":"bob","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"absent","s2":"present"},
    {"student_name":"test","prn":"123456","s1":"present","s2":"absent"}
  ]},
  {"attendance_date":"2026-03-13","slot_12_00_01_00_teacher":"alice","slot_01_00_02_00_teacher":"bob","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"present","s2":"present"},
    {"student_name":"test","prn":"123456","s1":"absent","s2":"present"}
  ]},

  
  {"attendance_date":"2026-03-18","slot_12_00_01_00_teacher":"alice","slot_01_00_02_00_teacher":"bob","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"absent"},
    {"student_name":"omkar","prn":"1567657","s1":"absent","s2":"present"},
    {"student_name":"test","prn":"123456","s1":"present","s2":"present"}
  ]},
  {"attendance_date":"2026-03-19","slot_12_00_01_00_teacher":"bob","slot_01_00_02_00_teacher":"alice","records":[
    {"student_name":"demo","prn":"1234","s1":"present","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"present","s2":"absent"},
    {"student_name":"test","prn":"123456","s1":"present","s2":"present"}
  ]},
  {"attendance_date":"2026-03-20","slot_12_00_01_00_teacher":"omkart","slot_01_00_02_00_teacher":"bob","records":[
    {"student_name":"demo","prn":"1234","s1":"absent","s2":"present"},
    {"student_name":"omkar","prn":"1567657","s1":"present","s2":"present"},
    {"student_name":"test","prn":"123456","s1":"present","s2":"absent"}
  ]}
]
                '''
attendance_list = json.loads(attendance_json)

final_data = []

for day in attendance_list:
    for student in day["records"]:
        final_data.append({
            "college_id": 1,
            "classroom_id": 6,
            "student_name": student["student_name"],
            "prn": student["prn"],
            "attendance_date": day["attendance_date"],

            "slot_12_00_01_00": student["s1"],
            "slot_01_00_02_00": student["s2"],

            "slot_12_00_01_00_teacher": day["slot_12_00_01_00_teacher"],
            "slot_01_00_02_00_teacher": day["slot_01_00_02_00_teacher"],

            "audit": None
        })


response = supabase.table("class_a_attendance").insert(final_data).execute()

if response.data:
    print(f"Inserted {len(final_data)} records successfully")
else:
    print("Error:", response)