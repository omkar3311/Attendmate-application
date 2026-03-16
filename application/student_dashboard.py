from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QDialog, QLineEdit,
    QFileDialog, QMessageBox
)
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QObject, QThread, Signal
import cv2
import json

from database import (
    add_student_to_classroom,
    get_classroom_full_data_by_name,
    update_classroom,load_qss_file
)
from recognition import reload_known_faces


class EditClassroomDialog(QDialog):
    def __init__(self, classroom_data):
        super().__init__()

        self.classroom_data = classroom_data
        self.setWindowTitle("Edit Classroom")
        self.resize(450, 300)

        layout = QVBoxLayout()

        self.class_name_input = QLineEdit()
        self.class_name_input.setPlaceholderText("Enter classroom name")
        self.class_name_input.setText(classroom_data.get("classroom_name", ""))
        layout.addWidget(QLabel("Classroom Name"))
        layout.addWidget(self.class_name_input)

        self.camera_input = QLineEdit()
        self.camera_input.setPlaceholderText("Enter camera input")
        self.camera_input.setText(str(classroom_data.get("camera_input", "")))
        layout.addWidget(QLabel("Camera Input"))
        layout.addWidget(self.camera_input)

        self.slot_input = QLineEdit()
        self.slot_input.setPlaceholderText('Example: [{"start":"01:00","end":"02:00"}]')
        slot_value = classroom_data.get("slot", "")
        if isinstance(slot_value, list):
            self.slot_input.setText(json.dumps(slot_value))
        else:
            self.slot_input.setText(str(slot_value))
        layout.addWidget(QLabel("Slots JSON"))
        layout.addWidget(self.slot_input)

        self.save_btn = QPushButton("Update Classroom")
        self.save_btn.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def validate_and_accept(self):
        class_name = self.class_name_input.text().strip()
        camera_input = self.camera_input.text().strip()
        slot_text = self.slot_input.text().strip()

        if not class_name:
            QMessageBox.warning(self, "Missing Data", "Please enter classroom name.")
            return

        if not camera_input:
            QMessageBox.warning(self, "Missing Data", "Please enter camera input.")
            return

        if not slot_text:
            QMessageBox.warning(self, "Missing Data", "Please enter slots.")
            return

        try:
            parsed = json.loads(slot_text)
            if not isinstance(parsed, list):
                raise ValueError
        except Exception:
            QMessageBox.warning(self, "Invalid Data", "Slots must be valid JSON list.")
            return

        self.accept()

    def get_data(self):
        return {
            "classroom_name": self.class_name_input.text().strip(),
            "camera_input": self.camera_input.text().strip(),
            "slot": json.loads(self.slot_input.text().strip())
        }


class AddStudentDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add Student")
        self.resize(420, 280)
        self.image_path = ""

        layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter student name")
        layout.addWidget(self.name_input)

        self.prn_input = QLineEdit()
        self.prn_input.setPlaceholderText("Enter student PRN")
        layout.addWidget(self.prn_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter student email")
        layout.addWidget(self.email_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Enter student password")
        layout.addWidget(self.pass_input)

        self.image_label = QLabel("No image selected")
        self.image_label.setWordWrap(True)
        layout.addWidget(self.image_label)

        self.select_btn = QPushButton("Select Image")
        self.select_btn.clicked.connect(self.select_image)
        layout.addWidget(self.select_btn)

        self.ok_btn = QPushButton("Add Student")
        self.ok_btn.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.ok_btn)

        self.setLayout(layout)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Student Image",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )

        if file_path:
            self.image_path = file_path
            self.image_label.setText(file_path)

    def validate_and_accept(self):
        student_name = self.name_input.text().strip()
        prn = self.prn_input.text().strip()
        email = self.email_input.text().strip()
        password = self.pass_input.text().strip()

        if not student_name:
            QMessageBox.warning(self, "Missing Data", "Please enter student name.")
            return

        if not prn:
            QMessageBox.warning(self, "Missing Data", "Please enter student PRN.")
            return

        if not email:
            QMessageBox.warning(self, "Missing Data", "Please enter student email.")
            return

        if not password:
            QMessageBox.warning(self, "Missing Data", "Please enter student password.")
            return

        if not self.image_path:
            QMessageBox.warning(self, "Missing Data", "Please select a student image.")
            return

        self.accept()

    def get_data(self):
        return {
            "student_name": self.name_input.text().strip(),
            "prn": self.prn_input.text().strip(),
            "email": self.email_input.text().strip(),
            "image_path": self.image_path,
            "password": self.pass_input.text().strip(),
        }


class AddStudentWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, class_name, student_name, image_path, student_prn, password, student_email):
        super().__init__()
        self.class_name = class_name
        self.student_name = student_name
        self.image_path = image_path
        self.student_prn = student_prn
        self.password = password
        self.student_email = student_email

    def run(self):
        try:
            result = add_student_to_classroom(
                self.class_name,
                self.student_name,
                self.image_path,
                self.student_prn,
                self.password,
                self.student_email
            )

            if result:
                try:
                    reload_known_faces()
                except Exception as e:
                    print("Face reload warning:", e)

                self.finished.emit(result)
            else:
                self.error.emit("Failed to add student")

        except Exception as e:
            self.error.emit(str(e))


