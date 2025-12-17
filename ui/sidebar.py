from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont

class Sidebar(QWidget):
    mode_changed = pyqtSignal(int)  # Emit mode index when changed
    
    def __init__(self):
        super().__init__()
        self.current_mode = 0
        self.init_ui()
    
    def init_ui(self):
        self.setFixedWidth(200)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-right: 2px solid #d0d0d0;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Logo/Title
        title_label = QLabel("CutPDF Tool")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #2c3e50;
                color: white;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Menu buttons
        self.cut_pdf_btn = QPushButton("✂️ Cắt PDF")
        self.cut_pdf_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.cut_pdf_btn.setFixedHeight(50)
        self.cut_pdf_btn.clicked.connect(lambda: self.switch_to_mode(0))
        
        self.convert_pdf_btn = QPushButton("🔄 Convert PDF")
        self.convert_pdf_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.convert_pdf_btn.setFixedHeight(50)
        self.convert_pdf_btn.clicked.connect(lambda: self.switch_to_mode(1))
        
        # Style cho menu buttons
        self.normal_button_style = """
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
                margin: 2px;
                background-color: #ecf0f1;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
        """
        
        self.active_button_style = """
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
                margin: 2px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        
        layout.addWidget(self.cut_pdf_btn)
        layout.addWidget(self.convert_pdf_btn)
        
        # Spacer
        layout.addStretch()
        
        # Version info
        version_label = QLabel("v2.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #7f8c8d; font-size: 10px; padding: 10px;")
        layout.addWidget(version_label)
        
        self.setLayout(layout)
        
        # Set initial state
        self.update_button_styles()
    
    def switch_to_mode(self, mode):
        """Chuyển đổi chế độ"""
        if mode != self.current_mode:
            self.current_mode = mode
            self.update_button_styles()
            self.mode_changed.emit(mode)
    
    def update_button_styles(self):
        """Cập nhật style cho buttons dựa trên mode hiện tại"""
        if self.current_mode == 0:  # Cut PDF active
            self.cut_pdf_btn.setStyleSheet(self.active_button_style)
            self.convert_pdf_btn.setStyleSheet(self.normal_button_style)
        else:  # Convert PDF active
            self.convert_pdf_btn.setStyleSheet(self.active_button_style)
            self.cut_pdf_btn.setStyleSheet(self.normal_button_style)