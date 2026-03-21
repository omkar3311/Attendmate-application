# ⚙️ Installation Guide

This project contains two main parts:

* 🖥️ Desktop Application (AI Attendance Engine)
* 🌐 Web Application (Dashboard & Management)

Follow the steps below to set up both.

---

# 🖥️ Desktop Application Setup

## 📁 Navigate to Desktop App

```bash
cd application
```

---

## 🐍 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

---

## ⚠️ Fix OpenCV Conflict (IMPORTANT)

If OpenCV is already installed, remove it to avoid conflicts with PySide6:

```bash
pip uninstall opencv-python -y
pip uninstall opencv-python-headless -y
```

---

## 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ This project uses `opencv-python-headless`. Do NOT install `opencv-python`.

---

## 🗄️ Setup Database

Make sure:

* PostgreSQL is installed and running
* Database configuration is correctly set in `database.py`

---

## ▶️ Run Desktop Application

```bash
python main.py
```

---

## 📌 Notes

* Ensure your camera (webcam/IP camera) is accessible
* First run may take time due to model loading (`yolov8n.pt`)
* Multiple classrooms may increase CPU/RAM usage

---

# 🌐 Web Application Setup

## 📁 Navigate to Web App

```bash
cd website
```

---

## 🐍 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

---

## 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Setup Environment Variables

Create a `.env` file inside the `website/` folder:

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

---

## ▶️ Run Web Server

```bash
uvicorn main:app --reload
```

---

## 🌍 Access Web App

Open your browser:

```bash
http://127.0.0.1:8000
```

---

# 🔄 Recommended Workflow

1. Start the Desktop Application (handles attendance)
2. Start the Web Application (dashboard & monitoring)

---

# 🧱 Project Structure

```bash
AttendMate/
├── application/   # Desktop App
└── website/       # Web App
```

---

# ⚠️ Common Issues

### OpenCV Conflict / Crash

Solution:

```bash
pip uninstall opencv-python -y
pip uninstall opencv-python-headless -y
pip install -r requirements.txt
```

---

### Camera Not Working

Check:

* Camera permissions
* Correct camera source (IP/Webcam index)

---

### Supabase Not Syncing

Check:

* Internet connection
* `.env` credentials

---

# 🚀 You're Ready

You can now run:

* AI-based attendance system (desktop)
* Web dashboard for monitoring and management

---
