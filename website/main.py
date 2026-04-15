from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import csv
import io

from utils import (
    router,
    get_classrooms_by_college,
    get_classroom_by_id,
    get_students_from_classroom_table,
    add_student_to_classroom_web,
    student_login,
    teacher_login,
    hod_login,
    hod_signup,
    get_student_dashboard_data,
    get_student_dashboard_data_by_prn,
    get_teachers_by_college,
    add_teacher_by_invite,
    get_college_by_id,
    defaulter_students
    
)

app = FastAPI()
app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


CURRENT_COLLEGE = {
    "id": None,
    "college_name": None,
    "creator": None,
    "creator_email": None
}

CURRENT_STUDENT = {
    "name": None,
    "email": None,
    "college_id": None,
    "classroom_id": None
}

CURRENT_USER = {
    "name": None,
    "email": None,
    "role": None,   
    "college_id": None
}


def reset_current_student():
    CURRENT_STUDENT["name"] = None
    CURRENT_STUDENT["email"] = None
    CURRENT_STUDENT["college_id"] = None
    CURRENT_STUDENT["classroom_id"] = None


def reset_current_user():
    CURRENT_USER["name"] = None
    CURRENT_USER["email"] = None
    CURRENT_USER["role"] = None
    CURRENT_USER["college_id"] = None


def reset_current_college():
    CURRENT_COLLEGE["id"] = None
    CURRENT_COLLEGE["college_name"] = None
    CURRENT_COLLEGE["creator"] = None
    CURRENT_COLLEGE["creator_email"] = None


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "new_home.html",
        {
            "request": request,
            "error": None,
            "success": None,
            "open_panel": False,
            "active_role": "student",
            "active_mode": "login",
        }
    )


@app.get("/logout")
def logout():
    reset_current_student()
    reset_current_user()
    reset_current_college()
    return RedirectResponse(url="/", status_code=303)


