# import os
# import tempfile
# from datetime import datetime, timedelta

# from database import (
#     startup_sync,
#     init_local_database,
#     pull_cloud_base_to_local,
#     process_sync_queue,
#     is_internet_available,
#     is_supabase_available,
#     get_pg_connection,
#     get_college_names,
#     check_college_login,
#     add_classroom,
#     get_classroom_data_by_name,
#     get_classroom_full_data_by_name,
#     get_classrooms_by_college_id,
#     update_classroom,
#     create_dynamic_student_table,
#     create_dynamic_attendance_table,
#     add_student_to_classroom,
#     mark_attendance_for_slot,
#     get_attendance_by_date,
#     parse_slot_data,
#     get_current_active_slot,cloud_table_accessible
# )


# def test_cloud_dynamic_table(classroom_table, attendance_table):
#     try:
#         student_ok = cloud_table_accessible(classroom_table)
#         attendance_ok = cloud_table_accessible(attendance_table)

#         print_result("cloud student table accessible", student_ok, classroom_table)
#         print_result("cloud attendance table accessible", attendance_ok, attendance_table)

#         return student_ok, attendance_ok
#     except Exception as e:
#         print_result("cloud dynamic table access", False, str(e))
#         return False, False
    
# def print_result(test_name, success, extra=""):
#     status = "PASSED" if success else "FAILED"
#     print(f"[{status}] {test_name}")
#     if extra:
#         print(f"       {extra}")


# def make_temp_dummy_image():
#     fd, path = tempfile.mkstemp(suffix=".jpg")
#     with os.fdopen(fd, "wb") as f:
#         # tiny fake jpg-like content; enough for file copy testing
#         f.write(b"\xff\xd8\xff\xe0" + b"TEST_IMAGE_DATA" + b"\xff\xd9")
#     return path


# def make_current_active_slot():
#     now = datetime.now()
#     start = (now - timedelta(minutes=10)).strftime("%H:%M")
#     end = (now + timedelta(minutes=50)).strftime("%H:%M")
#     return [{"start": start, "end": end}]


# def test_connection():
#     try:
#         conn = get_pg_connection()
#         conn.close()
#         print_result("Local PostgreSQL connection", True)
#         return True
#     except Exception as e:
#         print_result("Local PostgreSQL connection", False, str(e))
#         return False


# def test_startup():
#     try:
#         startup_sync()
#         print_result("startup_sync()", True)
#         return True
#     except Exception as e:
#         print_result("startup_sync()", False, str(e))
#         return False


# def test_base_tables_exist():
#     try:
#         conn = get_pg_connection()
#         cur = conn.cursor()

#         cur.execute("""
#             SELECT table_name
#             FROM information_schema.tables
#             WHERE table_schema='public'
#               AND table_name IN ('colleges', 'classrooms', 'sync_queue', 'local_id_counters')
#             ORDER BY table_name
#         """)
#         rows = [r[0] for r in cur.fetchall()]
#         cur.close()
#         conn.close()

#         needed = {"colleges", "classrooms", "sync_queue", "local_id_counters"}
#         success = needed.issubset(set(rows))
#         print_result("Base local tables created", success, f"Found: {rows}")
#         return success
#     except Exception as e:
#         print_result("Base local tables created", False, str(e))
#         return False


# def test_cloud_status():
#     internet = is_internet_available()
#     cloud = is_supabase_available()

#     print_result("Internet availability check", internet, f"internet={internet}")
#     print_result("Supabase availability check", cloud, f"supabase={cloud}")
#     return internet, cloud


# def test_pull_cloud():
#     try:
#         ok = pull_cloud_base_to_local()
#         print_result("pull_cloud_base_to_local()", ok, "This may fail if internet or Supabase is unavailable")
#         return ok
#     except Exception as e:
#         print_result("pull_cloud_base_to_local()", False, str(e))
#         return False


# def test_get_college_names():
#     try:
#         names = get_college_names()
#         success = isinstance(names, list)
#         print_result("get_college_names()", success, f"Result: {names}")
#         return names
#     except Exception as e:
#         print_result("get_college_names()", False, str(e))
#         return []


# def test_check_college_login():
#     try:
#         # update these if your actual local/cloud data is different
#         result = check_college_login("omkar", "omkar@gmail.com", "flux", "omkar")
#         success = result is not None
#         print_result("check_college_login()", success, f"Result: {result}")
#         return result
#     except Exception as e:
#         print_result("check_college_login()", False, str(e))
#         return None


# def test_add_classroom(college_id):
#     try:
#         slots = make_current_active_slot()
#         result = add_classroom(college_id, "test_class_demo", 0, slots)

