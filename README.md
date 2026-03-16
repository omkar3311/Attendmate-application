# Attendmate-application

AttendMate is an AI-powered attendance management system built to automate classroom attendance using face recognition and provide a complete management portal for HODs, teachers, and students.

It combines:

- a **desktop application** for live camera-based attendance
- a **web application** for managing colleges, classrooms, teachers, students, and attendance reports

The goal of the project is to reduce manual attendance work, improve visibility of attendance records, and provide a smoother academic workflow.

---

## Overview

AttendMate has two main modules:

### 1. Desktop Application
The desktop application is used for live classroom monitoring and attendance marking.

It:
- connects to classroom cameras
- checks whether a classroom slot is currently active
- runs face recognition on the camera feed
- detects recognized students in real time
- automatically marks attendance for the active slot
- allows classroom editing and student addition directly from the desktop interface

### 2. Web Application
The web application is used for administration and attendance monitoring.

It supports:
- HOD signup and login
- teacher login and invite-based onboarding
- student login and invite-based onboarding
- classroom management
- student management
- attendance dashboard viewing
- attendance chart visualization
- CSV export of classroom student data

---

## Core Features

### AI-Based Attendance Marking
- Live camera feed processing
- Face recognition using a recognition engine
- Attendance marking only during active classroom slots
- Periodic database updates for recognized students
- Camera on/off support for each classroom

### Classroom Management
- Create classrooms with:
  - classroom name
  - camera source
  - attendance slots
- Edit classroom details
- View classroom-wise students
- Load saved classrooms automatically

### Student Management
- Add students with:
  - name
  - PRN
  - email
  - password
  - image
- Reload known faces after adding new students
- View recognized and unknown people in classroom feed

### Role-Based Web Access
- **HOD / Principal**
  - signup and login
  - manage college-level dashboard
  - view classrooms
  - manage staff
  - invite teachers

- **Teacher**
  - login
  - access classroom dashboard
  - manage students in assigned college/classrooms

- **Student**
  - login
  - access attendance dashboard
  - view attendance summary
  - view date-wise attendance details
  - view attendance chart

### Attendance Dashboard
- present count
- absent count
- pending count
- attendance percentage
- date-wise slot attendance breakdown
- stacked attendance chart for visual analysis

### Data Export
- export classroom student list as CSV

---

## Project Structure

```bash
AttendMate/
├── application/
│   ├── camera.py
│   ├── database.py
│   ├── faces/
│   ├── login.py
│   ├── main_dashboard.py
│   ├── main_dashboard.qss
│   ├── main.py
│   ├── recognition.py
│   ├── student_dashboard.py
│   ├── student_dashboard.qss
│   ├── style.qss
│   └── yolov8n.pt
│
├── website/
│   ├── main.py
│   ├── utils.py
│   ├── static/
│   │   └── icon.ico
│   └── templates/
│       ├── class_dashboard.html
│       ├── main_dashboard.html
│       ├── new_home.html
│       ├── new_student.html
│       ├── staff_dashboard.html
│       ├── student_invite_login.html
│       └── teacher_invite_login.html
│
└── README.md
```

## Main Modules

### Desktop Application

The desktop application is used for live classroom attendance operations.

It allows the user to:

- connect a camera source for a classroom
- define active attendance slots for each classroom
- detect and recognize students through the camera feed
- automatically mark attendance only during active time slots
- monitor multiple classroom camera feeds
- add new classrooms
- edit classroom details
- add students with image data
- reload face data after adding new students
- view recognized and unknown people inside a classroom feed

The desktop app also monitors CPU and RAM usage so that multiple classroom cameras can be loaded in a safer and more controlled way.

---

### Web Application

The web application is used for academic and administrative management.

It provides:

- HOD / Principal signup and login
- teacher login and invite-based registration
- student login and invite-based registration
- classroom dashboards
- staff dashboard
- student attendance dashboard
- attendance chart visualization
- classroom-wise student viewing
- CSV export of student lists

The web portal is meant for structured access to the attendance data collected and managed by the system.

---

## Key Features

### 1. AI-Powered Attendance
The project uses a recognition engine with live camera input to identify students and mark attendance automatically. Attendance is not written continuously without control. Instead, it respects classroom slots and updates attendance periodically.

### 2. Slot-Based Attendance Logic
Attendance is only active during defined classroom slots. If the current time is outside the slot range, recognition is disabled for attendance marking.

### 3. Multi-Classroom Monitoring
The desktop dashboard can load multiple classroom camera widgets and manage them together. Classrooms are loaded one by one to avoid high system load.

### 4. Student Enrollment with Image Support
Students can be added with details such as name, PRN, email, password, and image. This image is used in the recognition workflow.

### 5. Role-Based Access
The web application supports separate flows for:
- HOD / Principal
- Teacher
- Student

Each role gets different dashboard access and actions.

### 6. Attendance Dashboard
Students can view:
- present count
- absent count
- pending count
- attendance percentage
- date-wise attendance slots
- attendance chart

Teachers and HODs can also open student attendance dashboards for review.

### 7. Invite-Based Joining
Teachers and students can join through invite routes, making onboarding more structured for institutions.

### 8. CSV Export
Classroom student data can be exported as CSV for reporting or record keeping.

