from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class NetworkTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Network Tab")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        network_info = QLabel("<< Network Controls >>")
        network_info.setAlignment(Qt.AlignCenter)
        network_info.setStyleSheet("background-color: lightgreen;")
        layout.addWidget(network_info)
