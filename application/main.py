import sys
from PySide6.QtWidgets import QApplication
from login import LoginPage

app = QApplication(sys.argv)

with open("style.qss", "r") as f:
    app.setStyleSheet(f.read())

window = LoginPage()
window.show()

app.exec()