---

## How the System Works

### Desktop Workflow

The desktop side is responsible for live attendance marking.

Typical flow:

1. A classroom is created with:
   - classroom name
   - camera source
   - slot timings

2. The application loads saved classrooms.

3. Each classroom camera feed is started.

4. During active slot timing:
   - the camera feed runs recognition
   - recognized student identities are collected
   - attendance is written to the database after fixed intervals

5. During inactive slot timing:
   - recognition for attendance is disabled
   - recognized student set is cleared

6. The user can open a classroom student window to:
   - view live frame updates
   - see recognized students
   - see unknown tracks
   - edit classroom details
   - add new students

---

### Web Workflow

The web side is responsible for management and reporting.

Typical flow:

#### HOD / Principal
- can sign up a college account
- can log in
- can access the main dashboard
- can view classrooms
- can manage staff
- can invite teachers

#### Teacher
- can log in using college-linked credentials
- can access the dashboard
- can open classrooms
- can view students in classroom-related pages

#### Student
- can log in with enrolled classroom details
- can access personal attendance dashboard
- can view attendance summaries and charts

---

## Authentication Flow

### Student Login
Students log in using:
- name
- email
- password
- college ID
- classroom ID

### Teacher Login
Teachers log in using:
- college ID
- teacher name
- email
- password

### HOD / Principal Login and Signup
HOD users can:
- create a new college account
- log in with college-linked credentials

---

## Attendance Dashboard Details

The student attendance dashboard includes:

- student name
- email
- PRN
- college ID
- classroom ID
- classroom name
- present slot count
- absent slot count
- pending slot count
- attendance percentage
- date-wise attendance table
- stacked attendance chart

This gives both a summary view and a detailed breakdown.

---

## Desktop Application Responsibilities

The desktop side handles the active attendance engine and classroom UI.

Its responsibilities include:

- managing live camera streams
- running face recognition logic
- checking if attendance slots are active
- collecting recognized students
- marking attendance in the database
- toggling classroom camera state
- showing classroom camera widgets
- loading saved classrooms
- monitoring system resources
- adding classrooms
- editing classroom data
- adding students and face data

---

## Web Application Responsibilities

The web side handles dashboards, user access, and attendance views.

Its responsibilities include:

- rendering login and signup pages
- handling role-based authentication
- managing HOD, teacher, and student access
- showing classroom dashboard pages
- showing staff management pages
- showing student attendance pages
- supporting invite-based teacher and student onboarding
- exporting classroom student data as CSV

---

## Technology Used

### Desktop Side
- Python
- PySide6
- OpenCV
- QThread-based worker logic
- YOLO model integration
- face recognition engine

### Web Side
- FastAPI
- Jinja2 templates
- HTML
- CSS
- JavaScript chart rendering

### Other
- Python backend business logic
- database-based attendance and classroom storage

---

## What Makes This Project Strong

AttendMate is stronger than a simple attendance app because it combines:

- AI and computer vision
- desktop and web integration
- role-based academic workflows
- student onboarding
- classroom scheduling
- attendance analytics
- export support

It is much closer to a real product prototype than a basic CRUD mini-project.

---

## Use Cases

This project can be useful for:

- colleges
- classrooms
- academic labs
- teacher-managed attendance systems
- institutions that want a smarter attendance workflow

---

## Current Strengths

- automated attendance marking
- slot-aware classroom recognition
- multi-role web portal
- attendance visualization
- classroom and staff management
- student invite flow
- student dashboard access
- export support

---

## Known Design Limitation

The web application currently stores logged-in user state using global dictionaries in memory. This works for local development or small demonstrations, but it is not ideal for production because multiple users can overwrite shared state.

A better future improvement would be:
- session middleware
- secure cookies
- token-based authentication
- production-safe user session handling

---

## Future Improvements

Possible next upgrades:

- proper session-based authentication
- stronger password security
- public deployment
- cloud database integration
- admin analytics dashboard
- better chart filtering
- attendance notifications
- downloadable reports beyond CSV
- improved mobile responsiveness
- better recognition confidence tracking
- audit logs for attendance updates

---

## Why AttendMate Matters

Manual attendance is repetitive, slow, and error-prone. AttendMate improves this by combining automated recognition with structured dashboards and management features.

It helps make attendance:

- faster
- smarter
- easier to monitor
- easier to manage
- more useful for reporting

---

## Resume-Friendly Project Description

### Short Version
Built an AI-powered attendance management system using face recognition and FastAPI, with a desktop application for automated attendance capture and a web dashboard for managing students, teachers, classrooms, and attendance records.

### Detailed Version
Developed a smart attendance management platform with two integrated modules: a PySide6-based desktop application that uses live camera input, slot-aware attendance logic, and face recognition for automated attendance marking, and a FastAPI-based web application that supports HOD, teacher, and student workflows including onboarding, classroom management, attendance dashboards, chart visualization, and CSV export.

---

## Final Note

AttendMate is a strong project that blends AI, desktop development, backend logic, and web-based management into one system. It can serve as a portfolio project, academic project, or a base for building a more production-ready attendance platform.

--- 

## 👨‍💻 **Author**

**Omkar Waghmare**  
Engineering in Computer Science | Aspiring Data Scientist