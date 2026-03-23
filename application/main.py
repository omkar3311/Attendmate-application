import sys
from PySide6.QtWidgets import QApplication
from login import LoginPage
from main_dashboard import Dashboard
from database import is_login

app = QApplication(sys.argv)

login_status , user = is_login()
if login_status:
    window = Dashboard(user)
    window.show()
else:
    # with open("style.qss", "r") as f:
    #     app.setStyleSheet(f.read())

    window = LoginPage()
    window.show()

app.exec()