#         success = result is not None and not (isinstance(result, dict) and result.get("error"))
#         print_result("add_classroom()", success, f"Result: {result}")
#         return result
#     except Exception as e:
#         print_result("add_classroom()", False, str(e))
#         return None


# def test_get_classroom(class_name):
#     try:
#         data = get_classroom_data_by_name(class_name)
#         full_data = get_classroom_full_data_by_name(class_name)

#         success = data is not None and full_data is not None
#         print_result("get_classroom_data_by_name()", data is not None, f"Result: {data}")
#         print_result("get_classroom_full_data_by_name()", full_data is not None, f"Result: {full_data}")
#         return data, full_data
#     except Exception as e:
#         print_result("get classroom functions", False, str(e))
#         return None, None


# def test_get_classrooms_by_college_id(college_id):
#     try:
#         rows = get_classrooms_by_college_id(college_id)
#         success = isinstance(rows, list)
#         print_result("get_classrooms_by_college_id()", success, f"Count: {len(rows)}")
#         return rows
#     except Exception as e:
#         print_result("get_classrooms_by_college_id()", False, str(e))
#         return []


# def test_update_classroom(classroom_id):
#     try:
#         slots = make_current_active_slot()
#         result = update_classroom(classroom_id, "test_class_demo", 1, slots)
#         success = result is not None
#         print_result("update_classroom()", success, f"Result: {result}")
#         return result
#     except Exception as e:
#         print_result("update_classroom()", False, str(e))
#         return None


# def test_dynamic_tables(classroom_table, attendance_table):
#     try:
#         slots = make_current_active_slot()
#         ok1 = create_dynamic_student_table(classroom_table, slots)
#         ok2 = create_dynamic_attendance_table(attendance_table, slots)

#         print_result("create_dynamic_student_table()", ok1, classroom_table)
#         print_result("create_dynamic_attendance_table()", ok2, attendance_table)
#         return ok1 and ok2
#     except Exception as e:
#         print_result("dynamic table creation", False, str(e))
#         return False


# def test_add_student(class_name):
#     dummy_path = None
#     try:
#         dummy_path = make_temp_dummy_image()
#         result = add_student_to_classroom(
#             class_name=class_name,
#             student_name="Test Student",
#             file_path=dummy_path,
#             student_prn="PRN_TEST_001",
#             password="1234",
#             email="teststudent@example.com"
#         )

#         success = result is not None
#         print_result("add_student_to_classroom()", success, f"Result: {result}")
#         return result
#     except Exception as e:
#         print_result("add_student_to_classroom()", False, str(e))
#         return None
#     finally:
#         if dummy_path and os.path.exists(dummy_path):
#             os.remove(dummy_path)


# def test_active_slot_logic():
#     try:
#         slots = make_current_active_slot()
#         slot, col = get_current_active_slot(slots)
#         success = slot is not None and col is not None
#         print_result("get_current_active_slot()", success, f"slot={slot}, column={col}")
#         return success
#     except Exception as e:
#         print_result("get_current_active_slot()", False, str(e))
#         return False


# def test_mark_attendance(class_name):
#     try:
#         result = mark_attendance_for_slot(class_name, ["prn_test_001"])
#         print_result("mark_attendance_for_slot()", result, f"Result: {result}")
#         return result
#     except Exception as e:
#         print_result("mark_attendance_for_slot()", False, str(e))
#         return False


# def test_get_attendance(class_name):
#     try:
#         rows = get_attendance_by_date(class_name)
#         success = isinstance(rows, list)
#         print_result("get_attendance_by_date()", success, f"Rows: {rows}")
#         return rows
#     except Exception as e:
#         print_result("get_attendance_by_date()", False, str(e))
#         return []


# def test_sync_queue_processing():
#     try:
#         result = process_sync_queue()
#         print_result("process_sync_queue()", result, f"Result: {result}")
#         return result
#     except Exception as e:
#         print_result("process_sync_queue()", False, str(e))
#         return False


# def test_sync_queue_rows():
#     try:
#         conn = get_pg_connection()
#         cur = conn.cursor()
#         cur.execute("""
#             SELECT id, entity_type, operation, target_name, status, retry_count
#             FROM public.sync_queue
#             ORDER BY id ASC
#         """)
#         rows = cur.fetchall()
#         cur.close()
#         conn.close()

#         print_result("sync_queue inspection", True, f"Rows: {rows}")
#         return rows
#     except Exception as e:
#         print_result("sync_queue inspection", False, str(e))
#         return []


# def main():
#     print("\n========== DATABASE TEST START ==========\n")

#     if not test_connection():
#         print("\nStop here. Your local PostgreSQL connection is not working.\n")
#         return

