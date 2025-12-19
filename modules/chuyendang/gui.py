import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
    QFileDialog, QMessageBox, QGroupBox, QScrollArea, QFrame,QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QIntValidator, QTextCharFormat, QTextCursor

import multiprocessing
import uuid
from modules.chuyendang.multi_process_threads.process_docx_Widget import DocxProcessWidget


# Lớp chính cho GUI
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Re-Answers Edmicro - Multi Process")
        self.resize(1200, 800)
        self.resources_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
        self.setWindowIcon(QIcon(os.path.join(self.resources_directory, "app_icon.png")))

        self.prompt_template_excel_path = os.path.join(self.resources_directory, "prompt_template.xlsx")
        self.config_json_file_path = os.path.join(self.resources_directory, "config.json")
        self.gemini_model_name = "gemini-2.5-pro"

        self.docx_widgets = []
        
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Chuyển Đổi Câu Hỏi AI")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        add_button = QPushButton("+ Thêm file DOCX")
        add_button.setStyleSheet("QPushButton { background-color: #2F80ED; color: white; padding: 8px; font-size: 12pt; }")
        add_button.clicked.connect(self.add_docx_widget)
        header_layout.addWidget(add_button)
        
        main_layout.addLayout(header_layout)

        # Scroll area cho các widget
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.scroll_layout = QHBoxLayout(scroll_widget)
        self.scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Tự động thêm một widget đầu tiên
        self.add_docx_widget()

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font: bold 11pt "Arial";
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding: 5px;
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                font-size: 10pt;
            }
            QComboBox {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                font-size: 10pt;
            }
            QPushButton {
                padding: 6px;
                font-size: 10pt;
                background-color: #2F80ED;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                padding: 4px;
            }
            QLabel {
                font-size: 10pt;
            }
            QFrame {
                background-color: white;
                margin: 5px;
                padding: 5px;
            }
        """)

    def add_docx_widget(self):
        process_id = str(uuid.uuid4())
        widget = DocxProcessWidget(self, process_id)
        widget.setFixedWidth(600)
        self.docx_widgets.append(widget)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
        
        # Thêm vào layout (trước stretch)
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, widget)

    def remove_docx_widget(self, widget):
        if widget in self.docx_widgets:
            widget.cleanup()
            self.docx_widgets.remove(widget)
            self.scroll_layout.removeWidget(widget)
            widget.deleteLater()

    def closeEvent(self, event):
        # Dọn dẹp tất cả các widget
        for widget in self.docx_widgets[:]:  # Copy list để tránh thay đổi trong vòng lặp
            widget.cleanup()
        
        event.accept()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)  # Đảm bảo tương thích đa nền tảng
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())