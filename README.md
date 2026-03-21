# 🎓 AttendMate – AI-Powered Attendance System

AttendMate is a **full-stack attendance platform** that automates classroom attendance using **face recognition** and provides a **role-based academic management system** for HODs, teachers, and students.

It combines:

* 🖥️ Desktop Application → Real-time AI attendance engine
* 🌐 Web Application → Academic management & analytics

---

## 🚀 Key Highlights

* 🤖 AI-powered face recognition for automated attendance
* 🧠 Offline-first architecture with zero data loss
* 🔄 Smart sync engine using queued operations
* 🎥 Multi-camera processing with thread-safe execution
* 📊 Role-based dashboards (HOD, Teacher, Student)
* ⚡ Resource-aware system (CPU & RAM monitoring)

---

## 🧩 Engineering Challenges Solved

* Built **offline-first system** with sync queue to handle network failures
* Managed **multiple camera streams** using QThread without blocking UI
* Implemented **safe thread lifecycle management** to prevent crashes
* Designed **dynamic table system** for scalable classroom isolation
* Controlled **real-time attendance writes** to avoid duplication and overload

---

## 🏗️ Architecture Overview

```id="arch1"
[Camera] → [Recognition Engine] → [Local PostgreSQL]
                                ↓
                          [Sync Queue]
                                ↓
                           [Supabase]

[Desktop UI] ←→ [Local System]

[Web App] ←→ [Cloud Database]
```

---

## 🖥️ Desktop Application (Core Engine)

The desktop application is the **central execution layer** responsible for real-time attendance processing and system control.

### It handles:

* 🎥 Live camera integration (IP & local sources)
* 🧠 Face detection, tracking, and recognition in real time
* ⏱️ Slot-based activation of attendance logic
* 🧾 Automatic attendance marking at fixed intervals
* 🧵 Multi-classroom execution using QThreads (parallel processing)
* 📉 CPU & RAM-aware camera loading for system stability
* 🔄 Background workers for heavy tasks (student add, sync, deletion)
* 🧑‍🎓 Student enrollment with image-based recognition
* 🔁 Instant face data reload after student addition
* 👁️ Real-time UI tracking of recognized vs unknown individuals
* 🔐 Safe classroom deletion with thread shutdown + DB cleanup

### Data Handling

* Local PostgreSQL → primary database (offline-first)
* Sync Queue → tracks pending operations
* Supabase → cloud backup & synchronization

---

## 🌐 Web Application (Management Layer)

Provides structured access to attendance data and academic workflows.

### 👨‍💼 HOD / Admin

* College & classroom management
* Staff onboarding via invite system

### 👨‍🏫 Teacher

* Classroom access
* Student management

### 👨‍🎓 Student

* Attendance dashboard
* Performance tracking
* Date-wise attendance insights

---

## 📊 Attendance & Analytics

* Present / Absent / Pending tracking
* Attendance percentage calculation
* Slot-wise and date-wise breakdown
* Chart-based visualization
* CSV export for reporting

---

## ⚙️ Tech Stack

**Desktop**

* Python, PySide6
* OpenCV, YOLO
* Face Recognition Engine

**Web**

* FastAPI
* Jinja2 Templates
* HTML, CSS, JavaScript

**Database**

* PostgreSQL (local-first)
* Supabase (cloud sync)

---

## ⚠️ Current Limitations (Design Scope)

* Web authentication currently uses **in-memory state**, optimized for development/demo environments
* Security layer (sessions/JWT) is not yet production-hardened

👉 These are **intentional trade-offs** to prioritize core system architecture, real-time processing, and reliability.

---

## 🔮 Future Improvements

* Secure authentication (JWT / sessions)
* Public deployment (cloud infrastructure)
* Advanced analytics dashboard
* Notification system
* Recognition confidence optimization

---

## 💡 Why This Project Stands Out

AttendMate goes beyond a typical CRUD system by combining:

* AI + Computer Vision
* Desktop + Web integration
* Real-time multi-threaded processing
* Offline-first distributed architecture

👉 Built with **production-oriented system design thinking**

---

## 👨‍💻 Author

**Omkar Waghmare**
Engineering in Computer Science
Aspiring Data Scientist 