#     test_startup()
#     test_base_tables_exist()
#     internet, cloud = test_cloud_status()

#     if internet and cloud:
#         test_pull_cloud()
#     else:
#         print("\n[INFO] Cloud pull skipped because internet or Supabase is not available.\n")

#     names = test_get_college_names()
#     login_data = test_check_college_login()

#     if login_data:
#         college_id = login_data["id"]
#     else:
#         print("\n[INFO] Could not get college_id from login. Falling back to 1.\n")
#         college_id = 1

#     classroom = test_add_classroom(college_id)

#     # if classroom already exists, fetch it
#     if isinstance(classroom, dict) and classroom.get("error") == "Classroom already exists":
#         print("\n[INFO] Classroom already exists, fetching existing one.\n")
#         classroom_data = get_classroom_data_by_name("test_class_demo")
#     else:
#         classroom_data = classroom

#     if not classroom_data:
#         print("\nStop here. Classroom creation/fetch failed.\n")
#         return

#     class_name = classroom_data["classroom_name"]
#     classroom_id = classroom_data["id"]
#     classroom_table = classroom_data["classroom_table"]
#     attendance_table = classroom_data["attendance_table"]

#     test_get_classroom(class_name)
#     test_get_classrooms_by_college_id(college_id)
#     test_update_classroom(classroom_id)
#     test_dynamic_tables(classroom_table, attendance_table)
#     test_cloud_dynamic_table(classroom_table, attendance_table)
#     test_active_slot_logic()
#     test_add_student(class_name)
#     test_mark_attendance(class_name)
#     test_get_attendance(class_name)
#     test_sync_queue_rows()
#     test_sync_queue_processing()
#     test_sync_queue_rows()

#     print("\n========== DATABASE TEST END ==========\n")


# if __name__ == "__main__":
#     main()

# from datetime import datetime, timedelta
# from database import (
#     insert_new_classroom_local_and_cloud,
#     create_dynamic_student_table,
#     create_dynamic_attendance_table,
#     get_pg_connection,
#     get_cloud_pg_connection,
#     table_exists_in_connection
# )


# def print_result(name, ok, extra=""):
#     status = "PASSED" if ok else "FAILED"
#     print(f"[{status}] {name}")
#     if extra:
#         print(f"       {extra}")


# def make_test_slots():
#     now = datetime.now()
#     start = (now - timedelta(minutes=5)).strftime("%H:%M")
#     end = (now + timedelta(minutes=55)).strftime("%H:%M")
#     return [{"start": start, "end": end}]


# def classroom_row_exists(conn, college_id, classroom_name):
#     cur = None
#     try:
#         cur = conn.cursor()
#         cur.execute("""
#             SELECT id, college_id, classroom_name, classroom_table, classroom_faces, camera_input, slot, attendance_table
#             FROM public.classrooms
#             WHERE college_id = %s
#               AND classroom_name = %s
#             LIMIT 1
#         """, (college_id, classroom_name))
#         return cur.fetchone()
#     finally:
#         if cur:
#             cur.close()


# def main():
#     classroom_name = f"newclassroom_{int(datetime.now().timestamp())}"
#     slots = make_test_slots()

#     print("\n========== CLASSROOM + DYNAMIC TABLE TEST START ==========\n")

#     classroom = insert_new_classroom_local_and_cloud(
#         college_id=1,
#         classroom_name=classroom_name,
#         camera_input=0,
#         slots=slots
#     )

#     ok_classroom = classroom is not None
#     print_result("Create classroom in local + cloud", ok_classroom, f"Result: {classroom}")

#     if not classroom:
#         print("\nStop here. Classroom creation failed.\n")
#         return

#     student_table = classroom["classroom_table"]
#     attendance_table = classroom["attendance_table"]

#     ok_student = create_dynamic_student_table(student_table)
#     print_result("Create student table in local + cloud", ok_student, student_table)

#     ok_attendance = create_dynamic_attendance_table(attendance_table, slots)
#     print_result("Create attendance table in local + cloud", ok_attendance, attendance_table)

#     local_conn = None
#     cloud_conn = None

#     try:
#         local_conn = get_pg_connection()
#         cloud_conn = get_cloud_pg_connection()

#         local_classroom = classroom_row_exists(local_conn, 1, classroom_name)
#         cloud_classroom = classroom_row_exists(cloud_conn, 1, classroom_name)

#         local_student_exists = table_exists_in_connection(local_conn, student_table)
#         local_attendance_exists = table_exists_in_connection(local_conn, attendance_table)
#         cloud_student_exists = table_exists_in_connection(cloud_conn, student_table)
#         cloud_attendance_exists = table_exists_in_connection(cloud_conn, attendance_table)

