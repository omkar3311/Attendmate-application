import sys
import psutil
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QGridLayout,
    QDialog,
    QLineEdit,
    QHBoxLayout,
    QMessageBox,
    QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from camera import CameraWidget
from database import add_classroom, get_classrooms_by_college_id,load_qss_file,startup_sync
from PySide6.QtWidgets import QTimeEdit
from PySide6.QtCore import QTime
from PySide6.QtWidgets import QSizePolicy

class SlotRow(QWidget):
    def __init__(self, removable=False, remove_callback=None):
        super().__init__()

        self.remove_callback = remove_callback
        layout = QHBoxLayout()

        self.start_input = QLineEdit("00:00")
        self.start_input.setInputMask("99:99")
        self.start_input.setPlaceholderText("HH:MM")

        self.end_input = QLineEdit("00:00")
        self.end_input.setInputMask("99:99")
        self.end_input.setPlaceholderText("HH:MM")

        layout.addWidget(QLabel("Start:"))
        layout.addWidget(self.start_input)
        layout.addWidget(QLabel("End:"))
        layout.addWidget(self.end_input)

        if removable:
            remove_btn = QPushButton("-")
            remove_btn.setFixedWidth(35)
            remove_btn.clicked.connect(self.remove_self)
            layout.addWidget(remove_btn)

        self.setLayout(layout)

    def remove_self(self):
        if self.remove_callback:
            self.remove_callback(self)

    def get_slot_data(self):
        return {
            "start": self.start_input.text().strip(),
            "end": self.end_input.text().strip()
        }

class CameraInputDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add Classroom")
        self.slot_rows = []

        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("Camera Source (Index or IP):"))
        self.camera_input = QLineEdit()
        self.main_layout.addWidget(self.camera_input)

        self.main_layout.addWidget(QLabel("Classroom Name:"))
        self.classroom_name_input = QLineEdit()
        self.main_layout.addWidget(self.classroom_name_input)

        slot_header = QHBoxLayout()
        slot_header.addWidget(QLabel("Slots:"))

        self.add_slot_btn = QPushButton("+")
        self.add_slot_btn.setFixedWidth(35)
        self.add_slot_btn.clicked.connect(self.add_slot_row)
        slot_header.addWidget(self.add_slot_btn)

        self.main_layout.addLayout(slot_header)

        self.slots_layout = QVBoxLayout()
        self.main_layout.addLayout(self.slots_layout)

        self.add_slot_row(first=True)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        self.main_layout.addLayout(buttons)
        self.setLayout(self.main_layout)

        ok_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)

    def add_slot_row(self, first=False):
        row = SlotRow(removable=not first, remove_callback=self.remove_slot_row)
        self.slot_rows.append(row)
        self.slots_layout.addWidget(row)

    def remove_slot_row(self, row_widget):
        self.slot_rows.remove(row_widget)
        self.slots_layout.removeWidget(row_widget)
        row_widget.deleteLater()
    
    def validate_and_accept(self):
        cam_source = self.camera_input.text().strip()
        classroom_name = self.classroom_name_input.text().strip()

        if not cam_source or not classroom_name:
            QMessageBox.warning(self, "Error", "Camera source and classroom name are required.")
            return

        slots = []
        for row in self.slot_rows:
            slot = row.get_slot_data()
            if not slot["start"] or not slot["end"]:
                QMessageBox.warning(self, "Error", "All slot fields must be filled.")
                return
            slots.append(slot)

        self.accept()

    def get_data(self):
        slots = [row.get_slot_data() for row in self.slot_rows]
        return (
            self.camera_input.text().strip(),
            self.classroom_name_input.text().strip(),
            slots
        )
        
        
