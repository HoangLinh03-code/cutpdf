import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QPixmap, QIcon
from datetime import datetime

from config.credentials import Config
from ui.cut_pdf_widget import CutPdfWidget
from ui.convert_pdf_widget import ConvertPdfWidget
from ui.sidebar import Sidebar

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CutPDF - PDF Processing Tool")
        self.resize(1200, 800)
        
        # Initialize data
        self.generated_files = []
        self.default_prompt_file = os.path.join(os.path.dirname(__file__), "..", "prompt.txt")
        self.current_mode = 0
        
        # Setup credentials với error handling tốt hơn
        self.setup_credentials()
        
        # Init UI (sẽ hoạt động cả khi có hoặc không có credentials)
        self.init_ui()

    def setup_credentials(self):
        """Setup credentials với fallback options"""
        try:
            self.credentials = Config.get_google_credentials()
            self.project_id = Config.GOOGLE_PROJECT_ID
            
            if self.credentials and self.project_id:
                print(f"✅ Credentials loaded successfully from ENV!")
                self.update_status("✅ Credentials loaded", "success")
            else:
                self.update_status("⚠️ Check .env file", "warning")
                self.show_credential_warning()
                
        except Exception as e:
            print(f"❌ Lỗi credentials: {e}")
            self.credentials = None
            
        # Hiển thị cảnh báo nhưng vẫn cho phép ứng dụng chạy
        if not self.credentials:
            self.update_status("⚠️ AI features disabled - No credentials", "warning")
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
            "• Đặt file service_account.json trong thư mục config/\n"
            "• Hoặc liên hệ admin để được hỗ trợ\n\n"
            "Ứng dụng vẫn có thể sử dụng các tính năng khác."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def init_ui(self):
        """Khởi tạo giao diện chính với sidebar và status bar"""
        # Main layout chính
        main_layout = QVBoxLayout()
        
        # Content layout (horizontal)
        content_layout = QHBoxLayout()
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.mode_changed.connect(self.switch_mode)
        content_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_area = QStackedWidget()
        
        # Tạo các widget - pass credentials (có thể là None)
        self.cut_pdf_widget = CutPdfWidget(
            self.credentials, 
            self.project_id, 
            self.default_prompt_file
        )
        
        self.convert_pdf_widget = ConvertPdfWidget()
        
        # Connect signals từ widgets để update status
        self.connect_widget_signals()
        
        self.content_area.addWidget(self.cut_pdf_widget)
        self.content_area.addWidget(self.convert_pdf_widget)
        
        content_layout.addWidget(self.content_area)
        content_layout.setStretch(0, 0)  # Sidebar cố định
        content_layout.setStretch(1, 1)  # Content linh hoạt
        
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
                background-color: #f0f0f0;
                border-top: 1px solid #d0d0d0;
                padding: 3px;
            }
        """)
        
        # Layout cho status bar
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        # 1. Status icon và message
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)
        self.status_message = QLabel("Sẵn sàng")
        self.status_message.setFont(QFont("Arial", 9))
        
        # 2. Progress indicator (ẩn mặc định)
        self.status_progress = QProgressBar()
        self.status_progress.setFixedSize(150, 20)
        self.status_progress.setVisible(False)
        self.status_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        # 3. Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # 4. File counter
        self.file_counter = QLabel("Files: 0")
        self.file_counter.setFont(QFont("Arial", 9))
        self.file_counter.setStyleSheet("color: #666;")
        
        # 5. Memory usage
        self.memory_label = QLabel()
        self.memory_label.setFont(QFont("Arial", 9))
        self.memory_label.setStyleSheet("color: #666;")
        
        # 6. Connection status
        self.connection_status = QLabel()
        self.connection_status.setFixedSize(16, 16)
        self.update_connection_status()
        
        # 7. Current time
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Arial", 9))
        self.time_label.setStyleSheet("color: #666;")
        self.update_time()
        
        # Timer để update thông tin real-time
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_realtime_info)
        self.status_timer.start(2000)  # Update mỗi 2 giây
        
        # Thêm các component vào layout
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_message)
        status_layout.addWidget(self.status_progress)
        status_layout.addItem(spacer)
        status_layout.addWidget(self.file_counter)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.memory_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.connection_status)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.time_label)

    def connect_widget_signals(self):
        """Kết nối signals từ các widget để update status"""
        if hasattr(self.cut_pdf_widget, 'status_changed'):
            self.cut_pdf_widget.status_changed.connect(self.update_status)
        if hasattr(self.cut_pdf_widget, 'progress_changed'):
            self.cut_pdf_widget.progress_changed.connect(self.update_progress)
        if hasattr(self.cut_pdf_widget, 'file_count_changed'):
            self.cut_pdf_widget.file_count_changed.connect(self.update_file_count)
    
    def update_status(self, message, status_type="info"):
        """
        Update status message với icon tương ứng
        status_type: 'info', 'success', 'warning', 'error', 'processing'
        """
        if not hasattr(self, 'status_message'):
            return
            
        self.status_message.setText(message)
        
        # Set icon và màu sắc theo loại status
        if status_type == "success":
            self.set_status_icon("✅", "#4CAF50")
        elif status_type == "error":
            self.set_status_icon("❌", "#f44336")
        elif status_type == "warning":
            self.set_status_icon("⚠️", "#ff9800")
        elif status_type == "processing":
            self.set_status_icon("🔄", "#2196f3")
        else:  # info
            self.set_status_icon("ℹ️", "#666666")
    
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
            # Auto count từ generated_files
            count = len(self.generated_files)
        
        self.file_counter.setText(f"Files: {count}")
        
        # Thay đổi màu theo số lượng
        if count == 0:
            color = "#666"
        elif count < 10:
            color = "#4CAF50"
        else:
            color = "#ff9800"
            
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
            
            # Thay đổi màu theo mức sử dụng
            if memory_mb > 500:
                self.memory_label.setStyleSheet("color: #f44336; font-weight: bold;")
            elif memory_mb > 200:
                self.memory_label.setStyleSheet("color: #ff9800;")
            else:
                self.memory_label.setStyleSheet("color: #666;")
                
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
        self.update_file_count()
    
    def show_status_message(self, message, duration=3000, status_type="info"):
        """Hiển thị message tạm thời trong status bar"""
        original_message = self.status_message.text()
        original_style = self.status_message.styleSheet()
        
        # Hiển thị message mới
        self.update_status(message, status_type)
        
        # Sau duration milliseconds, trở về message cũ
        QTimer.singleShot(duration, lambda: self.restore_status(original_message, original_style))
    
    def restore_status(self, message, style):
        """Khôi phục status message ban đầu"""
        self.status_message.setText(message)
        self.status_message.setStyleSheet(style)

    def switch_mode(self, mode):
        """Chuyển đổi chế độ giữa Cut PDF và Convert PDF"""
        self.current_mode = mode
        self.content_area.setCurrentIndex(mode)
        
        if mode == 0:
            self.setWindowTitle("CutPDF - Cắt PDF bằng AI")
            self.update_status("Switched to Cut PDF mode", "info")
        else:
            self.setWindowTitle("CutPDF - Convert PDF")
            self.update_status("Switched to Convert PDF mode", "info")
    
    def closeEvent(self, event):
        """Handle khi đóng ứng dụng"""
        self.update_status("Closing application...", "warning")
        
        # Stop timer
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # Cleanup
        event.accept()