#         print_result("Local classroom row exists", local_classroom is not None, str(local_classroom))
#         print_result("Cloud classroom row exists", cloud_classroom is not None, str(cloud_classroom))

#         print_result("Local student table exists", local_student_exists, student_table)
#         print_result("Local attendance table exists", local_attendance_exists, attendance_table)
#         print_result("Cloud student table exists", cloud_student_exists, student_table)
#         print_result("Cloud attendance table exists", cloud_attendance_exists, attendance_table)

#     except Exception as e:
#         print_result("Verification", False, str(e))
#     finally:
#         if local_conn:
#             local_conn.close()
#         if cloud_conn:
#             cloud_conn.close()

#     print("\n========== CLASSROOM + DYNAMIC TABLE TEST END ==========\n")


# if __name__ == "__main__":
#     main()



import os
import json
from datetime import date

from database import (
    startup_sync,
    init_local_database,
    is_internet_available,
    is_supabase_available,
    process_sync_queue,
    get_pending_sync_jobs,
    add_classroom,
    get_classroom_data_by_name,
    get_classroom_full_data_by_name,
    get_classrooms_by_college_id,
    update_classroom,
    add_student_to_classroom,
    mark_attendance_for_slot,
    get_attendance_by_date,
)


# ============================================================
# CONFIG - CHANGE THESE BEFORE RUNNING
# ============================================================

TEST_COLLEGE_ID = 1
TEST_CLASSROOM_NAME = "class_d"
UPDATED_CAMERA_INPUT = "1"

# Put a real image path here
TEST_STUDENT_IMAGE = r"pilli.jpg"

TEST_STUDENT_NAME = "Test Student D"
TEST_STUDENT_PRN = "PRN_CLASS_D_001"
TEST_STUDENT_PASSWORD = "1234"
TEST_STUDENT_EMAIL = "studentd@test.com"

INITIAL_SLOTS = [
    {"start": "00:00", "end": "23:59"}
]

UPDATED_SLOTS = [
    {"start": "00:00", "end": "23:59"}
]


# ============================================================
# HELPERS
# ============================================================

def line():
    print("=" * 70)


def section(title):
    line()
    print(title)
    line()


def ok(label, value=None):
    if value is None:
        print(f"[OK] {label}")
    else:
        print(f"[OK] {label}: {value}")


def fail(label, value=None):
    if value is None:
        print(f"[FAIL] {label}")
    else:
        print(f"[FAIL] {label}: {value}")


def show_json(label, data):
    print(f"{label}:")
    try:
        print(json.dumps(data, indent=2, default=str))
    except Exception:
        print(data)


def safe_run(label, func):
    try:
        result = func()
        ok(label)
        return result
    except Exception as e:
        fail(label, str(e))
        return None


# ============================================================
# TEST STEPS
# ============================================================

def test_environment():
    section("1. ENV / CONNECTIVITY CHECK")

    internet = is_internet_available()
    supabase_live = is_supabase_available()

    print(f"Internet Available : {internet}")
    print(f"Supabase Available : {supabase_live}")

    return internet, supabase_live


def test_startup():
    section("2. STARTUP SYNC")

    init_ok = init_local_database()
    print(f"init_local_database() -> {init_ok}")

    try:
        startup_sync()
        ok("startup_sync() completed")
    except Exception as e:
        fail("startup_sync()", str(e))


def test_add_classroom():
    section("3. ADD CLASSROOM")

    result = add_classroom(
        college_id=TEST_COLLEGE_ID,
        classroom_name=TEST_CLASSROOM_NAME,
        camera_input="0",
        slots=INITIAL_SLOTS
    )

    if result is None:
        fail("add_classroom returned None")
        return None

    if isinstance(result, dict) and result.get("error"):
        print(f"[INFO] add_classroom says: {result['error']}")
        return get_classroom_data_by_name(TEST_CLASSROOM_NAME)

    ok("add_classroom returned data")
    show_json("Created Classroom", result)
    return result


def test_get_classroom():
    section("4. GET CLASSROOM BY NAME")

    data = get_classroom_data_by_name(TEST_CLASSROOM_NAME)
    if not data:
        fail("get_classroom_data_by_name failed")
        return None

    ok("get_classroom_data_by_name")
    show_json("Classroom Data", data)

    full_data = get_classroom_full_data_by_name(TEST_CLASSROOM_NAME)
    if not full_data:
        fail("get_classroom_full_data_by_name failed")
        return data

    ok("get_classroom_full_data_by_name")
    show_json("Full Classroom Data", full_data)
    return full_data