class Student(QWidget):
    def __init__(self, camera_source, class_name):
        super().__init__()

        load_qss_file(self, "student_dashboard.qss")
        self.camera_source = camera_source
        self.class_name = class_name

        self.setWindowTitle(f"Class {class_name}")
        self.resize(1000, 560)

        outer_layout = QVBoxLayout()

        self.navbar_title = QLabel("AttendMate")
        self.navbar_title.setObjectName("navbarTitle")
        self.navbar_title.setAlignment(Qt.AlignCenter)
        outer_layout.addWidget(self.navbar_title)

        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        self.camera_label = QLabel("Camera Feed")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setFixedSize(520, 360)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 2px solid #444;
                border-radius: 10px;
                background-color: #111;
                color: #bbb;
                font-size: 16px;
            }
        """)

        left_layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)

        self.edit_classroom_btn = QPushButton("Edit Classroom")
        self.edit_classroom_btn.setFixedHeight(42)
        self.edit_classroom_btn.clicked.connect(self.open_edit_classroom_dialog)
        left_layout.addWidget(self.edit_classroom_btn)

        self.add_student_btn = QPushButton("Add New Student")
        self.add_student_btn.setFixedHeight(42)
        self.add_student_btn.clicked.connect(self.open_add_student_dialog)
        left_layout.addWidget(self.add_student_btn)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.status_label)

        left_layout.addStretch()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Track ID", "PRN / Name"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #444;
                border-radius: 8px;
                gridline-color: #555;
                font-size: 14px;
            }
        """)

        main_layout.addLayout(left_layout, 2)
        main_layout.addWidget(self.table, 1)

        outer_layout.addLayout(main_layout)

        self.setLayout(outer_layout)

        self.present_students = {}
        self.unknown_tracks = {}

        self.add_student_thread = None
        self.add_student_worker = None

    def open_edit_classroom_dialog(self):
        classroom_data = get_classroom_full_data_by_name(self.class_name)

        if not classroom_data:
            QMessageBox.critical(self, "Error", "Failed to fetch classroom data")
            return

        dialog = EditClassroomDialog(classroom_data)

        if dialog.exec():
            data = dialog.get_data()

            result = update_classroom(
                classroom_data["id"],
                data["classroom_name"],
                data["camera_input"],
                data["slot"]
            )

            if result:
                self.class_name = data["classroom_name"]
                self.setWindowTitle(f"Class {self.class_name}")
                QMessageBox.information(self, "Success", "Classroom updated successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to update classroom")

    def open_add_student_dialog(self):
        dialog = AddStudentDialog()

        if not dialog.exec():
            return

        data = dialog.get_data()

        student_name = data["student_name"]
        student_prn = data["prn"]
        student_email = data["email"]
        image_path = data["image_path"]
        password = data["password"]

        self.add_student_btn.setEnabled(False)
        self.add_student_btn.setText("Adding...")
        self.status_label.setText("Uploading student and saving data...")

        self.add_student_thread = QThread()
        self.add_student_worker = AddStudentWorker(
            self.class_name,
            student_name,
            image_path,
            student_prn,
            password,
            student_email
        )

        self.add_student_worker.moveToThread(self.add_student_thread)

        self.add_student_thread.started.connect(self.add_student_worker.run)
        self.add_student_worker.finished.connect(self.on_add_student_success)
        self.add_student_worker.error.connect(self.on_add_student_error)

        self.add_student_worker.finished.connect(self.add_student_thread.quit)
        self.add_student_worker.error.connect(self.add_student_thread.quit)

        self.add_student_worker.finished.connect(self.add_student_worker.deleteLater)
        self.add_student_worker.error.connect(self.add_student_worker.deleteLater)
        self.add_student_thread.finished.connect(self.add_student_thread.deleteLater)

        self.add_student_thread.start()

    def on_add_student_success(self, result):
        self.add_student_btn.setEnabled(True)
        self.add_student_btn.setText("Add New Student")
        self.status_label.setText("")
        QMessageBox.information(self, "Success", "Student added successfully")

    def on_add_student_error(self, message):
        self.add_student_btn.setEnabled(True)
        self.add_student_btn.setText("Add New Student")
        self.status_label.setText("")
        QMessageBox.critical(self, "Error", message)

    def update_frame(self, frame):
        # frame coming from camera widget is already RGB in your current flow
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            h, w, ch = frame.shape
            bytes_per_line = ch * w

            img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(img).scaled(
                self.camera_label.width(),
                self.camera_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.camera_label.setPixmap(pixmap)

    def update_table(self, people):
        current_unknown = set()

        for track_id, name, l, t, r, b in people:
            if name:
                if name not in self.present_students:
                    self.present_students[name] = track_id
            else:
                self.unknown_tracks[track_id] = True
                current_unknown.add(track_id)

        for track_id in list(self.unknown_tracks.keys()):
            if track_id not in current_unknown:
                del self.unknown_tracks[track_id]

        rows = []

        for name, track_id in self.present_students.items():
            rows.append((track_id, name))

        for track_id in self.unknown_tracks.keys():
            rows.append((track_id, "Unknown"))

        self.table.setRowCount(len(rows))

        for row, (track_id, name) in enumerate(rows):
            self.table.setItem(row, 0, QTableWidgetItem(str(track_id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(name)))