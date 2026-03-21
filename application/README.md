# 📌 AttendMate Desktop Application

AttendMate Desktop Application is the **core engine** of the system, responsible for real-time attendance tracking using AI-powered face recognition.

It is built with a **local-first architecture**, allowing the system to function even without an internet connection.

---

## 🚀 Overview

The desktop application handles:

- Live camera-based attendance
- Face recognition processing
- Classroom and student management
- Offline data storage with cloud sync

It performs all real-time operations while ensuring performance and reliability.

---

## ⚙️ Features

### 🎥 Real-Time Camera Processing
- Connect to IP cameras or local webcams
- Stream live video feeds
- Detect and track faces in real time
- Support multiple classroom camera feeds

---

### 🧠 AI-Based Face Recognition
- Recognizes students using stored image data
- Runs continuously on live frames
- Differentiates between recognized and unknown individuals

---

### 🕒 Slot-Based Attendance System
- Attendance is marked only during defined time slots
- Automatically disables recognition outside active slots
- Prevents invalid attendance entries

---

### 🧾 Automated Attendance Engine
- Collects recognized student identities
- Writes attendance at fixed intervals
- Prevents duplicate entries using constraints
- Supports slot-wise attendance tracking

---

## 🗄️ Database Architecture

### Local PostgreSQL
- Primary working database
- Stores classrooms, students, attendance, and sync queue
- Enables full offline functionality

### Cloud Sync (Supabase)
- Backup and synchronization layer
- Syncs data when internet is available

---

## 🔄 Smart Sync System

- Operations are stored in a local `sync_queue`
- Sync runs automatically when internet is available

### Sync Includes:
- Classroom data
- Student data
- Attendance records
- Image uploads

### Benefits:
- No data loss
- Smooth offline to online transition

---

## 🧩 Dynamic Table System

Each classroom dynamically creates:

- A student table
- An attendance table

### Advantages:
- Data isolation per classroom
- Scalable architecture
- Flexible schema design

---

## 🧵 Multi-Threaded Processing

- Each classroom runs in a separate `QThread`
- Prevents UI freezing
- Enables parallel camera streams
- Ensures safe thread shutdown

---

## ⚡ Background Task Handling

Heavy operations run in worker threads:

- Adding classrooms
- Adding students (with image processing)
- Deleting classrooms
- Syncing data

### Result:
- Smooth and responsive UI
- No blocking operations

---

## 🏫 Classroom Management

- Create classrooms with:
  - Name
  - Camera source
  - Time slots

- Edit classroom details
- Delete classrooms safely (with cleanup and thread shutdown)

---

## 👨‍🎓 Student Management

- Add students with:
  - Name
  - PRN
  - Email
  - Password
  - Image

- Image used for recognition
- Automatic face data reload after adding students
- Classroom-wise student isolation

---

## 📊 Real-Time Dashboard

- Live camera feed display
- Recognition ON/OFF status
- Recognized vs unknown tracking
- Camera toggle controls
- Instant classroom updates
- Smooth UI with signal-based updates

---

## 🧠 Resource-Aware Execution

The system monitors:

- CPU usage
- RAM usage

### Based on load:
- Delays new camera initialization
- Prevents system overload
- Maintains stable performance

---

## 🔐 Reliability Features

- Safe thread shutdown (prevents crashes)
- Exception handling in camera workers
- Offline-first operation
- Controlled sync retries
- Consistent UI and database state

---

## 🔄 Desktop Workflow

1. Create classroom (name, camera, slots)
2. Load saved classrooms
3. Start camera feeds
4. During active slots:
   - Run recognition
   - Collect student identities
   - Mark attendance
5. During inactive slots:
   - Disable attendance marking
   - Clear recognition data
6. Manage classrooms and students in real time

---

## 🧱 Project Structure

```bash
application/
├── camera.py
├── database.py
├── faces/
├── login.py
├── main_dashboard.py
├── main_dashboard.qss
├── main.py
├── recognition.py
├── student_dashboard.py
├── student_dashboard.qss
├── style.qss
└── yolov8n.pt
```


---

## 🛠️ Technologies Used

- Python
- PySide6 (GUI)
- OpenCV
- QThread (multi-threading)
- YOLO (object detection)
- Face Recognition Engine
- PostgreSQL

---

## 💡 Key Highlights

- Fully automated attendance system
- Works offline (local-first design)
- Multi-classroom support
- Real-time AI processing
- Scalable and modular architecture
- Smooth and responsive UI

---

## 🎯 Purpose

This application eliminates manual attendance by:

- Automating student recognition
- Reducing human error
- Saving time
- Providing accurate attendance tracking

---

## 👨‍💻 Author

**Omkar Waghmare**
Engineering in Computer Science
Aspiring Data Scientist .