@app.post("/auth")
def auth_action(
    request: Request,
    role: str = Form(...),
    mode: str = Form(...),

    student_name: str = Form(""),
    student_email: str = Form(""),
    student_password: str = Form(""),
    student_college_id: str = Form(""),
    student_classroom_id: str = Form(""),

    teacher_college_id: str = Form(""),
    teacher_name: str = Form(""),
    teacher_email: str = Form(""),
    teacher_password: str = Form(""),

    hod_login_name: str = Form(""),
    hod_login_college_name: str = Form(""),
    hod_login_email: str = Form(""),
    hod_login_password: str = Form(""),

    hod_signup_name: str = Form(""),
    hod_signup_college_name: str = Form(""),
    hod_signup_email: str = Form(""),
    hod_signup_password: str = Form(""),
):
    if role == "student":
        result = student_login(
            name=student_name,
            email=student_email,
            password=student_password,
            college_id=student_college_id,
            classroom_id=student_classroom_id,
        )

        if not result:
            return templates.TemplateResponse(
                "new_home.html",
                {
                    "request": request,
                    "error": "Student not found in that classroom. You are not enrolled.",
                    "success": None,
                    "open_panel": True,
                    "active_role": "student",
                    "active_mode": "login",
                }
            )

        reset_current_user()

        CURRENT_STUDENT["name"] = student_name.strip()
        CURRENT_STUDENT["email"] = student_email.strip()
        CURRENT_STUDENT["college_id"] = int(student_college_id)
        CURRENT_STUDENT["classroom_id"] = int(student_classroom_id)

        return RedirectResponse(url="/student/dashboard", status_code=303)

    if role == "teacher":
        result = teacher_login(
            college_id=teacher_college_id,
            teacher_name=teacher_name,
            email=teacher_email,
            password=teacher_password,
        )

        if not result:
            return templates.TemplateResponse(
                "new_home.html",
                {
                    "request": request,
                    "error": "Teacher login failed.",
                    "success": None,
                    "open_panel": True,
                    "active_role": "teacher",
                    "active_mode": "login",
                }
            )

        reset_current_student()

        CURRENT_USER["name"] = teacher_name.strip()
        CURRENT_USER["email"] = teacher_email.strip()
        CURRENT_USER["role"] = "teacher"
        CURRENT_USER["college_id"] = result["college_id"]

        CURRENT_COLLEGE["id"] = result["college_id"]
        CURRENT_COLLEGE["college_name"] = "College"
        CURRENT_COLLEGE["creator"] = teacher_name.strip()
        CURRENT_COLLEGE["creator_email"] = teacher_email.strip()

        return RedirectResponse(url="/dashboard", status_code=303)

    if role == "hod" and mode == "login":
        result = hod_login(
            name=hod_login_name,
            college_name=hod_login_college_name,
            email=hod_login_email,
            password=hod_login_password,
        )

        if not result:
            return templates.TemplateResponse(
                "new_home.html",
                {
                    "request": request,
                    "error": "HOD / Principal login failed.",
                    "success": None,
                    "open_panel": True,
                    "active_role": "hod",
                    "active_mode": "login",
                }
            )

        reset_current_student()

        CURRENT_USER["name"] = hod_login_name.strip()
        CURRENT_USER["email"] = hod_login_email.strip()
        CURRENT_USER["role"] = "hod"
        CURRENT_USER["college_id"] = result["id"]

        CURRENT_COLLEGE["id"] = result["id"]
        CURRENT_COLLEGE["college_name"] = result["college_name"]
        CURRENT_COLLEGE["creator"] = result["creator"]
        CURRENT_COLLEGE["creator_email"] = result["creator_email"]

        return RedirectResponse(url="/dashboard", status_code=303)

    if role == "hod" and mode == "signup":
        result = hod_signup(
            name=hod_signup_name,
            college_name=hod_signup_college_name,
            email=hod_signup_email,
            password=hod_signup_password,
        )

        if not result:
            return templates.TemplateResponse(
                "new_home.html",
                {
                    "request": request,
                    "error": "Signup failed. College or HOD may already exist.",
                    "success": None,
                    "open_panel": True,
                    "active_role": "hod",
                    "active_mode": "signup",
                }
            )

        return templates.TemplateResponse(
            "new_home.html",
            {
                "request": request,
                "error": None,
                "success": "HOD account created successfully. Now log in.",
                "open_panel": True,
                "active_role": "hod",
                "active_mode": "login",
            }
        )

    return templates.TemplateResponse(
        "new_home.html",
        {
            "request": request,
            "error": "Invalid request.",
            "success": None,
            "open_panel": True,
            "active_role": "student",
            "active_mode": "login",
        }
    )
@app.get("/teacher/invite/{college_id}")
def teacher_invite_page(request: Request, college_id: int):
    return templates.TemplateResponse(
        "teacher_invite_login.html",
        {
            "request": request,
            "college_id": college_id,
            "error": None,
            "success": None,
        }
    )
@app.post("/teacher/invite/{college_id}")
def teacher_invite_signup(
    request: Request,
    college_id: int,
    teacher_name: str = Form(...),
    teacher_email: str = Form(...),
    teacher_password: str = Form(...),
):
    result = add_teacher_by_invite(
        college_id=college_id,
        teacher_name=teacher_name.strip(),
        email=teacher_email.strip(),
        password=teacher_password.strip(),
    )

    if not result:
        return templates.TemplateResponse(
            "teacher_invite_login.html",
            {
                "request": request,
                "college_id": college_id,
                "error": "Teacher signup failed. Email may already exist or college is invalid.",
                "success": None,
            },
            status_code=400
        )

    reset_current_student()

    CURRENT_USER["name"] = teacher_name.strip()
    CURRENT_USER["email"] = teacher_email.strip()
    CURRENT_USER["role"] = "teacher"
    CURRENT_USER["college_id"] = int(college_id)

    college = get_college_by_id(int(college_id))
    if not college:
        return templates.TemplateResponse(
            "teacher_invite_login.html",
            {
                "request": request,
                "college_id": college_id,
                "error": "College not found.",
                "success": None,
            },
            status_code=404
        )

    CURRENT_COLLEGE["id"] = college["id"]
    CURRENT_COLLEGE["college_name"] = college["college_name"]
    CURRENT_COLLEGE["creator"] = college["creator"]
    CURRENT_COLLEGE["creator_email"] = college["creator_email"]

    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/student/invite/{college_id}/{classroom_id}")
