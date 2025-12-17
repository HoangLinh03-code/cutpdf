import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFont

from process import ProcessingThread
from threads.auto_processor import AutoProcessor
from threads.local_processor import LocalProcessor
from core.client_driver import GoogleDriveAPI
from threads.batch_processing import BatchProcessingThread
from core.compress_manager import CompressThread

from PyQt5.QtCore import pyqtSignal

class CutPdfWidget(QWidget):
    # Định nghĩa signals
    status_changed = pyqtSignal(str, str)  # message, type
    progress_changed = pyqtSignal(int, bool)  # value, visible
    file_count_changed = pyqtSignal(int)  # count
    
    def __init__(self, credentials, project_id, default_prompt_file):
        super().__init__()
        self.credentials = credentials
        self.project_id = project_id
        self.default_prompt_file = default_prompt_file
        
        # Check if credentials are valid
        self.has_valid_credentials = credentials is not None and project_id is not None
        
        # Data storage
        self.downloaded_pdfs = []
        self.local_pdfs = []
        self.generated_files = []
        self.auto_processor = None
        self.local_processor = None
        self.batch_thread = None
        self.compress_thread = None
        self.thread = None
        
        self.init_ui()
        
        # Disable AI-related features if no credentials
        if not self.has_valid_credentials:
            self.disable_ai_features()

    def disable_ai_features(self):
        """Vô hiệu hóa các tính năng cần AI khi không có credentials"""
        # Disable AI-related buttons
        if hasattr(self, 'process_button'):
            self.process_button.setEnabled(False)
            self.process_button.setToolTip("❌ Cần credentials để sử dụng AI")
            
        if hasattr(self, 'process_all_button'):
            self.process_all_button.setEnabled(False)
            self.process_all_button.setToolTip("❌ Cần credentials để sử dụng AI")
            
        if hasattr(self, 'auto_process_button'):
            self.auto_process_button.setEnabled(False)
            self.auto_process_button.setToolTip("❌ Cần credentials để sử dụng AI")
            
        if hasattr(self, 'auto_process_local_button'):
            self.auto_process_local_button.setEnabled(False)
            self.auto_process_local_button.setToolTip("❌ Cần credentials để sử dụng AI")

    def init_ui(self):
        font = QFont("Arial", 10)
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("✂️ CẮT PDF BẰNG AI")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #e8f5e8;
                border: 2px solid #4caf50;
                border-radius: 8px;
                color: #2e7d32;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(header_label)
        
        # Google Drive section
        drive_group = self.create_drive_section()
        layout.addWidget(drive_group)
        
        # Local folder section
        local_group = self.create_local_section()
        layout.addWidget(local_group)
        
        # PDF list section
        list_group = self.create_list_section()
        layout.addWidget(list_group)
        
        # Manual processing section
        manual_group = self.create_manual_section()
        layout.addWidget(manual_group)
        
        # Progress section
        progress_group = self.create_progress_section()
        layout.addWidget(progress_group)
        
        # Results section
        results_group = self.create_results_section()
        layout.addWidget(results_group)
        
        # Compression section
        compress_group = self.create_compression_section()
        layout.addWidget(compress_group)
        
        self.setLayout(layout)
    
    def create_drive_section(self):
        """Tạo section Google Drive"""
        group = QGroupBox("📁 Tải từ Google Drive")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        layout = QVBoxLayout()
        
        self.drive_url_input = QLineEdit()
        self.drive_url_input.setPlaceholderText("Nhập link folder Google Drive chứa file PDF...")
        self.drive_url_input.setFixedHeight(35)
        
        buttons_layout = QHBoxLayout()
        self.download_button = QPushButton("📥 Tải PDF từ Drive")
        self.download_button.setFixedHeight(40)
        self.download_button.clicked.connect(self.download_from_drive)
        
        self.auto_process_button = QPushButton("🤖 Auto xử lý từ Drive")
        self.auto_process_button.setFixedHeight(40)
        self.auto_process_button.setStyleSheet("background-color: #e6ffe6; font-weight: bold;")
        self.auto_process_button.clicked.connect(self.start_auto_processing)
        
        buttons_layout.addWidget(self.download_button)
        buttons_layout.addWidget(self.auto_process_button)
        
        layout.addWidget(self.drive_url_input)
        layout.addLayout(buttons_layout)
        group.setLayout(layout)
        return group
    
    def create_local_section(self):
        """Tạo section Local folder"""
        group = QGroupBox("💻 Xử lý từ Folder Local")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        layout = QVBoxLayout()
        
        self.local_folder_input = QLineEdit()
        self.local_folder_input.setPlaceholderText("Đường dẫn folder chứa PDF...")
        self.local_folder_input.setFixedHeight(35)
        
        buttons_layout = QHBoxLayout()
        self.browse_folder_button = QPushButton("📂 Chọn Folder")
        self.browse_folder_button.clicked.connect(self.browse_local_folder)
        
        self.scan_folder_button = QPushButton("🔍 Quét PDF")
        self.scan_folder_button.clicked.connect(self.scan_local_folder)
        
        self.auto_process_local_button = QPushButton("🔄 Auto xử lý từ Local")
        self.auto_process_local_button.setFixedHeight(40)
        self.auto_process_local_button.setStyleSheet("background-color: #ffe6e6; font-weight: bold;")
        self.auto_process_local_button.clicked.connect(self.start_local_processing)
        
        buttons_layout.addWidget(self.browse_folder_button)
        buttons_layout.addWidget(self.scan_folder_button)
        
        layout.addWidget(self.local_folder_input)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.auto_process_local_button)
        group.setLayout(layout)
        return group
    
    def create_list_section(self):
        """Tạo section PDF list"""
        group = QGroupBox("📋 Danh sách PDF & Xử lý")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        layout = QVBoxLayout()
        
        self.pdf_list = QListWidget()
        self.pdf_list.setFixedHeight(120)
        self.pdf_list.itemClicked.connect(self.select_pdf_from_list)
        
        self.process_all_button = QPushButton("⚡ Xử lý tất cả PDF")
        self.process_all_button.setFixedHeight(40)
        self.process_all_button.setStyleSheet("background-color: #e6f3ff; font-weight: bold;")
        self.process_all_button.clicked.connect(self.process_all_files)
        self.process_all_button.setEnabled(False)
        
        layout.addWidget(self.pdf_list)
        layout.addWidget(self.process_all_button)
        group.setLayout(layout)
        return group
    
    def create_manual_section(self):
        """Tạo section manual processing"""
        group = QGroupBox("✋ Xử lý thủ công")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        layout = QVBoxLayout()
        
        # PDF selection
        self.pdf_label = QLabel("Chưa chọn file PDF")
        self.pdf_label.setFixedHeight(35)
        self.pdf_label.setStyleSheet("border: 1px solid gray; padding: 5px; background-color: white;")
        self.pdf_button = QPushButton("📄 Chọn PDF")
        self.pdf_button.clicked.connect(self.select_pdf)
        
        pdf_layout = QHBoxLayout()
        pdf_layout.addWidget(self.pdf_label, 3)
        pdf_layout.addWidget(self.pdf_button, 1)
        
        # Prompt selection
        self.prompt_label = QLabel("Chưa chọn file prompt")
        self.prompt_label.setFixedHeight(35)
        self.prompt_label.setStyleSheet("border: 1px solid gray; padding: 5px; background-color: white;")
        
        # Set default prompt
        if os.path.isfile(self.default_prompt_file):
            self.prompt_label.setText(self.default_prompt_file)
        else:
            self.prompt_label.setText("prompt.txt không tìm thấy")
            
        self.prompt_button = QPushButton("📝 Chọn Prompt")
        self.prompt_button.clicked.connect(self.select_prompt)
        self.edit_prompt_button = QPushButton("✏️ Sửa Prompt")
        self.edit_prompt_button.clicked.connect(self.edit_prompt)
        
        prompt_layout = QHBoxLayout()
        prompt_layout.addWidget(self.prompt_label, 2)
        prompt_layout.addWidget(self.prompt_button, 1)
        prompt_layout.addWidget(self.edit_prompt_button, 1)
        
        # Compression settings
        compress_layout = QVBoxLayout()
        self.compress_checkbox = QCheckBox("🗜️ Nén PDF sau khi cắt")
        self.compress_checkbox.setChecked(True)
        
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Chất lượng:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "screen (72dpi - Nhỏ nhất)",
            "ebook (150dpi - Vừa phải)", 
            "printer (300dpi - Chất lượng cao)",
            "prepress (300dpi - Tốt nhất)"
        ])
        self.quality_combo.setCurrentIndex(1)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        
        compress_layout.addWidget(self.compress_checkbox)
        compress_layout.addLayout(quality_layout)
        
        # Process button
        self.process_button = QPushButton("🚀 Bắt đầu xử lý")
        self.process_button.setFixedHeight(45)
        self.process_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.process_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px;")
        self.process_button.clicked.connect(self.process_files)
        
        layout.addLayout(pdf_layout)
        layout.addLayout(prompt_layout)
        layout.addLayout(compress_layout)
        layout.addWidget(self.process_button)
        group.setLayout(layout)
        return group
    
    def create_progress_section(self):
        """Tạo section progress"""
        group = QGroupBox("📊 Tiến trình")
        layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("Sẵn sàng")
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        group.setLayout(layout)
        return group
    
    def create_results_section(self):
        """Tạo section results"""
        group = QGroupBox("📁 Kết quả")
        layout = QVBoxLayout()
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.docx_viewer = QWebEngineView()
        self.docx_list = QListWidget()
        self.docx_list.setFixedWidth(250)
        self.docx_list.itemClicked.connect(self.open_file_from_list)
        
        splitter.addWidget(self.docx_viewer)
        splitter.addWidget(self.docx_list)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        group.setLayout(layout)
        return group
    
    def create_compression_section(self):
        """Tạo section compression tools"""
        group = QGroupBox("🗜️ Công cụ nén PDF")
        layout = QVBoxLayout()
        
        # Quality selection
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Chất lượng nén:")
        self.compress_quality_combo = QComboBox()
        self.compress_quality_combo.addItems([
            "screen (72dpi - Nén tối đa)",
            "ebook (150dpi - Cân bằng)", 
            "printer (300dpi - Chất lượng cao)",
            "prepress (300dpi - Tốt nhất)"
        ])
        self.compress_quality_combo.setCurrentIndex(1)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.compress_quality_combo)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.compress_selected_btn = QPushButton("🗜️ Nén file đã chọn")
        self.compress_selected_btn.setFixedHeight(35)
        self.compress_selected_btn.clicked.connect(self.compress_selected_file)
        
        self.compress_all_btn = QPushButton("🗜️ Nén tất cả PDF")
        self.compress_all_btn.setFixedHeight(35)
        self.compress_all_btn.clicked.connect(self.compress_all_files)
        
        self.compress_folder_btn = QPushButton("🗜️ Nén folder")
        self.compress_folder_btn.setFixedHeight(35)
        self.compress_folder_btn.clicked.connect(self.compress_folder)
        
        buttons_layout.addWidget(self.compress_selected_btn)
        buttons_layout.addWidget(self.compress_all_btn)
        buttons_layout.addWidget(self.compress_folder_btn)
        
        layout.addLayout(quality_layout)
        layout.addLayout(buttons_layout)
        group.setLayout(layout)
        return group
    
    # Event handlers and utility methods
    def get_compression_settings(self):
        """Lấy thiết lập nén từ UI"""
        compress_enabled = self.compress_checkbox.isChecked()
        quality_text = self.quality_combo.currentText()
        
        quality_map = {
            "screen": "screen",
            "ebook": "ebook", 
            "printer": "printer",
            "prepress": "prepress"
        }
        
        quality = "ebook"
        for key in quality_map:
            if key in quality_text:
                quality = quality_map[key]
                break
        
        return compress_enabled, quality
    
    def get_compress_quality_from_combo(self):
        """Lấy quality từ compression combo"""
        quality_text = self.compress_quality_combo.currentText()
        quality_map = {
            "screen": "screen",
            "ebook": "ebook", 
            "printer": "printer",
            "prepress": "prepress"
        }
        
        quality = "ebook"
        for key in quality_map:
            if key in quality_text:
                quality = quality_map[key]
                break
        return quality
    
    def select_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file PDF", "", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_label.setText(file_path)

    def select_prompt(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file prompt", "", "Text Files (*.txt)")
        if file_path:
            self.prompt_label.setText(file_path)

    def edit_prompt(self):
        prompt_path = self.prompt_label.text()
        if os.path.isfile(prompt_path):
            os.system(f'notepad "{prompt_path}"')
        else:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file prompt.txt trước.")
    
    def process_files(self):
        """Xử lý một file PDF đơn lẻ"""
        if not self.has_valid_credentials:
            QMessageBox.warning(
                self, 
                "Thiếu Credentials", 
                "❌ Không thể sử dụng tính năng AI.\n\n"
                "Cần file service_account.json trong thư mục config/ để sử dụng tính năng này."
            )
            return
            
        pdf_file = self.pdf_label.text()
        prompt_path = self.prompt_label.text()

        # Validate files with Unicode support
        if not pdf_file or pdf_file == "Chưa chọn file PDF":
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file PDF.")
            return
            
        if not prompt_path or prompt_path == "Chưa chọn file prompt":
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file prompt.txt.")
            return

        # Normalize paths
        try:
            pdf_file = self.normalize_file_path(pdf_file)
            prompt_path = self.normalize_file_path(prompt_path)
            
            # Check file accessibility
            if not self.is_file_accessible(pdf_file):
                QMessageBox.warning(
                    self, 
                    "Lỗi", 
                    f"Không thể truy cập file PDF:\n{pdf_file}\n\n"
                    f"Có thể do:\n"
                    f"• File không tồn tại\n"
                    f"• Không có quyền đọc\n"
                    f"• Tên file có ký tự đặc biệt"
                )
                return
                
            if not self.is_file_accessible(prompt_path):
                QMessageBox.warning(self, "Lỗi", f"Không thể truy cập file prompt:\n{prompt_path}")
                return
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Lỗi", 
                f"Lỗi xử lý đường dẫn file:\n{str(e)}\n\n"
                f"Vui lòng kiểm tra:\n"
                f"• Tên file không chứa ký tự đặc biệt\n"
                f"• Đường dẫn không quá dài\n"
                f"• File có thể truy cập được"
            )
            return

        # Cleanup old thread
        if hasattr(self, 'thread') and self.thread is not None:
            try:
                self.thread.quit()
                self.thread.wait()
            except Exception:
                pass
            self.thread = None

        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Đang xử lý...")

        self.thread = ProcessingThread(pdf_file, prompt_path, self.project_id, self.credentials)
        self.thread.progress.connect(self.update_status)
        self.thread.error.connect(self.show_error)
        self.thread.finished.connect(self.processing_finished)
        self.thread.start()
    
    def download_from_drive(self):
        """Tải PDF từ Google Drive"""
        drive_url = self.drive_url_input.text().strip()
        if not drive_url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập link Google Drive folder.")
            return
        
        # Tạo thư mục download
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        download_path = os.path.join(app_dir, "downloaded_pdfs")
        
        # Disable UI
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Đang tải từ Google Drive...")
        
        try:
            # Tạo GoogleDriveAPI client
            client_secrets_file = os.path.join(app_dir, 'client_secret_409523926306-7tu8v8tqs22mq812nv9tuktiapfct823.apps.googleusercontent.com.json')
            if not os.path.exists(client_secrets_file):
                raise FileNotFoundError("Không tìm thấy file client_secret.json")
                
            drive_api = GoogleDriveAPI(client_secrets_file)
            
            # Extract folder ID và download
            folder_id = drive_api.extract_folder_id(drive_url)
            drive_api.download_all_pdfs_with_structure(folder_id, download_path)
            
            # Collect downloaded files
            downloaded_files = []
            for root, dirs, files in os.walk(download_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        downloaded_files.append(os.path.join(root, file))
            
            if downloaded_files:
                self.downloaded_pdfs = downloaded_files
                self.update_pdf_list()
                self.process_all_button.setEnabled(True)
                self.status_label.setText(f"Đã tải {len(downloaded_files)} file PDF")
                QMessageBox.information(
                    self, 
                    "Thành công", 
                    f"Đã tải xuống {len(downloaded_files)} file PDF từ Google Drive"
                )
            else:
                self.status_label.setText("Không tìm thấy file PDF nào")
                QMessageBox.information(self, "Thông báo", "Không tìm thấy file PDF nào trong folder")
        
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải từ Google Drive: {str(e)}")
            self.status_label.setText("Lỗi khi tải từ Drive")
        
        finally:
            self._set_ui_enabled(True)
            self.progress_bar.setVisible(False)
    
    def browse_local_folder(self):
        """Chọn folder local chứa PDF"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn folder chứa file PDF")
        if folder:
            self.local_folder_input.setText(folder)

    def scan_local_folder(self):
        """Quét và liệt kê PDF trong folder local"""
        folder_path = self.local_folder_input.text().strip()
        if not folder_path or not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn folder hợp lệ.")
            return
        
        try:
            # Normalize folder path
            folder_path = os.path.normpath(folder_path)
            
            # Quét PDF recursively với Unicode support
            pdf_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        # Normalize path để tránh lỗi Unicode
                        normalized_path = os.path.normpath(file_path)
                        
                        # Kiểm tra file tồn tại và readable
                        if os.path.exists(normalized_path) and os.access(normalized_path, os.R_OK):
                            pdf_files.append(normalized_path)
                        else:
                            print(f"⚠️ Cannot access: {normalized_path}")
            
            if pdf_files:
                self.local_pdfs = pdf_files
                self.update_pdf_list_local()
                self.process_all_button.setEnabled(True)
                
                self.emit_status(f"Found {len(pdf_files)} PDF files", "success")
                
                QMessageBox.information(
                    self, 
                    "Thành công", 
                    f"Tìm thấy {len(pdf_files)} file PDF trong folder:\n{folder_path}\n\n"
                    f"Bao gồm các file có ký tự tiếng Việt."
                )
            else:
                self.emit_status("No PDF files found", "warning")
                QMessageBox.information(
                    self, 
                    "Thông báo", 
                    f"Không tìm thấy file PDF nào trong folder:\n{folder_path}"
                )
                
        except Exception as e:
            self.emit_status(f"Error scanning folder: {str(e)}", "error")
            QMessageBox.critical(
                self, 
                "Lỗi", 
                f"Lỗi khi quét folder:\n{str(e)}\n\n"
                f"Có thể do:\n"
                f"• Tên file/folder có ký tự đặc biệt\n"
                f"• Không có quyền truy cập\n"
                f"• Đường dẫn quá dài"
            )

    def update_pdf_list(self):
        """Cập nhật danh sách PDF đã tải từ Drive"""
        self.pdf_list.clear()
        for pdf_path in self.downloaded_pdfs:
            file_name = os.path.basename(pdf_path)
            self.pdf_list.addItem(f"[DRIVE] {file_name}")

    def update_pdf_list_local(self):
        """Cập nhật danh sách PDF từ local folder"""
        self.pdf_list.clear()
        base_folder = self.local_folder_input.text()
        
        for pdf_path in self.local_pdfs:
            try:
                # Tạo relative path để display
                try:
                    relative_path = os.path.relpath(pdf_path, base_folder)
                except ValueError:
                    # Nếu không thể tạo relative path, dùng basename
                    relative_path = os.path.basename(pdf_path)
                
                # Đảm bảo hiển thị Unicode đúng
                display_text = f"[LOCAL] {relative_path}"
                
                # Kiểm tra độ dài để tránh display quá dài
                if len(display_text) > 80:
                    display_text = f"[LOCAL] ...{relative_path[-70:]}"
                
                self.pdf_list.addItem(display_text)
                
            except Exception as e:
                # Fallback: chỉ hiển thị basename
                file_name = os.path.basename(pdf_path)
                self.pdf_list.addItem(f"[LOCAL] {file_name}")
                print(f"⚠️ Display error for {pdf_path}: {e}")

    def select_pdf_from_list(self, item):
        """Chọn PDF từ danh sách để xử lý đơn lẻ"""
        try:
            item_text = item.text()
            
            if item_text.startswith("[DRIVE]"):
                file_name = item_text.replace("[DRIVE] ", "")
                for pdf_path in self.downloaded_pdfs:
                    if os.path.basename(pdf_path) == file_name:
                        # Đảm bảo đường dẫn được encode đúng
                        normalized_path = os.path.normpath(pdf_path)
                        self.pdf_label.setText(normalized_path)
                        self.emit_status(f"Selected: {file_name}", "info")
                        break
            elif item_text.startswith("[LOCAL]"):
                relative_path = item_text.replace("[LOCAL] ", "")
                full_path = os.path.join(self.local_folder_input.text(), relative_path)
                
                # Normalize và check existence
                normalized_path = os.path.normpath(full_path)
                if os.path.exists(normalized_path):
                    self.pdf_label.setText(normalized_path)
                    self.emit_status(f"Selected: {os.path.basename(normalized_path)}", "info")
                else:
                    self.emit_status(f"File not found: {relative_path}", "error")
                    QMessageBox.warning(self, "Lỗi", f"Không tìm thấy file:\n{normalized_path}")
                    
        except Exception as e:
            self.emit_status(f"Error selecting file: {str(e)}", "error")
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi chọn file:\n{str(e)}")
    
    def process_all_files(self):
        """Xử lý tất cả PDF đã tải"""
        if not self.downloaded_pdfs and not self.local_pdfs:
            QMessageBox.warning(self, "Lỗi", "Không có file PDF nào để xử lý.")
            return
        
        prompt_path = self.prompt_label.text()
        if not os.path.isfile(prompt_path) or prompt_path == "Chưa chọn file prompt":
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file prompt.txt.")
            return
        
        # Lấy compression settings
        compress_enabled, quality = self.get_compression_settings()
        
        # Xác định danh sách PDF cần xử lý
        pdf_files = self.downloaded_pdfs if self.downloaded_pdfs else self.local_pdfs
        
        # Cleanup old thread
        if hasattr(self, 'batch_thread') and self.batch_thread is not None:
            try:
                self.batch_thread.quit()
                self.batch_thread.wait()
            except Exception:
                pass
            self.batch_thread = None

        # Disable UI
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Đang xử lý tất cả PDF...")
        
        # Tạo thread xử lý batch với compression
        self.batch_thread = BatchProcessingThread(
            pdf_files, 
            prompt_path, 
            self.project_id, 
            self.credentials,
            compress_enabled,
            quality
        )
        self.batch_thread.progress.connect(self.update_status)
        self.batch_thread.error.connect(self.show_error)
        self.batch_thread.finished.connect(self.batch_processing_finished)
        self.batch_thread.start()

    def batch_processing_finished(self, all_generated_files):
        """Hoàn tất xử lý batch"""
        self.generated_files.extend(all_generated_files)
        
        # Update results list
        for file_path in all_generated_files:
            self.docx_list.addItem(os.path.basename(file_path))
        
        pdf_count = len(self.downloaded_pdfs) if self.downloaded_pdfs else len(self.local_pdfs)
        self.status_label.setText(f"Đã xử lý {pdf_count} file PDF - Tạo ra {len(all_generated_files)} file")
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
        # Enable UI
        self._set_ui_enabled(True)
        
        QMessageBox.information(
            self, 
            "Hoàn tất", 
            f"Đã xử lý xong {pdf_count} file PDF.\n"
            f"Tổng cộng tạo ra {len(all_generated_files)} file."
        )

    def start_auto_processing(self):
        """Bắt đầu auto processing từ Google Drive"""
        drive_url = self.drive_url_input.text().strip()
        prompt_path = self.prompt_label.text()
        
        # Validation
        if not drive_url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập link Google Drive folder.")
            return
        
        if not os.path.isfile(prompt_path) or prompt_path == "Chưa chọn file prompt":
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file prompt.txt.")
            return
        
        # Confirm dialog
        reply = QMessageBox.question(
            self, 
            "Xác nhận", 
            f"Bạn có muốn tự động:\n"
            f"1. Tải tất cả PDF từ Google Drive\n"
            f"2. Gửi lên AI để phân tích\n"
            f"3. Tự động cắt PDF thành các phần nhỏ\n\n"
            f"Quá trình này có thể mất vài phút...",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Cleanup old processor
        if hasattr(self, 'auto_processor') and self.auto_processor is not None:
            try:
                self.auto_processor.quit()
                self.auto_processor.wait()
            except Exception:
                pass
            self.auto_processor = None

        # Disable UI
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Bắt đầu auto processing...")
        
        # Start auto processor
        self.auto_processor = AutoProcessor(
            drive_url, 
            prompt_path, 
            self.project_id, 
            self.credentials
        )
        
        self.auto_processor.progress.connect(self.update_status)
        self.auto_processor.error.connect(self.show_error)
        self.auto_processor.finished.connect(self.auto_processing_finished)
        self.auto_processor.file_completed.connect(self.on_file_completed)
        self.auto_processor.start()

    def start_local_processing(self):
        """Bắt đầu auto processing từ folder local"""
        folder_path = self.local_folder_input.text().strip()
        prompt_path = self.prompt_label.text()
        
        # Validation
        if not folder_path or not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn folder local hợp lệ.")
            return
        
        if not os.path.isfile(prompt_path) or prompt_path == "Chưa chọn file prompt":
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file prompt.txt.")
            return
        
        # Scan PDFs if not scanned
        if not self.local_pdfs:
            self.scan_local_folder()
            if not self.local_pdfs:
                return
        
        # Confirm dialog
        reply = QMessageBox.question(
            self, 
            "Xác nhận", 
            f"Bạn có muốn tự động xử lý:\n"
            f"📁 Folder: {folder_path}\n"
            f"📄 Số PDF: {len(self.local_pdfs)} files\n\n"
            f"1. Gửi lên AI để phân tích\n"
            f"2. Tự động cắt PDF thành các phần nhỏ\n\n"
            f"Quá trình này có thể mất vài phút...",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Cleanup old processor
        if hasattr(self, 'local_processor') and self.local_processor is not None:
            try:
                self.local_processor.quit()
                self.local_processor.wait()
            except Exception:
                pass
            self.local_processor = None

        # Disable UI
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Bắt đầu xử lý từ folder local...")
        
        # Start local processor
        self.local_processor = LocalProcessor(
            folder_path,
            self.local_pdfs,
            prompt_path, 
            self.project_id, 
            self.credentials
        )
        
        self.local_processor.progress.connect(self.update_status)
        self.local_processor.error.connect(self.show_error)
        self.local_processor.finished.connect(self.local_processing_finished)
        self.local_processor.file_completed.connect(self.on_file_completed)
        self.local_processor.start()

    def on_file_completed(self, file_name, generated_files):
        """Callback khi hoàn thành xử lý 1 file"""
        print(f"✓ Hoàn thành: {file_name} - {len(generated_files)} files")
        
        # Update list with new files
        for file_path in generated_files:
            self.docx_list.addItem(os.path.basename(file_path))

    def auto_processing_finished(self, all_generated_files):
        """Hoàn tất auto processing"""
        self.generated_files.extend(all_generated_files)
        
        # Update UI
        self.status_label.setText(f"Auto processing hoàn tất! Tạo ra {len(all_generated_files)} file")
        self.progress_bar.setValue(100)
        
        # Show results
        QMessageBox.information(
            self, 
            "Hoàn tất Auto Processing", 
            f"✅ Đã tự động xử lý thành công!\n\n"
            f"📊 Tổng cộng tạo ra: {len(all_generated_files)} file\n"
            f"📁 Thư mục kết quả: auto_processed/processed/\n\n"
            f"Các file đã được tự động cắt theo phân tích của AI."
        )
        
        # Re-enable UI
        self._set_ui_enabled(True)
        self.progress_bar.setVisible(False)

    def local_processing_finished(self, all_generated_files):
        """Hoàn tất local processing"""
        self.generated_files.extend(all_generated_files)
        
        # Update UI
        self.status_label.setText(f"Local processing hoàn tất! Tạo ra {len(all_generated_files)} file")
        self.progress_bar.setValue(100)
        
        # Show results
        QMessageBox.information(
            self, 
            "Hoàn tất Local Processing", 
            f"✅ Đã xử lý thành công từ folder local!\n\n"
            f"📊 Tổng cộng tạo ra: {len(all_generated_files)} file\n"
            f"📁 Thư mục kết quả: local_processed/\n\n"
            f"Các file đã được tự động cắt theo phân tích của AI."
        )
        
        # Re-enable UI
        self._set_ui_enabled(True)
        self.progress_bar.setVisible(False)

    def compress_selected_file(self):
        """Nén file đã chọn trong danh sách kết quả"""
        current_item = self.docx_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file cần nén.")
            return
        
        file_name = current_item.text()
        
        # Tìm full path của file
        selected_file = None
        for file_path in self.generated_files:
            if os.path.basename(file_path) == file_name:
                selected_file = file_path
                break
        
        if not selected_file or not os.path.exists(selected_file):
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file đã chọn.")
            return
        
        quality = self.get_compress_quality_from_combo()
        
        # Disable UI
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Đang nén file: {file_name}")
        
        # Start compression thread
        self.compress_thread = CompressThread([selected_file], quality)
        self.compress_thread.progress.connect(self.update_status)
        self.compress_thread.error.connect(self.show_error)
        self.compress_thread.finished.connect(self.compression_finished)
        self.compress_thread.start()

    def compress_all_files(self):
        """Nén tất cả file PDF đã tạo"""
        if not self.generated_files:
            QMessageBox.warning(self, "Lỗi", "Không có file PDF nào để nén.")
            return
        
        quality = self.get_compress_quality_from_combo()
        
        # Filter only existing PDF files
        existing_files = [f for f in self.generated_files if os.path.exists(f) and f.lower().endswith('.pdf')]
        
        if not existing_files:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file PDF hợp lệ để nén.")
            return
        
        reply = QMessageBox.question(
            self, 
            "Xác nhận", 
            f"Bạn có muốn nén {len(existing_files)} file PDF?\n\n"
            f"Chất lượng: {quality}\n"
            f"Quá trình này có thể mất vài phút...",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Disable UI
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Đang nén {len(existing_files)} file PDF...")
        
        # Start compression thread
        self.compress_thread = CompressThread(existing_files, quality)
        self.compress_thread.progress.connect(self.update_status)
        self.compress_thread.error.connect(self.show_error)
        self.compress_thread.finished.connect(self.compression_finished)
        self.compress_thread.start()

    def compress_folder(self):
        """Nén tất cả PDF trong một folder được chọn"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn folder chứa PDF cần nén")
        if not folder:
            return
        
        # Scan PDF files in folder
        pdf_files = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        if not pdf_files:
            QMessageBox.information(self, "Thông báo", f"Không tìm thấy file PDF nào trong folder:\n{folder}")
            return
        
        quality = self.get_compress_quality_from_combo()
        
        reply = QMessageBox.question(
            self, 
            "Xác nhận", 
            f"Tìm thấy {len(pdf_files)} file PDF trong folder:\n{folder}\n\n"
            f"Bạn có muốn nén tất cả?\n"
            f"Chất lượng: {quality}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Disable UI
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Đang nén {len(pdf_files)} file PDF trong folder...")
        
        # Start compression thread
        self.compress_thread = CompressThread(pdf_files, quality)
        self.compress_thread.progress.connect(self.update_status)
        self.compress_thread.error.connect(self.show_error)
        self.compress_thread.finished.connect(self.compression_finished)
        self.compress_thread.start()

    def compression_finished(self, results):
        """Hoàn tất quá trình nén"""
        successful = results.get('successful', [])
        failed = results.get('failed', [])
        
        self.status_label.setText(f"Nén hoàn tất: {len(successful)} thành công, {len(failed)} thất bại")
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        
        # Show results
        message = f"✅ Hoàn tất nén PDF!\n\n"
        message += f"📊 Thành công: {len(successful)} file\n"
        if failed:
            message += f"❌ Thất bại: {len(failed)} file\n"
        
        if successful:
            total_saved = sum(result.get('saved_mb', 0) for result in successful)
            message += f"\n💾 Tổng dung lượng tiết kiệm: {total_saved:.2f} MB"
        
        QMessageBox.information(self, "Hoàn tất nén", message)

    def open_file_from_list(self, item):
        """Mở file được chọn từ danh sách kết quả"""
        file_name = item.text()
        
        # Tìm full path của file
        selected_file = None
        for file_path in self.generated_files:
            if os.path.basename(file_path) == file_name:
                selected_file = file_path
                break
        
        if selected_file and os.path.exists(selected_file):
            try:
                os.startfile(selected_file)  # Windows
            except AttributeError:
                os.system(f'open "{selected_file}"')  # macOS
            except Exception:
                os.system(f'xdg-open "{selected_file}"')  # Linux

    def _set_ui_enabled(self, enabled):
        """Enable/disable UI elements"""
        self.download_button.setEnabled(enabled)
        self.auto_process_button.setEnabled(enabled)
        self.auto_process_local_button.setEnabled(enabled)
        self.browse_folder_button.setEnabled(enabled)
        self.scan_folder_button.setEnabled(enabled)
        self.process_button.setEnabled(enabled)
        self.process_all_button.setEnabled(enabled)
        self.pdf_button.setEnabled(enabled)
        self.prompt_button.setEnabled(enabled)
        self.edit_prompt_button.setEnabled(enabled)
        self.compress_selected_btn.setEnabled(enabled)
        self.compress_all_btn.setEnabled(enabled)
        self.compress_folder_btn.setEnabled(enabled)
    
    def emit_status(self, message, status_type="info"):
        """Emit status signal to main window"""
        self.status_changed.emit(message, status_type)
    
    def emit_progress(self, value, visible=True):
        """Emit progress signal to main window"""
        self.progress_changed.emit(value, visible)
    
    def emit_file_count(self, count):
        """Emit file count signal to main window"""
        self.file_count_changed.emit(count)
    
    def update_status(self, message, percent):
        """Cập nhật status và progress bar"""
        self.status_label.setText(message)
        self.progress_bar.setValue(percent)
        
        # Emit to main window status bar
        if percent == 100:
            self.emit_status(message, "success")
            self.emit_progress(percent, False)  # Hide progress
        elif "Lỗi" in message or "Error" in message:
            self.emit_status(message, "error")
        else:
            self.emit_status(message, "processing")
            self.emit_progress(percent, True)
    
    def show_error(self, message):
        """Hiển thị lỗi và reset UI"""
        QMessageBox.critical(self, "Lỗi", message)
        self.status_label.setText("Lỗi xảy ra")
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)

    def processing_finished(self, generated_files):
        """Hoàn tất xử lý đơn lẻ"""
        self.generated_files.extend(generated_files)
        self.docx_list.clear()
        
        # Update results list
        for fname in self.generated_files:
            self.docx_list.addItem(os.path.basename(fname))
            
        self.status_label.setText("Hoàn tất xử lý")
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        
        if generated_files:
            self.docx_list.setCurrentRow(len(self.docx_list) - len(generated_files))
            
        # Emit signals
        self.emit_status(f"Completed! Generated {len(generated_files)} files", "success")
        self.emit_file_count(len(self.generated_files))
        self.emit_progress(100, False)
        
        # Show completion message
        QMessageBox.information(
            self, 
            "Hoàn tất", 
            f"Đã xử lý thành công!\nTạo ra {len(generated_files)} file PDF."
        )
    
    def normalize_file_path(self, file_path):
        """Normalize file path để xử lý Unicode và special characters"""
        try:
            # Normalize path
            normalized = os.path.normpath(file_path)
            
            # Ensure the path is properly encoded
            if isinstance(normalized, str):
                # Đảm bảo encoding đúng
                normalized = normalized.encode('utf-8', errors='replace').decode('utf-8')
            
            return normalized
        except Exception as e:
            print(f"⚠️ Error normalizing path {file_path}: {e}")
            return file_path

    def is_file_accessible(self, file_path):
        """Kiểm tra file có thể truy cập được không"""
        try:
            normalized_path = self.normalize_file_path(file_path)
            return os.path.exists(normalized_path) and os.access(normalized_path, os.R_OK)
        except Exception:
            return False

    def get_safe_filename(self, file_path):
        """Lấy tên file an toàn cho display"""
        try:
            return os.path.basename(self.normalize_file_path(file_path))
        except Exception:
            return "Unknown file"