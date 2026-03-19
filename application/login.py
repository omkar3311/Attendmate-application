from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QFrame,
    QCompleter,QDialog
    
)
from PySide6.QtCore import Qt
from PySide6.QtCore import QThread, Signal
from main_dashboard import Dashboard
from database import check_college_login, get_college_names,startup_sync

class LoadingDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Please wait")
        self.setFixedSize(300, 100)

        layout = QVBoxLayout(self)

        self.label = QLabel("Setting up your classrooms...")
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)

class SyncWorker(QThread):
    finished = Signal()

    def run(self):
        startup_sync()   
        self.finished.emit()
        
class LoginPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AttendMate Login")
        self.resize(600, 450)

        main_layout = QVBoxLayout()
        center_layout = QHBoxLayout()
        
        self.navbar_title = QLabel("AttendMate")
        self.navbar_title.setObjectName("navbarTitle")
        self.navbar_title.setAlignment(Qt.AlignCenter)
        
        self.card = QFrame()
        self.card.setObjectName("loginCard")
        self.card.setFixedWidth(320)

        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)

        self.label = QLabel("College Login")
        self.label.setObjectName("title")

        self.name = QLineEdit()
        self.name.setPlaceholderText("Enter Name")

        self.email = QLineEdit()
        self.email.setPlaceholderText("Enter Email")

        self.college_name = QLineEdit()
        self.college_name.setPlaceholderText("Enter College Name")
        college_names = get_college_names()
        self.completer = QCompleter(college_names)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.college_name.setCompleter(self.completer)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter Password")
        self.password.setEchoMode(QLineEdit.Password)

        self.button = QPushButton("Login")

        self.message = QLabel("")
        self.message.setObjectName("message")
        self.footer = QLabel("© 2025 AttendMate")
        self.footer.setObjectName("footer")
        self.footer.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(self.label)
        card_layout.addWidget(self.name)
        card_layout.addWidget(self.email)
        card_layout.addWidget(self.college_name)
        card_layout.addWidget(self.password)
        card_layout.addWidget(self.button)
        card_layout.addWidget(self.message)
        card_layout.addWidget(self.footer)

        self.card.setLayout(card_layout)

        center_layout.addStretch()
        center_layout.addWidget(self.card)
        center_layout.addStretch()

        main_layout.addWidget(self.navbar_title)
        main_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        self.button.clicked.connect(self.login_msg)

    def login_msg(self):
        name = self.name.text().strip()
        email = self.email.text().strip()
        college_name = self.college_name.text().strip()
        pwd = self.password.text().strip()

        if not name or not email or not college_name or not pwd:
            self.message.setStyleSheet("color: orange;")
            self.message.setText("Please fill all fields")
            return

        result = check_college_login(name, email, college_name, pwd)

        if result:
            self.message.setStyleSheet("color: lightgreen;")
            self.message.setText("Login successful")

            self.loading = LoadingDialog()

            self.worker = SyncWorker()

            def on_done():
                self.loading.accept()  

                self.dashboard = Dashboard(result)
                self.dashboard.show()
                self.close()

            self.worker.finished.connect(on_done)

            self.worker.start()
            self.loading.exec()
        else:
            self.message.setStyleSheet("color: red;")
            self.message.setText("User not found or invalid credentials")