def student_invite_page(request: Request, college_id: int, classroom_id: int):
    return templates.TemplateResponse(
        "student_invite_login.html",
        {
            "request": request,
            "college_id": college_id,
            "classroom_id": classroom_id,
            "error": None,
            "success": None,
        }
    )
    
@app.post("/student/invite/{college_id}/{classroom_id}")
async def student_invite_submit(
    request: Request,
    college_id: int,
    classroom_id: int,
    student_name: str = Form(...),
    prn: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    image: UploadFile = File(...)
):
    classroom = get_classroom_by_id(classroom_id)

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    if classroom["college_id"] != college_id:
        raise HTTPException(status_code=403, detail="This classroom does not belong to this college")

    result = await add_student_to_classroom_web(
        classroom=classroom,
        student_name=student_name.strip(),
        student_prn=prn.strip(),
        email=email.strip(),
        password=password.strip(),
        upload_file=image
    )

    if not result:
        return templates.TemplateResponse(
            "student_invite_login.html",
            {
                "request": request,
                "college_id": college_id,
                "classroom_id": classroom_id,
                "error": "Failed to join classroom.",
                "success": None,
            },
            status_code=400
        )

    return templates.TemplateResponse(
        "student_invite_login.html",
        {
            "request": request,
            "college_id": college_id,
            "classroom_id": classroom_id,
            "error": None,
            "success": "Student added successfully. Now login from home page.",
        }
    )
    
@app.post("/student/invite/login")
def student_invite_login(
    request: Request,
    college_id: str = Form(...),
    classroom_id: str = Form(...),
    student_name: str = Form(...),
    student_email: str = Form(...),
    student_password: str = Form(...),
):
    result = student_login(
        name=student_name,
        email=student_email,
        password=student_password,
        college_id=college_id,
        classroom_id=classroom_id,
    )

    if not result:
        return templates.TemplateResponse(
            "student_invite_login.html",
            {
                "request": request,
                "college_id": college_id,
                "classroom_id": classroom_id,
                "error": "Student login failed. Check your details.",
                "success": None,
            }
        )

    reset_current_user()

    CURRENT_STUDENT["name"] = student_name.strip()
    CURRENT_STUDENT["email"] = student_email.strip()
    CURRENT_STUDENT["college_id"] = int(college_id)
    CURRENT_STUDENT["classroom_id"] = int(classroom_id)

    return RedirectResponse(url="/student/dashboard", status_code=303)


@app.get("/student/dashboard")
def student_dashboard(request: Request):
    if (
        not CURRENT_STUDENT["name"]
        or not CURRENT_STUDENT["email"]
        or CURRENT_STUDENT["college_id"] is None
        or CURRENT_STUDENT["classroom_id"] is None
    ):
        return RedirectResponse(url="/", status_code=303)

    dashboard_data = get_student_dashboard_data(
        student_name=CURRENT_STUDENT["name"],
        student_email=CURRENT_STUDENT["email"],
        college_id=CURRENT_STUDENT["college_id"],
        classroom_id=CURRENT_STUDENT["classroom_id"],
    )

    if not dashboard_data:
        return templates.TemplateResponse(
            "new_home.html",
            {
                "request": request,
                "error": "Unable to load student dashboard.",
                "success": None,
                "open_panel": True,
                "active_role": "student",
                "active_mode": "login",
            }
        )

    attendance = dashboard_data.get("attendance", {})

    chart_labels = []
    present_chart_data = []
    absent_chart_data = []
    pending_chart_data = []

    for date, slots in attendance.items():
        present_count = 0
        absent_count = 0
        pending_count = 0

        for row in slots:
            status = row.get("status", "").lower()
            if status == "present":
                present_count += 1
            elif status == "absent":
                absent_count += 1
            else:
                pending_count += 1

        chart_labels.append(date)
        present_chart_data.append(present_count)
        absent_chart_data.append(absent_count)
        pending_chart_data.append(pending_count)

    return templates.TemplateResponse(
        "new_student.html",
        {
            "request": request,
            **dashboard_data,
            "chart_labels": chart_labels,
            "present_chart_data": present_chart_data,
            "absent_chart_data": absent_chart_data,
            "pending_chart_data": pending_chart_data,
        }
    )


