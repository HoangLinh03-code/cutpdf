import os
import uuid
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QSizePolicy
)
from PyQt5.QtGui import QFont

# Import widget gốc từ dự án chuyển dạng - KHÔNG ĐỔI CODE
from multi_process_threads.process_docx_Widget import DocxProcessWidget

class ChuyenDangModule(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window # Main Window của CutPDF
        self.docx_widgets = []
        self.setup_ui()

    def setup_ui(self):
        # Copy y hệt logic UI từ gui.py nhưng chỉnh sửa cho phù hợp QWidget
        main_layout = QVBoxLayout(self)

        # Header: Tiêu đề và nút Thêm file
        header_layout = QHBoxLayout()
        title_label = QLabel("Chuyển Đổi Câu Hỏi AI (Multi-Process)")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        add_button = QPushButton("+ Thêm file DOCX")
        add_button.setStyleSheet("QPushButton { background-color: #2F80ED; color: white; padding: 10px; font-size: 12pt; }")
        add_button.clicked.connect(self.add_docx_widget)
        header_layout.addWidget(add_button)
        
        main_layout.addLayout(header_layout)

        # Scroll area: Khu vực chứa các tiến trình chạy song song
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.scroll_layout = QHBoxLayout(scroll_widget) # Dàn hàng ngang như gui.py
        self.scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Tự động thêm một widget đầu tiên khi khởi tạo
        self.add_docx_widget()

    def add_docx_widget(self):
        # Khởi tạo DocxProcessWidget từ code gốc
        process_id = str(uuid.uuid4())
        widget = DocxProcessWidget(self, process_id)
        widget.setFixedWidth(600)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
        
        self.docx_widgets.append(widget)
        # Chèn vào trước Stretch cuối cùng
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, widget)

    def remove_docx_widget(self, widget):
        if widget in self.docx_widgets:
            widget.cleanup() # Đảm bảo dừng tiến trình con
            self.docx_widgets.remove(widget)
            self.scroll_layout.removeWidget(widget)
            widget.deleteLater()

    def cleanup_all(self):
        """Hàm dọn dẹp khi đóng App hoặc chuyển Module"""
        for widget in self.docx_widgets[:]:
            widget.cleanup()