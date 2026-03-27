"""
Main Window - Cửa sổ chính với 4 modules: Cut PDF, Convert PDF, GenQues KHTN, GenQues KHXH
"""
import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont
from datetime import datetime

from config.credentials import Config
from ui.cut_pdf_widget import CutPdfWidget
from ui.convert_pdf_widget import ConvertPdfWidget
from ui.genques_khtn_widget import GenQuesKHTNWidget
from ui.genques_khxh_widget import GenQuesKHXHWidget
from ui.sidebar import Sidebar
from ui.compress_pdf_widget import CompressPdfWidget
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CutPDF - Multi-Tool Platform")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 800)
        
        # Initialize data
        self.generated_files = []
        self.default_prompt_file = os.path.join(os.path.dirname(__file__), "..", "prompt.txt")
        self.current_mode = 0
        
        # Setup credentials với error handling
        self.setup_credentials()
        
        # Init UI
        self.init_ui()

    def setup_credentials(self):
        """Setup credentials với fallback options"""
        try:
            self.credentials = Config.get_google_credentials()
            self.project_id = Config.GOOGLE_PROJECT_ID
            
            if self.credentials and self.project_id:
                print(f"✅ Credentials loaded successfully!")
                self.update_status("✅ Credentials loaded", "success")
            else:
                self.update_status("⚠️ Check .env file", "warning")
                self.show_credential_warning()
                
        except Exception as e:
            print(f"❌ Lỗi credentials: {e}")
            self.credentials = None
            self.update_status("⚠️ AI features disabled", "warning")
            self.show_credential_warning()

    def show_credential_warning(self):
        """Hiển thị cảnh báo credentials nhưng không dừng app"""
        msg = QMessageBox()
        msg.setWindowTitle("Cảnh báo Credentials")
        msg.setIcon(QMessageBox.Warning)
        msg.setText("⚠️ Không thể tải thông tin xác thực Google Cloud!")
        msg.setInformativeText(
            "Một số tính năng AI sẽ bị vô hiệu hóa.\n\n"
            "Để khắc phục:\n"
            "• Kiểm tra file .env.gen trong thư mục gốc\n"
            "• Hoặc liên hệ admin để được hỗ trợ\n\n"
            "Ứng dụng vẫn có thể sử dụng các tính năng khác."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def init_ui(self):
        import uuid
        """Khởi tạo giao diện chính với sidebar và status bar"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content layout (horizontal)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.mode_changed.connect(self.switch_mode)
        content_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_area = QStackedWidget()
        
       
        # self.stacked_widget.addWidget(self.compress_pdf_widget) 

        # Tạo các widget
        self.cut_pdf_widget = CutPdfWidget(
            self.credentials, 
            self.project_id, 
            self.default_prompt_file
        )
        self.compress_pdf_widget = CompressPdfWidget()
        
        self.convert_pdf_widget = ConvertPdfWidget()
        
        # --- THÊM 2 WIDGET MỚI ---
        self.genques_khtn_widget = GenQuesKHTNWidget()
        self.genques_khxh_widget = GenQuesKHXHWidget()
        # -------------------------
        # self.chuyen_dang_widget = DocxProcessWidget(self, str(uuid.uuid4()))
        
        # Connect signals từ widgets để update status
        self.connect_widget_signals()
        
        # Add widgets to stack
        self.content_area.addWidget(self.cut_pdf_widget)         # Index 0
        self.content_area.addWidget(self.compress_pdf_widget)    # Index 1
        self.content_area.addWidget(self.convert_pdf_widget)     # Index 2
        self.content_area.addWidget(self.genques_khtn_widget)    # Index 3
        self.content_area.addWidget(self.genques_khxh_widget)    # Index 4
        # self.content_area.addWidget(self.chuyen_dang_widget)
        
        content_layout.addWidget(self.content_area)
        
        # Tạo status bar
        self.create_status_bar()
        
        # Thêm vào main layout
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        self.switch_mode(0)
    
    def create_status_bar(self):
        """Tạo thanh trạng thái phía dưới"""
        self.status_bar = QFrame()
        self.status_bar.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.status_bar.setFixedHeight(35)
        self.status_bar.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-top: 1px solid #2c3e50;
                padding: 3px;
            }
        """)
        
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        # 1. Status icon và message
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)
        self.status_message = QLabel("Sẵn sàng")
        self.status_message.setFont(QFont("Arial", 9))
        self.status_message.setStyleSheet("color: #ecf0f1;")
        
        # 2. Progress indicator
        self.status_progress = QProgressBar()
        self.status_progress.setFixedSize(150, 20)
        self.status_progress.setVisible(False)
        self.status_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2c3e50;
                border-radius: 3px;
                text-align: center;
                color: white;
                background-color: #2c3e50;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        
        # 3. Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # 4. File counter
        self.file_counter = QLabel("Files: 0")
        self.file_counter.setFont(QFont("Arial", 9))
        self.file_counter.setStyleSheet("color: #bdc3c7;")
        
        # 5. Memory usage
        self.memory_label = QLabel()
        self.memory_label.setFont(QFont("Arial", 9))
        self.memory_label.setStyleSheet("color: #bdc3c7;")
        
        # 6. Connection status
        self.connection_status = QLabel()
        self.connection_status.setFixedSize(16, 16)
        self.update_connection_status()
        
        # 7. Current time
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Arial", 9))
        self.time_label.setStyleSheet("color: #bdc3c7;")
        self.update_time()
        
        # Timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_realtime_info)
        self.status_timer.start(2000)
        
        # Add to layout
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_message)
        status_layout.addWidget(self.status_progress)
        status_layout.addItem(spacer)
        status_layout.addWidget(self.file_counter)
        status_layout.addWidget(QLabel("|", styleSheet="color: #7f8c8d;"))
        status_layout.addWidget(self.memory_label)
        status_layout.addWidget(QLabel("|", styleSheet="color: #7f8c8d;"))
        status_layout.addWidget(self.connection_status)
        status_layout.addWidget(QLabel("|", styleSheet="color: #7f8c8d;"))
        status_layout.addWidget(self.time_label)

    def connect_widget_signals(self):
        """Kết nối signals từ các widget để update status"""
        widgets = [
            self.cut_pdf_widget,
            self.compress_pdf_widget,
            self.convert_pdf_widget,
            self.genques_khtn_widget,
            self.genques_khxh_widget
        ]
        
        for widget in widgets:
            if hasattr(widget, 'status_changed'):
                widget.status_changed.connect(self.update_status)
            if hasattr(widget, 'progress_changed'):
                widget.progress_changed.connect(self.update_progress)
            if hasattr(widget, 'file_count_changed'):
                widget.file_count_changed.connect(self.update_file_count)
    
    def update_status(self, message, status_type="info"):
        """Update status message với icon tương ứng"""
        if not hasattr(self, 'status_message'):
            return
            
        self.status_message.setText(message)
        
        if status_type == "success":
            self.set_status_icon("✅", "#2ecc71")
        elif status_type == "error":
            self.set_status_icon("❌", "#e74c3c")
        elif status_type == "warning":
            self.set_status_icon("⚠️", "#f39c12")
        elif status_type == "processing":
            self.set_status_icon("🔄", "#3498db")
        else:
            self.set_status_icon("ℹ️", "#ecf0f1")
    
    def set_status_icon(self, emoji, color):
        """Set icon và màu cho status"""
        self.status_icon.setText(emoji)
        self.status_message.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def update_progress(self, value, visible=True):
        """Update progress bar"""
        if not hasattr(self, 'status_progress'):
            return
            
        self.status_progress.setValue(value)
        self.status_progress.setVisible(visible)
        
        if not visible:
            self.status_progress.setValue(0)
    
    def update_file_count(self, count=None):
        """Update file counter"""
        if not hasattr(self, 'file_counter'):
            return
            
        if count is None:
            count = len(self.generated_files)
        
        self.file_counter.setText(f"Files: {count}")
        
        if count == 0:
            color = "#bdc3c7"
        elif count < 10:
            color = "#2ecc71"
        else:
            color = "#f39c12"
            
        self.file_counter.setStyleSheet(f"color: {color};")
    
    def update_connection_status(self):
        """Update connection status icon"""
        if not hasattr(self, 'connection_status'):
            return
            
        if self.credentials:
            self.connection_status.setText("🟢")
            self.connection_status.setToolTip("Connected to Google Cloud")
        else:
            self.connection_status.setText("🔴")
            self.connection_status.setToolTip("No Google Cloud connection")
    
    def update_memory_usage(self):
        """Update memory usage display"""
        if not hasattr(self, 'memory_label'):
            return
            
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"RAM: {memory_mb:.1f}MB")
            
            if memory_mb > 500:
                self.memory_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            elif memory_mb > 200:
                self.memory_label.setStyleSheet("color: #f39c12;")
            else:
                self.memory_label.setStyleSheet("color: #bdc3c7;")
                
        except ImportError:
            self.memory_label.setText("RAM: N/A")
        except Exception:
            self.memory_label.setText("RAM: Error")
    
    def update_time(self):
        """Update current time display"""
        if not hasattr(self, 'time_label'):
            return
            
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)
    
    def update_realtime_info(self):
        """Update các thông tin real-time"""
        self.update_time()
        self.update_memory_usage()

    def switch_mode(self, mode):
        # if mode == 4: # Mode Chuyển Dạng
        #     if not hasattr(self, 'chuyen_dang_widget'):
        #         # Thiết lập môi trường riêng trước khi nạp module
        #         setup_chuyen_dang_env()
                
        #         # Import muộn (Lazy Import) để tiết kiệm tài nguyên
        #         from multi_process_threads.process_docx_Widget import DocxProcessWidget
        #         import uuid
                
        #         self.chuyen_dang_widget = DocxProcessWidget(self, str(uuid.uuid4()))
        #         self.content_area.addWidget(self.chuyen_dang_widget)
                
        #         # Quay lại thư mục gốc của CutPDF sau khi khởi tạo để không hỏng các module khác
        #         os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        """Chuyển đổi chế độ giữa 4 modules"""
        self.current_mode = mode
        self.content_area.setCurrentIndex(mode)
        
        titles = [
            "CutPDF - Cắt PDF bằng AI",
            "CutPDF - Nén PDF",
            "CutPDF - Convert PDF",
            "CutPDF - Sinh Câu Hỏi KHTN",
            "CutPDF - Sinh Câu Hỏi KHXH"
        ]
        
        messages = [
            "Switched to Cut PDF mode",
            "Switched to Compress PDF mode",
            "Switched to Convert PDF mode",
            "Switched to GenQues KHTN mode",
            "Switched to GenQues KHXH mode"
        ]
        
        self.setWindowTitle(titles[mode])
        self.update_status(messages[mode], "info")
    
    def closeEvent(self, event):
        """Handle khi đóng ứng dụng"""
        self.update_status("Closing application...", "warning")
        
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        event.accept()