class Dashboard(QWidget):

    def __init__(self, user_data):
        super().__init__()
        load_qss_file(self, "main_dashboard.qss")
        startup_sync()
        self.user_data = user_data
        self.college_id = user_data["id"]
        self.user_name = user_data["creator"]

        self.setWindowTitle("AttendMate Dashboard")
        self.resize(1100, 700)

        self.camera_count = 0
        self.camera_widgets = []
        self.pending_classrooms = []

        outer_layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        outer_layout.addWidget(self.scroll_area)

        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        self.navbar_title = QLabel("AttendMate")
        self.navbar_title.setObjectName("navbarTitle")
        self.navbar_title.setAlignment(Qt.AlignCenter)
        
        self.main_layout.addWidget(self.navbar_title)
        self.main_layout.addStretch()
        
        self.name = QLabel(f"Welcome {self.user_name}")
        self.name.setObjectName("welcomeLabel")
        self.name.setMinimumHeight(45)  
        self.main_layout.addWidget(self.name)

        self.resource_layout = QHBoxLayout()
        self.resource_layout.setSpacing(15)

        self.cpu_label = QLabel("CPU Usage: 0%")
        self.ram_label = QLabel("RAM Usage: 0%")
        self.camera_label = QLabel("Running Classrooms: 0")
        self.status_label = QLabel("Status: Safe")

        self.cpu_label.setFixedHeight(25)
        self.ram_label.setFixedHeight(25)
        self.camera_label.setFixedHeight(25)
        self.status_label.setFixedHeight(25)

        self.resource_layout.addWidget(self.status_label)
        self.resource_layout.addWidget(self.cpu_label)
        self.resource_layout.addWidget(self.ram_label)
        self.resource_layout.addWidget(self.camera_label)
        self.resource_layout.addStretch()   

        self.main_layout.addLayout(self.resource_layout)

        self.grid_layout = QGridLayout()
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setRowStretch(0, 1)
        self.grid_layout.setRowStretch(1, 1)
        self.grid_layout.setRowStretch(2, 1)
        self.grid_layout.setRowStretch(3, 1)
        self.grid_layout.setSpacing(10)

        self.main_layout.addLayout(self.grid_layout, 1)

        self.setLayout(self.main_layout)

        self.add_button = QPushButton("Add Camera")
        self.add_button.setFixedSize(360, 200)
        self.add_button.clicked.connect(self.ask_camera)
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self.update_resources)
        self.resource_timer.start(1500)

        self.load_saved_classrooms()
        self.start_saved_cameras_one_by_one()

    def update_resources(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        self.cpu_label.setText(f"CPU Usage: {cpu}%")
        self.ram_label.setText(f"RAM Usage: {ram}%")
        self.camera_label.setText(f"Running Classrooms: {len(self.camera_widgets)}")

        if cpu > 85 or ram > 85:
            self.status_label.setText("Status: High Load")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        elif cpu > 70 or ram > 70:
            self.status_label.setText("Status: Moderate Load")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.status_label.setText("Status: Safe")
            self.status_label.setStyleSheet("color: lightgreen; font-weight: bold;")

    def load_saved_classrooms(self):
        classrooms = get_classrooms_by_college_id(self.college_id)
        self.pending_classrooms = classrooms if classrooms else []

    def start_saved_cameras_one_by_one(self):
        self.sequential_timer = QTimer()
        self.sequential_timer.timeout.connect(self.load_next_camera)
        self.sequential_timer.start(2000)

    def load_next_camera(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        if cpu > 85 or ram > 85:
            return

        if not self.pending_classrooms:
            self.sequential_timer.stop()
            self.place_add_button()
            return

        classroom = self.pending_classrooms.pop(0)
        cam_source = classroom["camera_input"]
        classroom_name = classroom["classroom_name"]
        slots = classroom.get("slot", [])

        if str(cam_source).isdigit():
            cam_source = int(cam_source)

        self.add_camera(cam_source, classroom_name, slots)

    def place_add_button(self):
        self.grid_layout.removeWidget(self.add_button)

        row = self.camera_count // 2
        col = self.camera_count % 2
        self.grid_layout.addWidget(self.add_button, row, col)

    def ask_camera(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        if cpu > 85 or ram > 85:
            self.cpu_label.setStyleSheet("color: red; font-weight: bold;")
            self.ram_label.setStyleSheet("color: red; font-weight: bold;")
            return

        dialog = CameraInputDialog()

        if dialog.exec():
            cam_source, classroom_name , slots = dialog.get_data()

            if not cam_source or not classroom_name:
                return

            saved_data = add_classroom(
                college_id=self.college_id,
                classroom_name=classroom_name,
                camera_input=cam_source,
                slots=slots
            )
            if not saved_data:
                return

            if cam_source.isdigit():
                cam_source = int(cam_source)

            self.add_camera(cam_source, classroom_name, slots)

    def add_camera(self, cam_source, classroom_name, slots):
        cam_widget = CameraWidget(cam_source, classroom_name, slots)
        cam_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        row = self.camera_count // 2
        col = self.camera_count % 2

        self.grid_layout.removeWidget(self.add_button)
        self.grid_layout.addWidget(cam_widget, row, col)

        self.camera_widgets.append(cam_widget)
        self.camera_count += 1

        self.place_add_button()


# app = QApplication(sys.argv)

# user_data = {
#     "id": 1,
#     "email": "omkar@gmail.com",
#     "creator": "omkar",
#     "username": "omkar"
# }
# window = Dashboard(user_data)
# window.show()

# app.exec()