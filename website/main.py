from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
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
    defaulter_students,
    current_month_range,
    get_attendance_of_class,
    update_attendance_slot,
    update_class_teacher,
    update_defaulter_threshold,
    search, 
    reset_session
    
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
def     student_dashboard(request: Request):
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

    for date, data in attendance.items():

        if isinstance(data, dict):
            slots = data.get("slots", [])
        else:
            slots = data  

        present_count = 0
        absent_count = 0
        pending_count = 0

        for row in slots:

            if isinstance(row, dict):
                status = row.get("status", "").lower()
            else:
                status = str(row).lower()

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

    classroom_data = {}

    total_students = 0
    total_defaulters = 0
    total_present = 0
    total_absent = 0

    class_performance = []
    teacher_stats = {}
    slot_stats = {}
    daily_map = {}

    for classroom in classrooms:

        classroom_id = classroom["id"]

        students = get_students_from_classroom_table(classroom["classroom_table"])
        defaulters = defaulter_students(classroom["college_id"], classroom_id) or []

        student_count = len(students)
        defaulter_count = len([d for d in defaulters if d["defaulter"] == "YES"])

        total_students += student_count
        total_defaulters += defaulter_count

        attendance_rows = get_attendance_of_class(classroom["attendance_table"])
        rows = attendance_rows.data or []

        present = 0
        absent = 0

        for row in rows:

            row_date = str(row.get("attendance_date"))

            if row_date not in daily_map:
                daily_map[row_date] = {"present":0,"absent":0}

            for key, value in row.items():

                if key.startswith("slot_") and not key.endswith("_teacher"):

                    val = str(value).lower()

                    teacher_name = row.get(f"{key}_teacher", "Unknown")

                    if key not in slot_stats:
                        slot_stats[key] = {"present":0,"absent":0}

                    if teacher_name not in teacher_stats:
                        teacher_stats[teacher_name] = {"present":0,"absent":0}

                    if val == "present":
                        present += 1
                        total_present += 1
                        daily_map[row_date]["present"] += 1
                        slot_stats[key]["present"] += 1
                        teacher_stats[teacher_name]["present"] += 1

                    elif val == "absent":
                        absent += 1
                        total_absent += 1
                        daily_map[row_date]["absent"] += 1
                        slot_stats[key]["absent"] += 1
                        teacher_stats[teacher_name]["absent"] += 1

        total = present + absent
        percent = round((present / total * 100), 2) if total > 0 else 0

        class_performance.append({
            "class": classroom["classroom_name"],
            "percent": percent,
            "defaulters": defaulter_count
        })

        classroom_data[classroom_id] = {
            "student_count": student_count,
            "defaulter_count": defaulter_count
        }

    overall_percent = round(
        (total_present / (total_present + total_absent) * 100), 2
    ) if (total_present + total_absent) > 0 else 0

    best_class = max(class_performance, key=lambda x:x["percent"], default=None)
    worst_class = min(class_performance, key=lambda x:x["percent"], default=None)

    avg_class_attendance = round(
        sum(x["percent"] for x in class_performance) / len(class_performance),2
    ) if class_performance else 0

    trend_labels = sorted(daily_map.keys())
    trend_values = []

    for d in trend_labels:
        p = daily_map[d]["present"]
        a = daily_map[d]["absent"]
        total = p + a
        perc = round((p/total*100),2) if total > 0 else 0
        trend_values.append(perc)

    teacher_board = []

    for t,v in teacher_stats.items():
        total = v["present"] + v["absent"]
        perc = round((v["present"]/total*100),2) if total>0 else 0
        teacher_board.append({"teacher":t,"percent":perc})

    teacher_board = sorted(teacher_board,key=lambda x:x["percent"],reverse=True)

    slot_board = []

    for s,v in slot_stats.items():
        total = v["present"] + v["absent"]
        perc = round((v["present"]/total*100),2) if total>0 else 0
        slot_board.append({"slot":s,"percent":perc})

    prediction = round(sum(trend_values[-5:]) / len(trend_values[-5:]),2) if trend_values else overall_percent

    alerts = []

    if overall_percent < 75:
        alerts.append("Overall attendance below 75%")

    if total_defaulters > 10:
        alerts.append("High defaulter count detected")

    if worst_class:
        alerts.append(f"Needs attention: {worst_class['class']}")

    return templates.TemplateResponse(
        "main_dashboard.html",
        {
            "request": request,
            "college": CURRENT_COLLEGE,
            "classrooms": classrooms,
            "classroom_data": classroom_data,
            "classroom_count": len(classrooms),
            "student_count": total_students,
            "defaulter_count": total_defaulters,
            "teacher_count": len(teachers),
            "current_role": CURRENT_USER["role"],
            "overall_percent": overall_percent,
            "best_class": best_class,
            "worst_class": worst_class,
            "avg_class_attendance": avg_class_attendance,
            "class_performance": class_performance,
            "trend_labels": trend_labels,
            "trend_values": trend_values,
            "teacher_board": teacher_board[:5],
            "slot_board": slot_board,
            "prediction": prediction,
            "alerts": alerts
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
    
@app.post("/classroom/{classroom_id}/set-defaulter")
def set_defaulter(
    classroom_id: int,
    defaulter: int = Form(...)
):
    if CURRENT_USER["role"] not in ["teacher", "hod"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    result = update_defaulter_threshold(classroom_id, defaulter)

    if not result:
        raise HTTPException(status_code=400, detail="Update failed")

    return RedirectResponse(url=f"/classroom/{classroom_id}", status_code=303)

@app.post("/classroom/{classroom_id}/set-teacher")
def set_teacher(
    classroom_id: int,
    class_teacher: str = Form(...)
):
    if CURRENT_USER["role"] != "hod":
        raise HTTPException(status_code=403, detail="Unauthorized")

    result = update_class_teacher(
                    classroom_id,
                    class_teacher.strip(),
                    CURRENT_USER["college_id"]
                )

    if not result:
        raise HTTPException(status_code=400, detail="Update failed")

    return RedirectResponse(url=f"/classroom/{classroom_id}", status_code=303)

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
        
    defaulter_count = sum(1 for student in students if student.get("defaulter") == "YES")
        
    base_url = str(request.base_url).rstrip("/")
    student_join_link = f"http://127.0.0.1:8000/student/invite/{CURRENT_COLLEGE['id']}/{classroom['id']}"
    teacher_join_link = f"{base_url}/teacher/join"
    teachers = get_teachers_by_college(CURRENT_USER["college_id"])

    return templates.TemplateResponse(
        "class_dashboard.html",
        {
            "request": request,
            "college": CURRENT_COLLEGE,
            "classroom": classroom,
            "students": students,
            "defualters_count" : defaulter_count,
            "student_count": len(students),
            "error_message": None,
            "success_message": None,
            "current_role": CURRENT_USER["role"],
            "student_join_link": student_join_link,
            "teacher_join_link": teacher_join_link,
            "teachers": teachers,
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

    for date, data in attendance.items():
        slots = data.get("slots", [])

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
            "class_teacher" : classroom["class_teacher"],
            "present_chart_data": present_chart_data,
            "absent_chart_data": absent_chart_data,
            "pending_chart_data": pending_chart_data,
            "current_role": CURRENT_USER["role"],
        }
    )

@app.post("/attendance/update")
async def update_attendance(
    request: Request,
    classroom_id: int = Form(...),
    prn: str = Form(...),
    attendance_date: str = Form(...),
    slot_label: str = Form(...),
    new_status: str = Form(...)
):
    if CURRENT_USER["role"] not in ["teacher", "hod"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    success = update_attendance_slot(
        college_id=CURRENT_USER["college_id"],
        classroom_id=classroom_id,
        prn=prn,
        attendance_date=attendance_date,
        slot_label=slot_label,
        new_status=new_status,
        teacher_name=CURRENT_USER["name"]
    )

    if not success:
        raise HTTPException(status_code=400, detail="Update failed")

    return {"message": "Attendance updated"}

@app.get("/classroom/{classroom_id}/export/csv")
def export_classroom_csv(classroom_id: int):
    if CURRENT_USER["college_id"] is None or not CURRENT_USER["role"]:
        return RedirectResponse(url="/", status_code=303)

    classroom = get_classroom_by_id(classroom_id)

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    if classroom["college_id"] != CURRENT_USER["college_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    classroom_table = classroom["classroom_table"]
    attendance_table = classroom["attendance_table"]

    students_res = get_students_from_classroom_table(classroom_table)

    students = {s["prn"]: s for s in (students_res or [])}

    attendance_res = get_attendance_of_class(attendance_table)
    attendance_rows = attendance_res.data or []
    attendance_rows = sorted(
    attendance_rows,
    key=lambda x: (
        str(x.get("prn", ""))
    )
)
    slot_columns = set()
    for row in attendance_rows:
        for key in row.keys():
            if key.startswith("slot_"):
                slot_columns.add(key)

    slot_columns = sorted(slot_columns)

    def format_slot(slot):
        return slot.replace("slot_", "").replace("_", ":")

    formatted_slots = [format_slot(s) for s in slot_columns]

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Student Name", "PRN", "Email", "Date", *formatted_slots
    ])

    for row in attendance_rows:
        prn = row.get("prn")
        student = students.get(prn, {})

        csv_row = [
            student.get("student_name", ""),
            prn,
            student.get("email", ""),
            row.get("attendance_date", "")
        ]

        for slot in slot_columns:
            csv_row.append(row.get(slot, "pending"))

        writer.writerow(csv_row)

    output.seek(0)

    safe_classroom_name = classroom["classroom_name"].replace(" ", "_").lower()

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={safe_classroom_name}_attendance.csv"
        }
    )
    
load_dotenv()

groq = Groq(api_key=os.getenv("API_KEY"))

class ChatRequest(BaseModel):
    query: str
    file_name: str
    session_id: str


@app.post("/chat/groq")
def chat_groq(request: ChatRequest):

    contexts = search(
        request.file_name,
        request.query,
        request.session_id
    )

    context = "\n".join(contexts)

    response = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "Answer only using context"
            },
            {
                "role": "user",
                "content": f"""
Context:
{context}

Question:
{request.query}

Answer:
"""
            }
        ],
        temperature=0.3
    )

    return {
        "answer": response.choices[0].message.content
    }

@app.post("/reset")
def reset(session_id: str):
    reset_session(session_id)
    return {"message": "session reset"}
    
#End