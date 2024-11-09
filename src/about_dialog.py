import os
import sys

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

from src.utils import get_resource_path

class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About")
        self.setFixedSize(400,200)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20,20,20,20)

        app_name = QLabel("Adjustment Rule Demystifier v1.1")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        app_name.setFont(font)
        app_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(app_name)

        description = QLabel (
            "A tool for demystifying and analysing adjustment rule and its triggers."
            "This application allows you to view, modify and update adjustment rules"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)

        built_by = QLabel(
            "Built with great dificulty by Omar K."
            " Send feedback to omar.khan@ukg.com"
        )
        built_by.setWordWrap(True)
        built_by.setAlignment(Qt.AlignCenter)
        layout.addWidget(built_by)

        logo_label = QLabel()
        logo_pixmap = QPixmap(get_resource_path("resources/images/ard.png"))
        logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.insertWidget(0, logo_label)  # Add at the top of the dial
        # og

        self.setLayout(layout)