def test_list_classrooms():
    section("5. GET CLASSROOMS BY COLLEGE ID")

    rows = get_classrooms_by_college_id(TEST_COLLEGE_ID)

    if rows is None:
        fail("get_classrooms_by_college_id returned None")
        return []

    ok("get_classrooms_by_college_id", f"{len(rows)} classrooms found")
    show_json("Classrooms", rows)
    return rows


def test_update_classroom(classroom_data):
    section("6. UPDATE CLASSROOM")

    if not classroom_data:
        fail("No classroom data available for update")
        return None

    classroom_id = classroom_data["id"]

    result = update_classroom(
        classroom_id=classroom_id,
        classroom_name=TEST_CLASSROOM_NAME,
        camera_input=UPDATED_CAMERA_INPUT,
        slots=UPDATED_SLOTS
    )

    if not result:
        fail("update_classroom failed")
        return None

    ok("update_classroom")
    show_json("Updated Classroom", result)
    return result


def test_add_student():
    section("7. ADD STUDENT")

    if not os.path.exists(TEST_STUDENT_IMAGE):
        fail("Student image file not found", TEST_STUDENT_IMAGE)
        print("Put a valid image file path in TEST_STUDENT_IMAGE before testing this step.")
        return None

    result = add_student_to_classroom(
        class_name=TEST_CLASSROOM_NAME,
        student_name=TEST_STUDENT_NAME,
        file_path=TEST_STUDENT_IMAGE,
        student_prn=TEST_STUDENT_PRN,
        password=TEST_STUDENT_PASSWORD,
        email=TEST_STUDENT_EMAIL
    )

    if not result:
        fail("add_student_to_classroom failed")
        return None

    ok("add_student_to_classroom")
    show_json("Added Student", result)
    return result


def test_mark_attendance():
    section("8. MARK ATTENDANCE")

    recognized_people = [TEST_STUDENT_PRN]

    result = mark_attendance_for_slot(
        class_name=TEST_CLASSROOM_NAME,
        recognized_people=recognized_people
    )

    print(f"mark_attendance_for_slot() -> {result}")
    if result:
        ok("Attendance marked")
    else:
        fail("Attendance marking failed")

    return result


def test_get_attendance():
    section("9. GET ATTENDANCE")

    today = str(date.today())
    rows = get_attendance_by_date(TEST_CLASSROOM_NAME, today)

    if rows is None:
        fail("get_attendance_by_date returned None")
        return []

    ok("get_attendance_by_date", f"{len(rows)} records found")
    show_json("Attendance Rows", rows)
    return rows


def test_sync_queue():
    section("10. SYNC QUEUE STATUS")

    pending_before = get_pending_sync_jobs(200)
    ok("Fetched pending sync jobs before processing", len(pending_before))
    show_json("Pending Jobs Before", pending_before)

    process_result = process_sync_queue()
    print(f"process_sync_queue() -> {process_result}")

    pending_after = get_pending_sync_jobs(200)
    ok("Fetched pending sync jobs after processing", len(pending_after))
    show_json("Pending Jobs After", pending_after)

    return pending_before, pending_after


# ============================================================
# MAIN RUNNER
# ============================================================

def main():
    section("DATABASE FLOW TEST START")

    print("Test classroom name:", TEST_CLASSROOM_NAME)
    print("Test college id    :", TEST_COLLEGE_ID)
    print("Today              :", str(date.today()))
    print("Student image path :", TEST_STUDENT_IMAGE)

    internet, supabase_live = test_environment()
    test_startup()

    created = test_add_classroom()
    fetched = test_get_classroom()
    test_list_classrooms()
    updated = test_update_classroom(fetched or created)
    student = test_add_student()
    attendance_marked = test_mark_attendance()
    attendance_rows = test_get_attendance()
    pending_before, pending_after = test_sync_queue()

    section("FINAL SUMMARY")

    print(f"Internet Available          : {internet}")
    print(f"Supabase Available          : {supabase_live}")
    print(f"Classroom Created/Fetched   : {bool(created or fetched)}")
    print(f"Classroom Updated           : {bool(updated)}")
    print(f"Student Added               : {bool(student)}")
    print(f"Attendance Marked           : {bool(attendance_marked)}")
    print(f"Attendance Rows Found       : {len(attendance_rows) if attendance_rows is not None else 0}")
    print(f"Pending Jobs Before Sync    : {len(pending_before) if pending_before is not None else 0}")
    print(f"Pending Jobs After Sync     : {len(pending_after) if pending_after is not None else 0}")

    line()
    print("DONE")
    line()


if __name__ == "__main__":
    main()