@app.get("/dashboard")
def dashboard(request: Request):
    classrooms = get_classrooms_by_college(CURRENT_COLLEGE["id"])
    teachers = get_teachers_by_college(CURRENT_COLLEGE["id"]) if CURRENT_USER["role"] == "hod" else []

    return templates.TemplateResponse(
        "main_dashboard.html",
        {
            "request": request,
            "college": CURRENT_COLLEGE,
            "classrooms": classrooms,
            "classroom_count": len(classrooms),
            "teacher_count": len(teachers),
            "current_role": CURRENT_USER["role"]
        }
    )

@app.get("/staff")
def staff_dashboard(request: Request):
    if CURRENT_USER["role"] != "hod":
        raise HTTPException(status_code=403, detail="Only HOD can view staff page")

    teachers = get_teachers_by_college(CURRENT_COLLEGE["id"])
    teacher_invite_link = f"http://127.0.0.1:8000/teacher/invite/{CURRENT_COLLEGE['id']}"

    return templates.TemplateResponse(
        "staff_dashboard.html",
        {
            "request": request,
            "college": CURRENT_COLLEGE,
            "teachers": teachers,
            "teacher_count": len(teachers),
            "teacher_invite_link": teacher_invite_link,
            "error_message": None,
            "success_message": None,
        }
    )
@app.get("/classroom/{classroom_id}")
def classroom_dashboard(request: Request, classroom_id: int):
    if CURRENT_USER["college_id"] is None or not CURRENT_USER["role"]:
        return RedirectResponse(url="/", status_code=303)

    classroom = get_classroom_by_id(classroom_id)

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    if classroom["college_id"] != CURRENT_USER["college_id"]:
        raise HTTPException(status_code=403, detail="This classroom does not belong to current college")

    students = get_students_from_classroom_table(classroom["classroom_table"])
    defaulters = defaulter_students(classroom["college_id"] ,classroom_id)

    defaulter_map = {d["prn"]: d["defaulter"] for d in defaulters}

    for student in students:
        student["defaulter"] = defaulter_map.get(student.get("prn"), "NO")
        
    base_url = str(request.base_url).rstrip("/")
    student_join_link = f"http://127.0.0.1:8000/student/invite/{CURRENT_COLLEGE['id']}/{classroom['id']}"
    teacher_join_link = f"{base_url}/teacher/join"

    return templates.TemplateResponse(
        "class_dashboard.html",
        {
            "request": request,
            "college": CURRENT_COLLEGE,
            "classroom": classroom,
            "students": students,
            "student_count": len(students),
            "error_message": None,
            "success_message": None,
            "current_role": CURRENT_USER["role"],
            "student_join_link": student_join_link,
            "teacher_join_link": teacher_join_link,
        }
    )


