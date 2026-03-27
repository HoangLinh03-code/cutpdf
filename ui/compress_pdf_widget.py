import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QListWidget, QProgressBar, QMessageBox, 
    QGroupBox, QComboBox, QFrame, QScrollArea, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.compress_manager import CompressThread

class CompressPdfWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.compress_thread = None
        self.init_ui()

    def init_ui(self):
        # Thiết lập Layout chính có ScrollArea
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # 1. Header
        header_label = QLabel("🗜️ CÔNG CỤ NÉN PDF HÀNG LOẠT")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 8px;
                color: #1565c0;
            }
        """)
        layout.addWidget(header_label)

        # 2. Section Chọn File
        select_group = QGroupBox("📁 Chọn File PDF cần nén")
        select_group.setFont(QFont("Arial", 11, QFont.Bold))
        select_layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("📄 Thêm File(s)")
        self.btn_add_files.setFixedHeight(35)
        self.btn_add_files.clicked.connect(self.add_files)

        self.btn_add_folder = QPushButton("📂 Thêm Folder")
        self.btn_add_folder.setFixedHeight(35)
        self.btn_add_folder.clicked.connect(self.add_folder)
        
        self.btn_clear_list = QPushButton("🗑️ Xóa danh sách")
        self.btn_clear_list.setFixedHeight(35)
        self.btn_clear_list.clicked.connect(self.clear_files)

        btn_layout.addWidget(self.btn_add_files)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_clear_list)

        self.file_list_widget = QListWidget()
        self.file_list_widget.setFixedHeight(200)
        self.file_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        select_layout.addLayout(btn_layout)
        select_layout.addWidget(QLabel("Danh sách file chờ nén (Hỗ trợ chọn nhiều):"))
        select_layout.addWidget(self.file_list_widget)
        select_group.setLayout(select_layout)
        layout.addWidget(select_group)

        # 3. Section Cấu hình và Nén
        config_group = QGroupBox("⚙️ Cấu hình Nén")
        config_group.setFont(QFont("Arial", 11, QFont.Bold))
        config_layout = QVBoxLayout()

        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Chất lượng nén:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "screen (72dpi - Nén tối đa, chất lượng thấp)",
            "ebook (150dpi - Cân bằng, khuyên dùng)", 
            "printer (300dpi - Chất lượng cao)",
            "prepress (300dpi - Tốt nhất, ít nén)"
        ])
        self.quality_combo.setCurrentIndex(1)
        self.quality_combo.setFixedHeight(35)
        quality_layout.addWidget(self.quality_combo)
        quality_layout.setStretch(1, 1)

        self.btn_compress = QPushButton("🚀 Bắt đầu Nén PDF")
        self.btn_compress.setFixedHeight(45)
        self.btn_compress.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_compress.setStyleSheet("background-color: #2196f3; color: white; border-radius: 5px;")
        self.btn_compress.clicked.connect(self.start_compression)

        config_layout.addLayout(quality_layout)
        config_layout.addSpacing(10)
        config_layout.addWidget(self.btn_compress)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 4. Progress Section
        progress_group = QGroupBox("📊 Tiến trình")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("Sẵn sàng")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Đẩy nội dung lên trên
        layout.addStretch()
        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn File PDF", "", "PDF Files (*.pdf)")
        if files:
            for f in files:
                f = os.path.normpath(f)
                if f not in self.selected_files:
                    self.selected_files.append(f)
            self.update_list_ui()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn Folder chứa PDF")
        if folder:
            added_count = 0
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        full_path = os.path.normpath(os.path.join(root, file))
                        if full_path not in self.selected_files:
                            self.selected_files.append(full_path)
                            added_count += 1
            self.update_list_ui()
            if added_count > 0:
                self.status_label.setText(f"Đã thêm {added_count} file từ folder.")
            else:
                self.status_label.setText("Không tìm thấy file PDF mới nào trong folder.")

    def clear_files(self):
        self.selected_files.clear()
        self.update_list_ui()
        self.status_label.setText("Đã xóa danh sách.")

    def update_list_ui(self):
        self.file_list_widget.clear()
        for f in self.selected_files:
            self.file_list_widget.addItem(f)

    def get_quality_setting(self):
        quality_text = self.quality_combo.currentText()
        if "screen" in quality_text: return "screen"
        if "printer" in quality_text: return "printer"
        if "prepress" in quality_text: return "prepress"
        return "ebook"

    def start_compression(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất một file PDF để nén.")
            return

        quality = self.get_quality_setting()
        
        # Cleanup thread cũ nếu có
        if self.compress_thread is not None:
            self.compress_thread.quit()
            self.compress_thread.wait()
            self.compress_thread = None

        # Lock UI
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Đang khởi tạo quá trình nén...")

        # Truyền output_suffix là '_compress' theo đúng yêu cầu
        self.compress_thread = CompressThread(
            pdf_files=self.selected_files, 
            quality=quality, 
            output_suffix='_compress'
        )
        self.compress_thread.progress.connect(self.update_progress)
        self.compress_thread.error.connect(self.handle_error)
        self.compress_thread.finished.connect(self.compression_finished)
        self.compress_thread.start()

    def update_progress(self, message, percent):
        self.status_label.setText(message)
        self.progress_bar.setValue(percent)

    def handle_error(self, error_msg):
        QMessageBox.critical(self, "Lỗi", error_msg)
        self.status_label.setText("Lỗi xảy ra trong quá trình nén.")
        self._set_ui_enabled(True)
        self.progress_bar.setVisible(False)

    def compression_finished(self, results):
        self.status_label.setText(f"Hoàn tất nén {len(results)} file.")
        self.progress_bar.setValue(100)
        self._set_ui_enabled(True)
        
        # Mở thư mục chứa file đầu tiên (nếu có)
        if results:
            first_dir = os.path.dirname(results[0])
            try:
                os.startfile(first_dir)
            except Exception:
                pass

        QMessageBox.information(
            self, 
            "Hoàn tất", 
            f"✅ Đã nén xong {len(results)} file PDF.\nCác file mới có đuôi '_compress'."
        )

    def _set_ui_enabled(self, enabled):
        self.btn_add_files.setEnabled(enabled)
        self.btn_add_folder.setEnabled(enabled)
        self.btn_clear_list.setEnabled(enabled)
        self.btn_compress.setEnabled(enabled)
        self.quality_combo.setEnabled(enabled)
        self.file_list_widget.setEnabled(enabled)