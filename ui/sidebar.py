"""
Sidebar - Thanh điều hướng chính với 4 modules
"""
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
        self.setFixedWidth(220)
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo/Title
        title_label = QLabel("CutPDF Tool")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                background-color: #1a252f;
                color: white;
                border-bottom: 3px solid #3498db;
            }
        """)
        layout.addWidget(title_label)
        
        # Spacer nhỏ
        layout.addSpacing(15)
        
        # Menu buttons
        self.cut_pdf_btn = self.create_menu_button("✂️ Cắt PDF")
        self.cut_pdf_btn.clicked.connect(lambda: self.switch_to_mode(0))
        
        self.convert_pdf_btn = self.create_menu_button("🔄 Convert PDF")
        self.convert_pdf_btn.clicked.connect(lambda: self.switch_to_mode(1))
        
        # --- THÊM 2 NÚT MỚI ---
        self.genques_khtn_btn = self.create_menu_button("🧪 GenQues KHTN")
        self.genques_khtn_btn.clicked.connect(lambda: self.switch_to_mode(2))
        
        self.genques_khxh_btn = self.create_menu_button("🏛️ GenQues KHXH")
        self.genques_khxh_btn.clicked.connect(lambda: self.switch_to_mode(3))
        # self.chuyen_dang_btn = self.create_menu_button("🔄 Chuyển Dạng CH")
        # self.chuyen_dang_btn.clicked.connect(lambda: self.switch_to_mode(4))
        # ------------------------
        
        layout.addWidget(self.cut_pdf_btn)
        layout.addWidget(self.convert_pdf_btn)
        layout.addWidget(self.genques_khtn_btn)
        layout.addWidget(self.genques_khxh_btn)
        # layout.addWidget(self.chuyen_dang_btn)
        
        # Spacer to push version to bottom
        layout.addStretch()
        
        # Version info
        version_label = QLabel("v2.5")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                color: #95a5a6; 
                font-size: 10px; 
                padding: 15px;
                background-color: #1a252f;
            }
        """)
        layout.addWidget(version_label)
        
        self.setLayout(layout)
        
        # Store buttons for easy access
        self.buttons = [
            self.cut_pdf_btn,
            self.convert_pdf_btn,
            self.genques_khtn_btn,
            self.genques_khxh_btn
            # self.chuyen_dang_btn
        ]
        
        # Set initial state
        self.update_button_styles()
    
    def create_menu_button(self, text):
        """Tạo menu button với style thống nhất"""
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 11, QFont.Bold))
        btn.setFixedHeight(55)
        return btn
    
    def switch_to_mode(self, mode):
        """Chuyển đổi chế độ"""
        if mode != self.current_mode:
            self.current_mode = mode
            self.update_button_styles()
            self.mode_changed.emit(mode)
    
    def update_button_styles(self):
        """Cập nhật style cho buttons dựa trên mode hiện tại"""
        normal_style = """
            QPushButton {
                text-align: left;
                padding: 15px 20px;
                border: none;
                border-left: 4px solid transparent;
                background-color: transparent;
                color: #bdc3c7;
            }
            QPushButton:hover {
                background-color: #34495e;
                color: white;
                border-left: 4px solid #3498db;
            }
        """
        
        active_style = """
            QPushButton {
                text-align: left;
                padding: 15px 20px;
                border: none;
                border-left: 4px solid #3498db;
                background-color: #34495e;
                color: white;
                font-weight: bold;
            }
        """
        
        for i, btn in enumerate(self.buttons):
            if i == self.current_mode:
                btn.setStyleSheet(active_style)
            else:
                btn.setStyleSheet(normal_style)