@app.post("/classroom/{classroom_id}/add-student")
async def add_student_web(
    request: Request,
    classroom_id: int,
    student_name: str = Form(...),
    prn: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    image: UploadFile = File(...)
):
    if CURRENT_USER["college_id"] is None or not CURRENT_USER["role"]:
        return RedirectResponse(url="/", status_code=303)

    classroom = get_classroom_by_id(classroom_id)

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    if classroom["college_id"] != CURRENT_USER["college_id"]:
        raise HTTPException(status_code=403, detail="This classroom does not belong to current college")

    student_name = student_name.strip()
    prn = prn.strip()
    email = email.strip()
    password = password.strip()

    students = get_students_from_classroom_table(classroom["classroom_table"])
    base_url = str(request.base_url).rstrip("/")
    student_join_link = f"{base_url}/student/join?classroom_id={classroom_id}"
    teacher_join_link = f"{base_url}/teacher/join"

    if not student_name or not prn or not email or not password:
        return templates.TemplateResponse(
            "class_dashboard.html",
            {
                "request": request,
                "college": CURRENT_COLLEGE,
                "classroom": classroom,
                "students": students,
                "student_count": len(students),
                "error_message": "All fields are required.",
                "success_message": None,
                "current_role": CURRENT_USER["role"],
                "student_join_link": student_join_link,
                "teacher_join_link": teacher_join_link,
            },
            status_code=400
        )

    if not image or not image.filename:
        return templates.TemplateResponse(
            "class_dashboard.html",
            {
                "request": request,
                "college": CURRENT_COLLEGE,
                "classroom": classroom,
                "students": students,
                "student_count": len(students),
                "error_message": "Please select an image.",
                "success_message": None,
                "current_role": CURRENT_USER["role"],
                "student_join_link": student_join_link,
                "teacher_join_link": teacher_join_link,
            },
            status_code=400
        )

    result = await add_student_to_classroom_web(
        classroom=classroom,
        student_name=student_name,
        student_prn=prn,
        email=email,
        password=password,
        upload_file=image
    )

    if not result:
        students = get_students_from_classroom_table(classroom["classroom_table"])
        return templates.TemplateResponse(
            "class_dashboard.html",
            {
                "request": request,
                "college": CURRENT_COLLEGE,
                "classroom": classroom,
                "students": students,
                "student_count": len(students),
                "error_message": "Failed to add student.",
                "success_message": None,
                "current_role": CURRENT_USER["role"],
                "student_join_link": student_join_link,
                "teacher_join_link": teacher_join_link,
            },
            status_code=500
        )

    return RedirectResponse(
        url=f"/classroom/{classroom_id}",
        status_code=303
    )


@app.get("/student/view/{classroom_id}/{prn}")
def view_student_page(request: Request, classroom_id: int, prn: str):
    if CURRENT_USER["college_id"] is None or not CURRENT_USER["role"]:
        return RedirectResponse(url="/", status_code=303)

    classroom = get_classroom_by_id(classroom_id)

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    if classroom["college_id"] != CURRENT_USER["college_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized classroom access")

    dashboard_data = get_student_dashboard_data_by_prn(
        college_id=classroom["college_id"],
        classroom_id=classroom_id,
        prn=prn
    )

    if not dashboard_data:
        raise HTTPException(status_code=404, detail="Student dashboard not found")

    attendance = dashboard_data.get("attendance", {})

    chart_labels = []
    present_chart_data = []
    absent_chart_data = []
    pending_chart_data = []

    for date, slots in attendance.items():
        present_count = 0
        absent_count = 0
        pending_count = 0

        for row in slots:
            status = row.get("status", "").lower()
            if status == "present":
                present_count += 1
            elif status == "absent":
                absent_count += 1
            else:
                pending_count += 1

        chart_labels.append(date)
        present_chart_data.append(present_count)
        absent_chart_data.append(absent_count)
        pending_chart_data.append(pending_count)

    return templates.TemplateResponse(
        "new_student.html",
        {
            "request": request,
            **dashboard_data,
            "chart_labels": chart_labels,
            "present_chart_data": present_chart_data,
            "absent_chart_data": absent_chart_data,
            "pending_chart_data": pending_chart_data,
        }
    )


@app.get("/classroom/{classroom_id}/export/csv")
def export_classroom_csv(classroom_id: int):
    if CURRENT_USER["college_id"] is None or not CURRENT_USER["role"]:
        return RedirectResponse(url="/", status_code=303)

    classroom = get_classroom_by_id(classroom_id)

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    if classroom["college_id"] != CURRENT_USER["college_id"]:
        raise HTTPException(status_code=403, detail="This classroom does not belong to current college")

    students = get_students_from_classroom_table(classroom["classroom_table"])

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Student Name", "PRN", "Email"])

    for student in students:
        writer.writerow([
            student.get("student_name", ""),
            student.get("prn", ""),
            student.get("email", "")
        ])

    output.seek(0)

    safe_classroom_name = classroom["classroom_name"].replace(" ", "_").lower()

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={safe_classroom_name}_students.csv"
        }
    )