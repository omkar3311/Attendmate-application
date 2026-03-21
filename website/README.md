# 🌐 AttendMate Web Application  
### Role-Based Academic Management System

The **AttendMate Web Application** is the management layer of the AttendMate ecosystem. It provides a structured interface for **HODs, teachers, and students** to interact with attendance data, manage classrooms, and monitor academic performance.

Built using **FastAPI + Jinja2 templates**, the system connects to a **Supabase cloud database** for real-time data access and management.

---

## 🚀 Overview

The web application enables:

- Academic structure management (colleges, classrooms, users)  
- Role-based dashboards  
- Attendance tracking and analytics  
- Invite-based onboarding system  
- Centralized control over classroom data  

---

## 🎭 Role-Based Access System

### 👨‍🎓 Student
- Login using classroom credentials  
- Access personal attendance dashboard  
- View:
  - Present / Absent / Pending counts  
  - Attendance percentage  
  - Date-wise and slot-wise attendance  

---

### 👨‍🏫 Teacher
- Access assigned classrooms  
- Manage students  
- Add students with image upload  
- View classroom data  
- Export student list as CSV  

---

### 👨‍💼 HOD / Admin
- Create and manage colleges  
- Manage teachers  
- Access all classrooms  
- Generate invite links for teachers  

---

## 🔐 Authentication System

- Role-based login (Student / Teacher / HOD)  
- Secure password verification using **bcrypt hashing**  
- Credentials validated against database records  

---

## 🏫 Classroom & Data Structure

- Each classroom is associated with:
  - A **student table**
  - An **attendance table**
- Data is isolated per classroom for scalability  
- Table names are validated to ensure safe database queries  

---

## 📊 Attendance & Analytics

The system provides detailed attendance insights:

- ✅ Present / Absent / Pending tracking  
- 📅 Date-wise attendance records  
- ⏱️ Slot-based attendance breakdown  
- 📈 Attendance percentage calculation  
- 📊 Chart-based visualization  

---

## 🔗 Invite-Based Onboarding

### 👨‍🏫 Teacher Invite
- Unique invite link per college  
- Enables teacher registration  

### 👨‍🎓 Student Invite
- Classroom-specific invite link  
- Requires:
  - Name  
  - PRN  
  - Email  
  - Password  
  - Image upload  

---

## 🖼️ Student Image Handling

- Images uploaded during student registration  
- Stored in Supabase storage  
- Used for identification and future AI integration  

**Supported formats:**
- `.jpg`
- `.jpeg`
- `.png`

---

## 🌐 Frontend (Templates)

The UI is built using **Jinja2 templates** rendered via FastAPI.

### Key Templates:
- `new_home.html` → Authentication UI  
- `new_student.html` → Student dashboard  
- `main_dashboard.html` → Teacher/HOD dashboard  
- `class_dashboard.html` → Classroom management  
- `staff_dashboard.html` → Teacher management  
- `student_invite_login.html` → Student onboarding  
- `teacher_invite_login.html` → Teacher onboarding  

Templates dynamically receive backend data to render dashboards and analytics.

---

## 📁 Core Features

- Multi-role authentication system  
- Classroom and student management  
- Attendance analytics dashboard  
- CSV export functionality  
- Image upload integration  
- Invite-based onboarding  
- Dynamic database structure  

---

## 🔮 Future Improvements

- JWT / session-based authentication  
- Role-based access middleware  
- Deployment-ready architecture  
- Advanced analytics dashboard  
- Integration with AI attendance engine  

---

## 💡 Summary

The AttendMate Web Application delivers a structured and scalable academic management system with:

- Clean role-based access  
- Real-time attendance insights  
- Modular classroom architecture  
- Seamless integration with backend services  

It is designed with **production-oriented system thinking**, making it a strong foundation for building a complete intelligent attendance platform.

---
## 👨‍💻 Author

**Omkar Waghmare**
Engineering in Computer Science
Aspiring Data Scientist .