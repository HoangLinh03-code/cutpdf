import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont
from datetime import datetime
import requests
import time

# THÊM IMPORT CHO GOOGLE DRIVE
from core.client_driver import GoogleDriveAPI  # THÊM DÒNG NÀY

class ConvertPdfWidget(QWidget):
    # Signals để giao tiếp với main window
    status_changed = pyqtSignal(str, str)  # message, type
    progress_changed = pyqtSignal(int, bool)  # value, visible
    file_count_changed = pyqtSignal(int)  # count
    
    def __init__(self):
        super().__init__()
        
        # Data storage
        self.selected_pdfs = []
        self.converted_files = []
        self.conversion_thread = None
        
        # Mathpix credentials
        self.app_key = None
        self.app_id = None
        self.load_mathpix_credentials()
        
        self.init_ui()

    def load_mathpix_credentials(self):
        """Load Mathpix credentials từ .env hoặc fallback hardcoded"""
        try:
            
            self.app_key = os.getenv('MATHPIX_APP_KEY')
            self.app_id = os.getenv('MATHPIX_APP_ID')
            
            # Fallback về hardcoded credentials nếu không có trong .env
            if not self.app_key or not self.app_id:
                print("⚠️ Using fallback Mathpix credentials")
                self.app_key = "ccea572d017978e32d6bc06ec98e1cf8edee07834194f6a23175730cf4e30b02"
                self.app_id = "companyname_edmicroeducationcompanylimited_taxcode_0108115077_address_5thfloor_tayhabuilding_no_19tohuustreet_trungvanward_namtuliemdistrict_hanoicity_vietnam_d72a10_c73665"
            
        except ImportError:
            print("⚠️ python-dotenv not installed, using hardcoded credentials")
            self.app_key = "ccea572d017978e32d6bc06ec98e1cf8edee07834194f6a23175730cf4e30b02"
            self.app_id = "companyname_edmicroeducationcompanylimited_taxcode_0108115077_address_5thfloor_tayhabuilding_no_19tohuustreet_trungvanward_namtuliemdistrict_hanoicity_vietnam_d72a10_c73665"
        except Exception as e:
            print(f"⚠️ Error loading Mathpix credentials: {e}")
            # Use hardcoded as fallback
            self.app_key = "ccea572d017978e32d6bc06ec98e1cf8edee07834194f6a23175730cf4e30b02"
            self.app_id = "companyname_edmicroeducationcompanylimited_taxcode_0108115077_address_5thfloor_tayhabuilding_no_19tohuustreet_trungvanward_namtuliemdistrict_hanoicity_vietnam_d72a10_c73665"

    def init_ui(self):
        """Khởi tạo giao diện Convert PDF"""
        
        # --- [FIX GIAO DIỆN START] ---
        # 1. Tạo layout bao ngoài cùng
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # 2. Tạo vùng cuộn (Scroll Area)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True) # Cho phép nội dung co giãn
        scroll_area.setFrameShape(QFrame.NoFrame) # Bỏ viền xấu

        # 3. Tạo Widget chứa nội dung (Container)
        content_widget = QWidget()
        
        # 4. Layout chính gắn vào Container (Thay vì gắn trực tiếp vào self như cũ)
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15) # Tăng khoảng cách giữa các phần cho thoáng (Dãn ra)
        layout.setContentsMargins(20, 20, 20, 20) # Căn lề rộng rãi
        # --- [FIX GIAO DIỆN END] ---
        
        # Header - CẬP NHẬT
        header_label = QLabel("🔄 CONVERT PDF TO MARKDOWN & DOCX\n📥 Hỗ trợ tải từ Google Drive")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 8px;
                color: #1565c0;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(header_label)
        
        # File selection section
        file_section = self.create_file_section()
        layout.addWidget(file_section)
        
        # Conversion options
        options_section = self.create_options_section()
        layout.addWidget(options_section)
        
        # Progress section
        progress_section = self.create_progress_section()
        layout.addWidget(progress_section)
        
        # Results section
        results_section = self.create_results_section()
        layout.addWidget(results_section)
        
        # self.setLayout(layout)  <-- BỎ DÒNG NÀY (CODE CŨ)

        # --- [FIX GIAO DIỆN START] ---
        # 5. Đẩy nội dung lên trên cùng và gắn vào Scroll Area
        layout.addStretch() 
        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)
        # --- [FIX GIAO DIỆN END] ---

    def create_file_section(self):
        """Tạo section chọn file - THÊM GOOGLE DRIVE SUPPORT"""
        group = QGroupBox("📁 Chọn PDF Files")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        layout = QVBoxLayout()
        layout.setSpacing(10) # Dãn khoảng cách trong group box
        
        # THÊM: Google Drive URL input
        drive_layout = QHBoxLayout()
        drive_label = QLabel("Google Drive URL:")
        self.drive_url_input = QLineEdit()
        self.drive_url_input.setPlaceholderText("Nhập link folder Google Drive chứa file PDF...")
        self.drive_url_input.setFixedHeight(35)
        
        self.download_from_drive_btn = QPushButton("📥 Tải từ Drive")
        self.download_from_drive_btn.setFixedHeight(35)
        self.download_from_drive_btn.clicked.connect(self.download_from_drive)
        
        drive_layout.addWidget(drive_label)
        drive_layout.addWidget(self.drive_url_input, 3)
        drive_layout.addWidget(self.download_from_drive_btn, 1)
        
        # File selection buttons
        buttons_layout = QHBoxLayout()
        
        self.select_files_btn = QPushButton("📄 Chọn PDF Files")
        self.select_files_btn.setFixedHeight(40)
        self.select_files_btn.clicked.connect(self.select_pdf_files)
        
        self.select_folder_btn = QPushButton("📂 Chọn Folder")
        self.select_folder_btn.setFixedHeight(40)
        self.select_folder_btn.clicked.connect(self.select_pdf_folder)
        
        self.clear_list_btn = QPushButton("🗑️ Xóa danh sách")
        self.clear_list_btn.setFixedHeight(40)
        self.clear_list_btn.clicked.connect(self.clear_file_list)
        
        buttons_layout.addWidget(self.select_files_btn)
        buttons_layout.addWidget(self.select_folder_btn)
        buttons_layout.addWidget(self.clear_list_btn)
        
        # File list
        self.pdf_list = QListWidget()
        self.pdf_list.setFixedHeight(150)
        self.pdf_list.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # File count label
        self.file_count_label = QLabel("Số file được chọn: 0")
        self.file_count_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.file_count_label.setStyleSheet("color: #666;")
        
        layout.addLayout(drive_layout)  # THÊM DRIVE LAYOUT
        layout.addLayout(buttons_layout)
        layout.addWidget(self.pdf_list)
        layout.addWidget(self.file_count_label)
        
        group.setLayout(layout)
        return group

    def create_options_section(self):
        """Tạo section options - CẬP NHẬT để hiển thị folder structure"""
        group = QGroupBox("⚙️ Conversion Options")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        layout = QVBoxLayout()
        layout.setSpacing(8) # Dãn khoảng cách
        
        # Output format
        format_layout = QHBoxLayout()
        format_label = QLabel("Output Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "📝 Markdown (.md)", 
            "📄 DOCX (Microsoft Word)", 
            "📃 PDF (OCR Enhanced)"
        ])
        self.format_combo.setCurrentIndex(0)
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        
        # Output folder
        output_layout = QHBoxLayout()
        output_label = QLabel("Output Base Folder:")
        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("Để trống sẽ tạo folder 'output' trong project...")
        self.browse_output_btn = QPushButton("📂 Browse")
        self.browse_output_btn.clicked.connect(self.browse_output_folder)
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_folder_input, 2)
        output_layout.addWidget(self.browse_output_btn)
        
        # THÊM: Folder structure info
        self.folder_structure_info = QLabel("📁 Structure: output/{source_folder_name}/{filename}_converted.md")
        self.folder_structure_info.setStyleSheet("color: #666; font-style: italic; font-size: 9px;")
        self.folder_structure_info.setWordWrap(True)
        
        # Advanced options
        self.keep_original_checkbox = QCheckBox("Giữ lại file PDF gốc")
        self.keep_original_checkbox.setChecked(True)
        
        self.auto_open_checkbox = QCheckBox("Tự động mở file sau khi convert")
        self.auto_open_checkbox.setChecked(False)
        
        self.smart_wait_checkbox = QCheckBox("Smart waiting (tự động chờ conversion hoàn thành)")
        self.smart_wait_checkbox.setChecked(True)
        self.smart_wait_checkbox.setToolTip("Tự động kiểm tra status thay vì chờ cố định 15 giây")
        
        # Credentials status
        self.credentials_status = QLabel()
        self.update_credentials_status()
        
        layout.addLayout(format_layout)
        layout.addLayout(output_layout)
        layout.addWidget(self.folder_structure_info)  # THÊM INFO
        layout.addWidget(self.keep_original_checkbox)
        layout.addWidget(self.auto_open_checkbox)
        layout.addWidget(self.smart_wait_checkbox)
        layout.addWidget(self.credentials_status)
        
        group.setLayout(layout)
        return group

    def create_progress_section(self):
        """Tạo section progress"""
        group = QGroupBox("📊 Progress")
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Overall progress
        self.overall_progress = QProgressBar()
        self.overall_progress.setVisible(False)
        self.overall_progress_label = QLabel("Overall Progress")
        
        # Current file progress
        self.current_progress = QProgressBar()
        self.current_progress.setVisible(False)
        self.current_progress_label = QLabel("Current File")
        
        # Status
        self.status_label = QLabel("Ready to convert")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        
        layout.addWidget(self.overall_progress_label)
        layout.addWidget(self.overall_progress)
        layout.addWidget(self.current_progress_label)
        layout.addWidget(self.current_progress)
        layout.addWidget(self.status_label)
        
        group.setLayout(layout)
        return group

    def create_results_section(self):
        """Tạo section results"""
        group = QGroupBox("📄 Conversion Results")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.convert_btn = QPushButton("🚀 Bắt đầu Convert")
        self.convert_btn.setFixedHeight(45)
        self.convert_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.convert_btn.clicked.connect(self.start_conversion)
        
        self.stop_btn = QPushButton("⏹️ Dừng")
        self.stop_btn.setFixedHeight(45)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_conversion)
        
        self.open_folder_btn = QPushButton("📂 Mở thư mục kết quả")
        self.open_folder_btn.setFixedHeight(45)
        self.open_folder_btn.clicked.connect(self.open_results_folder)
        
        buttons_layout.addWidget(self.convert_btn, 2)
        buttons_layout.addWidget(self.stop_btn, 1)
        buttons_layout.addWidget(self.open_folder_btn, 1)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setFixedHeight(200)
        self.results_list.itemDoubleClicked.connect(self.open_result_file)
        
        # Statistics
        self.stats_label = QLabel("Statistics: 0 converted, 0 failed")
        self.stats_label.setFont(QFont("Arial", 10))
        self.stats_label.setStyleSheet("color: #666; padding: 5px;")
        
        layout.addLayout(buttons_layout)
        layout.addWidget(self.results_list)
        layout.addWidget(self.stats_label)
        
        group.setLayout(layout)
        return group

    def update_credentials_status(self):
        """Cập nhật trạng thái credentials"""
        if self.app_key and self.app_id:
            self.credentials_status.setText("✅ Mathpix credentials loaded")
            self.credentials_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.credentials_status.setText("❌ Mathpix credentials not found")
            self.credentials_status.setStyleSheet("color: red; font-weight: bold;")

    def select_pdf_files(self):
        """Chọn multiple PDF files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Chọn PDF Files", 
            "", 
            "PDF Files (*.pdf)"
        )
        
        if files:
            self.selected_pdfs.extend(files)
            self.update_file_list()

    def select_pdf_folder(self):
        """Chọn folder chứa PDF"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn folder chứa PDF files")
        if folder:
            # Scan PDF files in folder
            pdf_files = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
            
            if pdf_files:
                self.selected_pdfs.extend(pdf_files)
                self.update_file_list()
                QMessageBox.information(
                    self, 
                    "Thành công", 
                    f"Tìm thấy {len(pdf_files)} PDF files trong folder"
                )
            else:
                QMessageBox.information(self, "Thông báo", "Không tìm thấy PDF files nào")

    def clear_file_list(self):
        """Xóa danh sách file"""
        self.selected_pdfs.clear()
        self.update_file_list()

    def update_file_list(self):
        """Cập nhật danh sách file trong UI - THÊM SOURCE DISPLAY"""
        self.pdf_list.clear()
        
        # Remove duplicates
        self.selected_pdfs = list(set(self.selected_pdfs))

        download_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "downloaded_pdfs")
        
        for pdf_path in self.selected_pdfs:
            # Xác định source của file
            if download_path in pdf_path:
                source_prefix = "[DRIVE] "
            else:
                source_prefix = "[LOCAL] "
                
            item_text = f"{source_prefix}{os.path.basename(pdf_path)}"
            if len(pdf_path) > 80:
                item_text += f"\n📁 ...{pdf_path[-60:]}"
            else:
                item_text += f"\n📁 {pdf_path}"
                
            self.pdf_list.addItem(item_text)
        
        # Update count
        count = len(self.selected_pdfs)
        self.file_count_label.setText(f"Số file được chọn: {count}")
        
        # Enable/disable convert button
        has_files = count > 0
        has_credentials = bool(self.app_key and self.app_id)
        self.convert_btn.setEnabled(has_files and has_credentials)
        
        # Emit file count to main window
        self.emit_file_count(count)
   

    def browse_output_folder(self):
        """Browse output folder"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu kết quả")
        if folder:
            self.output_folder_input.setText(folder)

    def start_conversion(self):
        """Bắt đầu quá trình convert"""
        if not self.selected_pdfs:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất 1 PDF file")
            return
        
        if not self.app_key or not self.app_id:
            QMessageBox.warning(
                self, 
                "Lỗi", 
                "Mathpix credentials không hợp lệ.\n\n"
                "Vui lòng kiểm tra MATHPIX_APP_KEY và MATHPIX_APP_ID"
            )
            return
        
        # Confirm conversion
        format_text = self.format_combo.currentText()
        reply = QMessageBox.question(
            self, 
            "Xác nhận", 
            f"Bạn có muốn convert {len(self.selected_pdfs)} PDF files?\n\n"
            f"Output format: {format_text}\n"
            f"Smart waiting: {'Enabled' if self.smart_wait_checkbox.isChecked() else 'Disabled'}\n"
            f"Quá trình này có thể mất vài phút...",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Start conversion thread
        self.start_conversion_thread()

    def start_conversion_thread(self):
        """Bắt đầu conversion thread"""
        # Cleanup old thread
        if self.conversion_thread is not None:
            self.conversion_thread.quit()
            self.conversion_thread.wait()
        
        # Get output folder
        output_folder = self.output_folder_input.text().strip()
        if not output_folder:
            output_folder = None  # Use same folder as original
        
        # Create conversion thread
        self.conversion_thread = ConversionThread(
            self.selected_pdfs,
            output_folder,
            self.app_key,
            self.app_id,
            self.format_combo.currentText(),
            self.smart_wait_checkbox.isChecked()
        )
        
        # Connect signals
        self.conversion_thread.progress_updated.connect(self.update_progress)
        self.conversion_thread.file_completed.connect(self.on_file_completed)
        self.conversion_thread.conversion_finished.connect(self.on_conversion_finished)
        self.conversion_thread.error_occurred.connect(self.on_error_occurred)
        
        # Update UI
        self.set_conversion_ui_state(True)
        
        # Start thread
        self.conversion_thread.start()

    def stop_conversion(self):
        """Dừng conversion"""
        if self.conversion_thread:
            self.conversion_thread.stop_conversion()
            self.status_label.setText("Đang dừng conversion...")

    def set_conversion_ui_state(self, converting):
        """Set UI state khi convert"""
        self.convert_btn.setEnabled(not converting)
        self.stop_btn.setEnabled(converting)
        
        if converting:
            self.overall_progress.setVisible(True)
            self.current_progress.setVisible(True)
            self.status_label.setText("Đang convert...")
            self.emit_status("Starting PDF conversion...", "processing")
        else:
            self.overall_progress.setVisible(False)
            self.current_progress.setVisible(False)
            self.status_label.setText("Ready to convert")

    def update_progress(self, overall_percent, current_percent, status_message):
        """Cập nhật progress"""
        if overall_percent >= 0:
            self.overall_progress.setValue(overall_percent)
        if current_percent >= 0:
            self.current_progress.setValue(current_percent)
        self.status_label.setText(status_message)
        
        # Emit to main window
        if overall_percent >= 0:
            self.emit_progress(overall_percent, True)
        self.emit_status(status_message, "processing")

    def on_file_completed(self, original_file, output_file, success, error_msg):
        """Xử lý khi hoàn thành 1 file"""
        file_name = os.path.basename(original_file)
        
        if success:
            self.converted_files.append(output_file)
            result_text = f"✅ {file_name} → {os.path.basename(output_file)}"
            self.results_list.addItem(result_text)
            
            # Auto open if requested
            if self.auto_open_checkbox.isChecked():
                try:
                    os.startfile(output_file)
                except:
                    pass
        else:
            result_text = f"❌ {file_name} - {error_msg}"
            self.results_list.addItem(result_text)
        
        # Update stats
        self.update_statistics()

    def on_conversion_finished(self, successful_count, failed_count):
        """Xử lý khi hoàn thành conversion"""
        self.set_conversion_ui_state(False)
        
        # Update progress
        self.emit_progress(100, False)
        self.emit_file_count(len(self.converted_files))
        
        # Show completion message
        message = f"🎉 Conversion hoàn tất!\n\n"
        message += f"✅ Thành công: {successful_count} files\n"
        if failed_count > 0:
            message += f"❌ Thất bại: {failed_count} files\n"
        
        self.emit_status(f"Conversion completed: {successful_count} successful", "success")
        
        QMessageBox.information(self, "Hoàn tất", message)

    def on_error_occurred(self, error_message):
        """Xử lý khi có lỗi"""
        self.set_conversion_ui_state(False)
        self.status_label.setText("Conversion failed")
        self.emit_status(f"Conversion error: {error_message}", "error")
        
        QMessageBox.critical(self, "Lỗi", f"Conversion failed:\n{error_message}")

    def update_statistics(self):
        """Cập nhật thống kê"""
        successful = len([item for item in range(self.results_list.count()) 
                         if self.results_list.item(item).text().startswith("✅")])
        failed = self.results_list.count() - successful
        
        self.stats_label.setText(f"Statistics: {successful}, {failed} failed")

    def open_results_folder(self):
        """Mở thư mục kết quả"""
        if self.converted_files:
            folder = os.path.dirname(self.converted_files[0])
            try:
                os.startfile(folder)
            except:
                QMessageBox.information(self, "Thông báo", f"Results folder: {folder}")
        else:
            QMessageBox.information(self, "Thông báo", "Chưa có file nào được convert")

    def open_result_file(self, item):
        """Mở file kết quả khi double click"""
        item_text = item.text()
        if item_text.startswith("✅"):
            # Extract file name and find full path
            for converted_file in self.converted_files:
                if os.path.basename(converted_file) in item_text:
                    try:
                        os.startfile(converted_file)
                    except Exception as e:
                        QMessageBox.warning(self, "Lỗi", f"Không thể mở file: {str(e)}")
                    break

    def emit_status(self, message, status_type="info"):
        """Emit status signal to main window"""
        self.status_changed.emit(message, status_type)
    
    def emit_progress(self, value, visible=True):
        """Emit progress signal to main window"""
        self.progress_changed.emit(value, visible)
    
    def emit_file_count(self, count):
        """Emit file count signal to main window"""
        self.file_count_changed.emit(count)

    def download_from_drive(self):
        """Tải PDF từ Google Drive - DI CHUYỂN VÀO ConvertPdfWidget"""
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
        
        # Disable UI during download
        self.set_download_ui_state(False)
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
                # Thêm vào danh sách selected_pdfs
                self.selected_pdfs.extend(downloaded_files)
                self.update_file_list()
                
                self.status_label.setText(f"Đã tải {len(downloaded_files)} file PDF")
                self.emit_status(f"Downloaded {len(downloaded_files)} PDF files from Drive", "success")
                
                QMessageBox.information(
                    self, 
                    "Thành công", 
                    f"Đã tải xuống {len(downloaded_files)} file PDF từ Google Drive"
                )
            else:
                self.status_label.setText("Không tìm thấy file PDF nào")
                QMessageBox.information(self, "Thông báo", "Không tìm thấy file PDF nào trong folder")
        
        except Exception as e:
            error_msg = f"Không thể tải từ Google Drive: {str(e)}"
            QMessageBox.critical(self, "Lỗi", error_msg)
            self.status_label.setText("Lỗi khi tải từ Drive")
            self.emit_status(error_msg, "error")
        
        finally:
            self.set_download_ui_state(True)

    def set_download_ui_state(self, enabled):
        """Set UI state khi download từ Drive - DI CHUYỂN VÀO ConvertPdfWidget"""
        self.download_from_drive_btn.setEnabled(enabled)
        self.select_files_btn.setEnabled(enabled)
        self.select_folder_btn.setEnabled(enabled)
        self.convert_btn.setEnabled(enabled and len(self.selected_pdfs) > 0 and bool(self.app_key and self.app_id))


# XÓA DUPLICATE - CHỈ GIỮ LỚP ConversionThread DƯỚI ĐÂY
class ConversionThread(QThread):
    """Thread xử lý conversion - TÍCH HỢP convert_odf_md.py"""
    
    progress_updated = pyqtSignal(int, int, str)  # overall%, current%, status
    file_completed = pyqtSignal(str, str, bool, str)  # original, output, success, error
    conversion_finished = pyqtSignal(int, int)  # successful, failed
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pdf_files, output_folder, app_key, app_id, output_format, smart_wait=True):
        super().__init__()
        self.pdf_files = pdf_files
        self.output_folder = output_folder
        self.app_key = app_key
        self.app_id = app_id
        self.output_format = output_format
        self.smart_wait = smart_wait
        self.should_stop = False
        
    def stop_conversion(self):
        """Dừng conversion"""
        self.should_stop = True
        
    def run(self):
        """Chạy conversion"""
        successful = 0
        failed = 0
        total_files = len(self.pdf_files)
        
        try:
            for i, pdf_file in enumerate(self.pdf_files):
                if self.should_stop:
                    break
                    
                # Update overall progress
                overall_percent = int((i / total_files) * 100)
                file_name = os.path.basename(pdf_file)
                self.progress_updated.emit(overall_percent, 0, f"Converting {file_name} ({i+1}/{total_files})")
                
                # Convert single file
                success, output_file, error_msg = self.convert_single_file(pdf_file)
                
                if success:
                    successful += 1
                    self.file_completed.emit(pdf_file, output_file, True, "")
                else:
                    failed += 1
                    self.file_completed.emit(pdf_file, "", False, error_msg)
                
                # Delay giữa các file để tránh rate limit
                if i < total_files - 1 and not self.should_stop:
                    self.progress_updated.emit(-1, -1, "Waiting 3 seconds to avoid rate limit...")
                    time.sleep(3)
            
            # Final progress update
            if not self.should_stop:
                self.progress_updated.emit(100, 100, "Conversion completed")
                self.conversion_finished.emit(successful, failed)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def convert_single_file(self, pdf_file):
        """Convert một file PDF - TÍCH HỢP từ convert_odf_md.py"""
        try:
            # Update current file progress
            file_name = os.path.basename(pdf_file)
            file_size = os.path.getsize(pdf_file) / (1024 * 1024)  # MB
            self.progress_updated.emit(-1, 10, f"Uploading {file_name} ({file_size:.1f}MB)")
            
            # 1. Upload PDF to Mathpix
            pdf_id = self.send_pdf_to_mathpix(pdf_file)
            if not pdf_id:
                return False, "", "Failed to upload PDF"
            
            self.progress_updated.emit(-1, 30, f"Processing {file_name} (PDF ID: {pdf_id[:8]}...)")
            
            # 2. Wait for processing
            if self.smart_wait:
                # Smart waiting với status check
                if not self.wait_for_conversion(pdf_id, file_name):
                    return False, "", "Processing timeout or failed"
            else:
                # Fixed waiting
                time.sleep(15)
            
            self.progress_updated.emit(-1, 80, f"Downloading {file_name}")
            
            # 3. Download result
            output_file = self.download_result(pdf_id, pdf_file)
            if not output_file:
                return False, "", "Failed to download result"
            
            # 4. Verify output file
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                self.progress_updated.emit(-1, 100, f"Completed {file_name} ({file_size} bytes)")
                return True, output_file, ""
            else:
                return False, "", "Output file not created"
            
        except Exception as e:
            return False, "", str(e)
    
    def send_pdf_to_mathpix(self, file_path):
        """Gửi PDF lên Mathpix - TÍCH HỢP từ convert_odf_md.py"""
        try:
            with open(file_path, "rb") as f:
                files = {
                    "file": (os.path.basename(file_path), f, "application/pdf")
                }
                
                # Specify conversion formats based on output format
                data = {}
                if "Markdown" in self.output_format:
                    data["conversion_formats[md]"] = "true"
                    data["conversion_formats[docx]"] = "false"
                elif "DOCX" in self.output_format:
                    data["conversion_formats[docx]"] = "true"
                    data["conversion_formats[md]"] = "false"
                
                response = requests.post(
                    "https://api.mathpix.com/v3/pdf",
                    headers={
                        "app_id": self.app_id,
                        "app_key": self.app_key
                    },
                    files=files,
                    data=data,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('pdf_id')
                else:
                    print(f"❌ API Error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
    
    def check_conversion_status(self, pdf_id):
        """Kiểm tra trạng thái conversion - TỪ convert_odf_md.py"""
        headers = {
            'app_key': self.app_key,
            'app_id': self.app_id
        }
        
        try:
            url = f"https://api.mathpix.com/v3/pdf/{pdf_id}"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                print(f"❌ Status check error: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return None
    
    def wait_for_conversion(self, pdf_id, file_name, max_wait_time=300):
        """Chờ conversion hoàn thành - TỪ convert_odf_md.py"""
        start_time = time.time()
        check_interval = 10  # Check mỗi 10 giây
        
        while time.time() - start_time < max_wait_time and not self.should_stop:
            status_result = self.check_conversion_status(pdf_id)
            
            if not status_result:
                time.sleep(check_interval)
                continue
            
            status = status_result.get('status', 'unknown')
            elapsed = int(time.time() - start_time)
            
            if status == 'completed':
                self.progress_updated.emit(-1, 70, f"✅ {file_name} processed successfully ({elapsed}s)")
                return True
            elif status == 'error':
                error_msg = status_result.get('error', 'Unknown error')
                self.progress_updated.emit(-1, 0, f"❌ Processing error: {error_msg}")
                return False
            elif status == 'processing':
                self.progress_updated.emit(-1, 50, f"🔄 Processing {file_name}... ({elapsed}s)")
            
            time.sleep(check_interval)
        
        # Timeout
        self.progress_updated.emit(-1, 0, f"⏰ Timeout processing {file_name}")
        return False
    
    def download_result(self, pdf_id, original_file):
        """Download kết quả conversion - CẬP NHẬT để tạo folder theo tên folder gốc"""
        try:
            # Determine output directory structure
            if self.output_folder:
                # Sử dụng output folder được chỉ định
                base_output_dir = self.output_folder
            else:
                # Tạo folder output trong thư mục gốc của project
                if getattr(sys, 'frozen', False):
                    app_dir = os.path.dirname(sys.executable)
                else:
                    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                base_output_dir = os.path.join(app_dir, "output")
        
            # Tạo subfolder dựa trên tên folder chứa file gốc
            original_dir_name = os.path.basename(os.path.dirname(original_file))
            
            # Nếu file từ Drive, lấy tên folder cuối cùng trong path
            if "downloaded_pdfs" in original_file:
                # Extract folder name từ path: .../downloaded_pdfs/folder_name/file.pdf
                path_parts = original_file.split(os.sep)
                if "downloaded_pdfs" in path_parts:
                    drive_index = path_parts.index("downloaded_pdfs")
                    if drive_index + 1 < len(path_parts) - 1:  # Có folder con sau downloaded_pdfs
                        original_dir_name = path_parts[drive_index + 1]
                    else:
                        original_dir_name = "drive_files"
        
            # Tạo thư mục output cuối cùng
            output_dir = os.path.join(base_output_dir, original_dir_name)
            
            # Tạo output filename dựa trên format
            base_name = os.path.splitext(os.path.basename(original_file))[0]
            
            if "Markdown" in self.output_format:
                output_file = os.path.join(output_dir, f"{base_name}.md")
                url = f"https://api.mathpix.com/v3/pdf/{pdf_id}.md"
                write_mode = 'w'
                encoding = 'utf-8'
            elif "DOCX" in self.output_format:
                output_file = os.path.join(output_dir, f"{base_name}_converted.docx")
                url = f"https://api.mathpix.com/v3/pdf/{pdf_id}.docx"
                write_mode = 'wb'
                encoding = None
            else:  # PDF OCR
                output_file = os.path.join(output_dir, f"{base_name}_ocr.pdf")
                url = f"https://api.mathpix.com/v3/pdf/{pdf_id}.pdf"
                write_mode = 'wb'
                encoding = None
        
            # Download file
            headers = {
                'app_key': self.app_key, 
                'app_id': self.app_id
            }
            
            response = requests.get(url, headers=headers, timeout=120)
            
            if response.status_code == 200:
                # Ensure output directory exists
                os.makedirs(output_dir, exist_ok=True)
                
                # Write file
                if write_mode == 'w':
                    # Text mode for Markdown
                    with open(output_file, 'w', encoding=encoding) as f:
                        f.write(response.text)
                else:
                    # Binary mode for DOCX/PDF
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                
                return output_file
            else:
                print(f"❌ Download error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None