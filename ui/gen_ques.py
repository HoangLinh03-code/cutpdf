"""
Base GenQues Widget - Giao diện chung cho sinh câu hỏi KHTN và KHXH
Tương thích với kiến trúc CutPdfByDrive hiện tại
"""
import sys
import os
import glob
import threading
import concurrent.futures
import mammoth
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QGroupBox, QCheckBox, QProgressBar, QMessageBox, QListWidget, 
    QFileDialog, QTreeWidget, QTreeWidgetItem, QHeaderView, 
    QTabWidget, QTextEdit, QTreeWidgetItemIterator, QSpinBox, QDialog, QSplitter,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFont
from config.credentials import Config
from ui.groupfiles import main as _smart_group_files

# ============================================================
# CLASS ĐA LUỒNG (WORKER) - ĐÃ TỐI ƯU HÓA
# ============================================================
class TaskInfo:
    """Class lưu thông tin cho từng nhiệm vụ nhỏ"""
    def __init__(self, output_name, pdf_files, task_type, prompt_content):
        self.output_name = output_name
        self.pdf_files = pdf_files
        self.task_type = task_type  # "TN", "DS", hoặc "TLN"
        self.prompt_content = prompt_content

class ProcessingThread(QThread):
    progress = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, selected_items, prompt_paths, project_id, creds, processor_module, max_workers=3):
        super().__init__()
        self.selected_items = selected_items
        self.prompt_paths = prompt_paths
        self.project_id = project_id
        self.creds = creds
        self.processor_module = processor_module # Module xử lý (KHXH hoặc KHTN)
        self.max_workers = max_workers
        self.generated_files = []
        self.is_running = True
        self.lock = threading.Lock()

    def run(self):
        """Logic chạy chính: Tách nhỏ tác vụ để chạy song song"""
        import time

        self.progress.emit("⚙️ Đang chuẩn bị dữ liệu và đọc Prompt...")

        # 1. Đọc Prompt
        prompts = {}
        for key in ["trac_nghiem", "dung_sai", "tra_loi_ngan", "tu_luan"]:
            if key in self.prompt_paths and self.prompt_paths[key]:
                try:
                    with open(self.prompt_paths[key], "r", encoding="utf-8") as f:
                        prompts[key] = f.read()
                except Exception as e:
                    self.error_signal.emit(f"Lỗi đọc prompt {key}: {e}")
                    return

        # 2. Tạo danh sách công việc
        all_tasks = []
        for output_name, pdf_files in self.selected_items.items():
            if "trac_nghiem" in prompts:
                all_tasks.append(TaskInfo(output_name, pdf_files, "TN", prompts["trac_nghiem"]))
            if "dung_sai" in prompts:
                all_tasks.append(TaskInfo(output_name, pdf_files, "DS", prompts["dung_sai"]))
            if "tra_loi_ngan" in prompts:
                all_tasks.append(TaskInfo(output_name, pdf_files, "TLN", prompts["tra_loi_ngan"]))
            if "tu_luan" in prompts:
                all_tasks.append(TaskInfo(output_name, pdf_files, "TL", prompts["tu_luan"]))

        total_tasks = len(all_tasks)
        if total_tasks == 0:
            self.finished.emit([])
            return

        self.progress.emit(f"🚀 Bắt đầu xử lý {total_tasks} tác vụ với module: {self.processor_module.__name__}...")
        self.progress_update.emit(0, total_tasks)

        completed_count = 0
        failed_count = 0

        # 3. Thực thi song song
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {}
            for task in all_tasks:
                if not self.is_running: break
                future = executor.submit(self._process_worker, task)
                future_to_task[future] = task
                time.sleep(5)  # Tránh spam API

            for future in concurrent.futures.as_completed(future_to_task):
                if not self.is_running: break
                task = future_to_task[future]
                try:
                    result_path, error_msg = future.result()
                    with self.lock:
                        completed_count += 1
                        if result_path:
                            self.generated_files.append(result_path)
                            status_icon = "✅"
                            msg = f"Xong {task.output_name} ({task.task_type})"
                        else:
                            failed_count += 1
                            status_icon = "⚠️"
                            msg = f"Lỗi {task.output_name}: {error_msg}"
                    
                    self.progress.emit(f"{status_icon} [{completed_count}/{total_tasks}] {msg}")
                    self.progress_update.emit(completed_count, total_tasks)

                except Exception as e:
                    completed_count += 1
                    self.progress.emit(f"❌ Exception tại {task.output_name}: {str(e)}")
                    self.progress_update.emit(completed_count, total_tasks)

        self.finished.emit(self.generated_files)

    def _process_worker(self, task):
        """Gọi hàm xử lý từ module được truyền vào"""
        MODEL_NAME = "gemini-3-pro-preview"
        
        try:
            if task.task_type == "TN":
                func = getattr(self.processor_module, 'response2docx_json', None)
                suffix = "_TN"
            elif task.task_type == "DS":
                func = getattr(self.processor_module, 'response2docx_dung_sai_json', None)
                suffix = "_DS"
            elif task.task_type == "TLN":
                func = getattr(self.processor_module, 'response2docx_tra_loi_ngan_json', None)
                suffix = "_TLN"
            else: # [THÊM MỚI] Tự luận
                func = getattr(self.processor_module, 'response2docx_tu_luan_json', None)
                suffix = "_TL"

            if not func:
                return None, f"Module không hỗ trợ loại đề {task.task_type}"

            output_filename = f"{task.output_name}{suffix}"
            
            docx_path = func(
                task.pdf_files,
                task.prompt_content,
                output_filename,
                self.project_id,
                self.creds,
                MODEL_NAME, 
                batch_name=task.output_name
            )
            
            if docx_path and os.path.exists(docx_path):
                return docx_path, None
            else:
                return None, "Không tạo được file DOCX"

        except Exception as e:
            return None, str(e)

    def stop(self):
        self.is_running = False

# ============================================================
# CLASS GIAO DIỆN CHÍNH (BASE WIDGET)
# ============================================================
class GenQuesWidget(QWidget):
    # Signals để giao tiếp với main window
    status_changed = pyqtSignal(str, str)  # message, type
    progress_changed = pyqtSignal(int, bool)  # value, visible
    file_count_changed = pyqtSignal(int)  # count
    
    def __init__(self, prompt_folder_name, processor_module, widget_title="GenQues"):
        super().__init__()
        self.processor_module = processor_module
        self.widget_title = widget_title
        self.generated_files = []
        self.processing_thread = None
        self.settings = QSettings("CutPDF_Tool", "GenQues_Module")
        
        # Thiết lập đường dẫn Prompt
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.prompt_base_dir = os.path.join(current_dir, "modules", prompt_folder_name)
        
        self.default_prompt_tn = os.path.join(self.prompt_base_dir, "promptTest.txt")
        self.default_prompt_ds = os.path.join(self.prompt_base_dir, "promptTestDS.txt")
        self.default_prompt_tln = os.path.join(self.prompt_base_dir, "promptTestTLN.txt")
        self.default_prompt_tl = os.path.join(self.prompt_base_dir, "promptTuLuan   .txt")

        # Load nội dung prompt
        self.load_default_prompts()
        self.current_prompt_tn = self.default_prompt_tn
        self.current_prompt_ds = self.default_prompt_ds
        self.current_prompt_tln = self.default_prompt_tln
        self.current_prompt_tl = self.default_prompt_tl

        # Setup Credentials
        self.setup_credentials()
        
        # Setup UI
        self.setup_theme()
        self.init_ui()

    def setup_theme(self):
        self.setStyleSheet("""
            QWidget { 
                font-family: 'Segoe UI', sans-serif; 
                font-size: 14px; 
                background-color: #f5f7fa;
            }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #e0e0e0; 
                border-radius: 8px; 
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 15px; 
                padding: 0 5px;
                color: #1976D2;
                font-size: 15px;
            }
            QPushButton { 
                padding: 8px 15px; 
                border-radius: 5px; 
                border: 1px solid #ccc; 
                background: #fff;
                font-weight: 600;
            }
            QPushButton:hover { 
                background: #e3f2fd;
                border-color: #2196F3;
            }
            QPushButton#ProcessBtn { 
                background-color: #2e7d32; 
                color: white; 
                border: none; 
                font-weight: bold; 
                padding: 12px;
                font-size: 16px;
            }
            QPushButton#ProcessBtn:hover { 
                background-color: #1b5e20; 
            }
            QPushButton#ProcessBtn:disabled { 
                background-color: #a5d6a7; 
            }
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f9fbfd;
            }
            QTreeWidget::item {
                height: 40px;
                padding: 2px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:hover {
                background-color: #e3f2fd;
            }
            QTreeWidget::item:selected {
                background-color: #bbdefb;
            }
        """)

    def setup_credentials(self):
        try:
            self.project_id = Config.GOOGLE_PROJECT_ID
            self.credentials = Config.get_google_credentials()
        except Exception:
            self.project_id = "unknown"
            self.credentials = None

    def load_default_prompts(self):
        self.prompt_tn_content = ""
        self.prompt_ds_content = ""
        self.prompt_tln_content = ""
        self.prompt_tl_content = ""
        def get_valid_path(setting_key, default_path):
            # Lấy đường dẫn đã lưu, nếu không có thì dùng default
            saved_path = self.settings.value(setting_key, default_path, type=str)
            # Kiểm tra xem file đó còn tồn tại không
            if os.path.exists(saved_path):
                return saved_path
            return default_path
        def read_safe(path):
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f: 
                    return f.read()
            return ""
        self.current_prompt_tn = get_valid_path("path_prompt_tn", self.default_prompt_tn)
        self.current_prompt_ds = get_valid_path("path_prompt_ds", self.default_prompt_ds)
        self.current_prompt_tln = get_valid_path("path_prompt_tln", self.default_prompt_tln)
        self.current_prompt_tl = get_valid_path("path_prompt_tl", self.default_prompt_tl)
        
        self.prompt_tn_content = read_safe(self.current_prompt_tn)
        self.prompt_ds_content = read_safe(self.current_prompt_ds)
        self.prompt_tln_content = read_safe(self.current_prompt_tln)
        self.prompt_tl_content = read_safe(self.current_prompt_tl)
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header
        header_label = QLabel(f"📝 {self.widget_title.upper()}")
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
        main_layout.addWidget(header_label)
        
        self.tab_widget = QTabWidget()

        # TAB 1: CẤU HÌNH & XỬ LÝ
        proc_tab = QWidget()
        tab_layout_root = QVBoxLayout(proc_tab)
        tab_layout_root.setContentsMargins(0, 0, 0, 0)

        # 2. Tạo vùng cuộn (ScrollArea)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True) # Cho phép nội dung co giãn
        scroll_area.setFrameShape(QFrame.NoFrame) # Bỏ viền xấu

        # 3. Tạo Widget chứa nội dung (Container)
        content_container = QWidget()
        
        # 4. Gắn layout cũ (proc_layout) vào Container này thay vì proc_tab
        proc_layout = QVBoxLayout(content_container) 
        proc_layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. Nguồn tài liệu
        file_group = QGroupBox("1. Chọn Tài Liệu PDF (đã cắt)")
        file_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_add_file = QPushButton("📄 Thêm File")
        self.btn_add_folder = QPushButton("📁 Thêm Folder")
        self.btn_select_all = QPushButton("☑️ Chọn hết")
        self.btn_deselect_all = QPushButton("☐ Bỏ chọn")
        self.btn_remove = QPushButton("❌ Xóa mục chọn")
        self.btn_clear = QPushButton("🗑️ Xóa List")
        
        self.btn_add_file.clicked.connect(self.add_pdf_files)
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_select_all.clicked.connect(self.select_all_items)
        self.btn_deselect_all.clicked.connect(self.deselect_all_items)
        self.btn_remove.clicked.connect(self.remove_selected_items)
        self.btn_clear.clicked.connect(lambda: self.file_tree.clear() or self.update_file_count())
        
        btn_layout.addWidget(self.btn_add_file)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addWidget(self.btn_deselect_all)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear)
        
        self.just_checked = False
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Tên File", "Đường dẫn"])
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setIndentation(20)
        self.file_tree.itemChanged.connect(self.handle_item_check_changed)
        self.file_tree.itemClicked.connect(self.handle_smart_click)
        
        header = self.file_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.file_tree.setColumnWidth(0, 450)
        
        self.file_count_lbl = QLabel("Chưa chọn file nào")
        self.file_count_lbl.setAlignment(Qt.AlignRight)
        
        file_layout.addLayout(btn_layout)
        file_layout.addWidget(self.file_tree)
        file_layout.addWidget(self.file_count_lbl)
        file_group.setLayout(file_layout)

        # 2. Cấu hình Prompt
        conf_group = QGroupBox("2. Cấu Hình Loại Đề")
        conf_layout = QVBoxLayout()
        
        # Trắc nghiệm
        tn_container = QWidget()
        tn_layout = QHBoxLayout(tn_container)
        tn_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chk_tn = QCheckBox("Trắc nghiệm (4 đáp án)")
        self.chk_tn.setChecked(True)
        self.chk_tn.stateChanged.connect(self.update_process_button_state)
        
        self.prompt_tn_label = QLabel(os.path.basename(self.current_prompt_tn))
        self.prompt_tn_label.setStyleSheet("color: #666; font-style: italic;")
        
        self.btn_select_prompt_tn = QPushButton("📂 Chọn")
        self.btn_select_prompt_tn.setFixedWidth(80)
        self.btn_select_prompt_tn.clicked.connect(lambda: self.select_prompt_file("trac_nghiem"))
        
        self.btn_edit_tn = QPushButton("✏️ Sửa")
        self.btn_edit_tn.setFixedWidth(70)
        self.btn_edit_tn.clicked.connect(lambda: self.edit_prompt("trac_nghiem"))
        
        tn_layout.addWidget(self.chk_tn, 2)
        tn_layout.addWidget(QLabel("Prompt:"), 0)
        tn_layout.addWidget(self.prompt_tn_label, 3)
        tn_layout.addWidget(self.btn_select_prompt_tn)
        tn_layout.addWidget(self.btn_edit_tn)

        # Đúng sai
        ds_container = QWidget()
        ds_layout = QHBoxLayout(ds_container)
        ds_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chk_ds = QCheckBox("Đúng / Sai")
        self.chk_ds.setChecked(True)
        self.chk_ds.stateChanged.connect(self.update_process_button_state)
        
        self.prompt_ds_label = QLabel(os.path.basename(self.current_prompt_ds))
        self.prompt_ds_label.setStyleSheet("color: #666; font-style: italic;")
        
        self.btn_select_prompt_ds = QPushButton("📂 Chọn")
        self.btn_select_prompt_ds.setFixedWidth(80)
        self.btn_select_prompt_ds.clicked.connect(lambda: self.select_prompt_file("dung_sai"))
        
        self.btn_edit_ds = QPushButton("✏️ Sửa")
        self.btn_edit_ds.setFixedWidth(70)
        self.btn_edit_ds.clicked.connect(lambda: self.edit_prompt("dung_sai"))
        
        ds_layout.addWidget(self.chk_ds, 2)
        ds_layout.addWidget(QLabel("Prompt:"), 0)
        ds_layout.addWidget(self.prompt_ds_label, 3)
        ds_layout.addWidget(self.btn_select_prompt_ds)
        ds_layout.addWidget(self.btn_edit_ds)

        # Trả lời ngắn
        tln_container = QWidget()
        tln_layout = QHBoxLayout(tln_container)
        tln_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chk_tln = QCheckBox("Trả lời ngắn")
        self.chk_tln.setChecked(True)
        self.chk_tln.stateChanged.connect(self.update_process_button_state)
        
        self.prompt_tln_label = QLabel(os.path.basename(self.current_prompt_tln))
        self.prompt_tln_label.setStyleSheet("color: #666; font-style: italic;")
        
        self.btn_select_prompt_tln = QPushButton("📂 Chọn")
        self.btn_select_prompt_tln.setFixedWidth(80)
        self.btn_select_prompt_tln.clicked.connect(lambda: self.select_prompt_file("tra_loi_ngan"))
        
        self.btn_edit_tln = QPushButton("✏️ Sửa")
        self.btn_edit_tln.setFixedWidth(70)
        self.btn_edit_tln.clicked.connect(lambda: self.edit_prompt("tra_loi_ngan"))
        
        tln_layout.addWidget(self.chk_tln, 2)
        tln_layout.addWidget(QLabel("Prompt:"), 0)
        tln_layout.addWidget(self.prompt_tln_label, 3)
        tln_layout.addWidget(self.btn_select_prompt_tln)
        tln_layout.addWidget(self.btn_edit_tln)
        
        tl_container = QWidget()
        tl_layout = QHBoxLayout(tl_container)
        tl_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chk_tl = QCheckBox("Tự luận")
        self.chk_tl.setChecked(True) 
        self.chk_tl.stateChanged.connect(self.update_process_button_state)
        
        self.prompt_tl_label = QLabel(os.path.basename(self.current_prompt_tl))
        self.prompt_tl_label.setStyleSheet("color: #666; font-style: italic;")
        
        self.btn_select_prompt_tl = QPushButton("📂 Chọn")
        self.btn_select_prompt_tl.setFixedWidth(80)
        self.btn_select_prompt_tl.clicked.connect(lambda: self.select_prompt_file("tu_luan"))
        
        self.btn_edit_tl = QPushButton("✏️ Sửa")
        self.btn_edit_tl.setFixedWidth(70)
        self.btn_edit_tl.clicked.connect(lambda: self.edit_prompt("tu_luan"))
        
        tl_layout.addWidget(self.chk_tl, 2)
        tl_layout.addWidget(QLabel("Prompt:"), 0)
        tl_layout.addWidget(self.prompt_tl_label, 3)
        tl_layout.addWidget(self.btn_select_prompt_tl)
        tl_layout.addWidget(self.btn_edit_tl)

        conf_layout.addWidget(tn_container)
        conf_layout.addWidget(ds_container)
        conf_layout.addWidget(tln_container)
        conf_layout.addWidget(tl_container)
        conf_group.setLayout(conf_layout)

        # 3. Action
        act_layout = QVBoxLayout()
        
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("Số bài xử lí cùng lúc:"))
        self.spin_worker = QSpinBox()
        self.spin_worker.setRange(1, 50)
        self.spin_worker.setValue(3)
        self.spin_worker.setFixedWidth(60)
        thread_layout.addWidget(self.spin_worker)
        thread_layout.addStretch()
        
        self.btn_process = QPushButton("🚀 BẮT ĐẦU SINH CÂU HỎI")
        self.btn_process.setObjectName("ProcessBtn")
        self.btn_process.setMinimumHeight(50)
        self.btn_process.clicked.connect(self.process_files)
        
        act_layout.addLayout(thread_layout)
        act_layout.addWidget(self.btn_process)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v/%m (%p%)")
        
        self.status_lbl = QLabel("Sẵn sàng")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("font-weight: bold; color: #555; min-height: 40px;")
        
        act_layout.addWidget(self.progress_bar)
        act_layout.addWidget(self.status_lbl)

        proc_layout.addWidget(file_group, 5)
        proc_layout.addWidget(conf_group, 3)
        proc_layout.addLayout(act_layout, 1)
        scroll_area.setWidget(content_container)
            
            # Đưa vùng cuộn vào layout của Tab
        tab_layout_root.addWidget(scroll_area)

        # TAB 2: KẾT QUẢ
        res_tab = QWidget()
        res_layout = QHBoxLayout()
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        lbl_result = QLabel("📂 Danh sách đã tạo")
        lbl_result.setStyleSheet("font-weight: bold; color: #2E7D32; padding: 5px;")
        
        self.res_list = QListWidget()
        self.res_list.itemClicked.connect(self.preview_docx)
        
        left_layout.addWidget(lbl_result)
        left_layout.addWidget(self.res_list)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        preview_header = QHBoxLayout()
        lbl_preview = QLabel("📋 Xem trước tài liệu")
        lbl_preview.setStyleSheet("font-weight: bold; color: #1565C0; padding: 5px;")
        
        self.btn_open_word = QPushButton("↗️ Mở bằng Word/WPS")
        self.btn_open_word.setFixedSize(180, 35)
        self.btn_open_word.clicked.connect(self.open_word)
        self.btn_open_word.setEnabled(False)
        
        preview_header.addWidget(lbl_preview)
        preview_header.addStretch()
        preview_header.addWidget(self.btn_open_word)
        
        self.web_view = QWebEngineView()
        
        right_layout.addLayout(preview_header)
        right_layout.addWidget(self.web_view)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 9)

        res_layout.addWidget(splitter)
        res_tab.setLayout(res_layout)

        self.tab_widget.addTab(proc_tab, "⚙️ Cấu hình & Chạy")
        self.tab_widget.addTab(res_tab, "📄 Kết quả")
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
        
        self.update_process_button_state()

    # --- LOGIC QUẢN LÝ FILE ---
    def add_pdf_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn PDF", "", "PDF Files (*.pdf)")
        if files:
            for f in files:
                item = QTreeWidgetItem(self.file_tree)
                item.setText(0, os.path.basename(f))
                item.setText(1, f)
                item.setCheckState(0, Qt.Checked)
                item.setData(0, Qt.UserRole, "file")
            self.update_file_count()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục")
        if folder:
            self.add_folder_to_tree(folder, self.file_tree)
            self.update_file_count()

    def add_folder_to_tree(self, folder_path, parent_item, is_root=True):
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, f"📁 {os.path.basename(folder_path)}")
        folder_item.setText(1, folder_path)
        folder_item.setCheckState(0, Qt.Checked)
        folder_item.setData(0, Qt.UserRole, "folder")
        
        pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
        for pdf_file in sorted(pdf_files):
            file_item = QTreeWidgetItem(folder_item)
            file_item.setText(0, os.path.basename(pdf_file))
            file_item.setText(1, pdf_file)
            file_item.setCheckState(0, Qt.Checked)
            file_item.setData(0, Qt.UserRole, "file")
        
        for name in sorted(os.listdir(folder_path)):
            subfolder_path = os.path.join(folder_path, name)
            if os.path.isdir(subfolder_path):
                self.add_folder_to_tree(subfolder_path, folder_item, is_root=False)
        
        if is_root: 
            folder_item.setExpanded(True)

    def handle_item_check_changed(self, item, column):
        """Xử lý sự kiện khi user tick vào checkbox"""
        self.just_checked = True
        if column != 0: return

        self.file_tree.blockSignals(True)
        
        try:
            check_state = item.checkState(0)
            self.update_children_check_state(item, check_state)
            self.update_parent_check_state(item)
            self.update_file_count()
        except Exception as e:
            print(f"Error in handle_item_check_changed: {e}")
        finally:
            self.file_tree.blockSignals(False)

    def handle_smart_click(self, item, column):
        """Logic thông minh: Bấm vào chữ = Tick"""
        if self.just_checked:
            self.just_checked = False
            return

        self.file_tree.blockSignals(True)
        try:
            current_state = item.checkState(0)
            new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
            item.setCheckState(0, new_state)
            
            self.handle_item_check_changed(item, 0)
            self.just_checked = False 
        finally:
            self.file_tree.blockSignals(False)
        
        self.update_file_count()
    
    def update_children_check_state(self, parent_item, check_state):
        """Cập nhật trạng thái con"""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child.setCheckState(0, check_state)
            if child.childCount() > 0:
                self.update_children_check_state(child, check_state)

    def update_parent_check_state(self, item):
        """Cập nhật trạng thái cha"""
        parent = item.parent()
        if parent is None: return
        
        checked_count = 0
        total_count = parent.childCount()
        
        for i in range(total_count):
            child = parent.child(i)
            if child.checkState(0) == Qt.Checked: 
                checked_count += 1
            elif child.checkState(0) == Qt.PartiallyChecked:
                parent.setCheckState(0, Qt.PartiallyChecked)
                self.update_parent_check_state(parent)
                return
        
        if checked_count == 0: 
            parent.setCheckState(0, Qt.Unchecked)
        elif checked_count == total_count: 
            parent.setCheckState(0, Qt.Checked)
        else: 
            parent.setCheckState(0, Qt.PartiallyChecked)
        
        self.update_parent_check_state(parent)

    def select_all_items(self):
        """Chọn tất cả items"""
        iterator = QTreeWidgetItemIterator(self.file_tree)
        while iterator.value():
            item = iterator.value()
            item.setCheckState(0, Qt.Checked)
            iterator += 1

    def deselect_all_items(self):
        """Bỏ chọn tất cả items"""
        iterator = QTreeWidgetItemIterator(self.file_tree)
        while iterator.value():
            item = iterator.value()
            item.setCheckState(0, Qt.Unchecked)
            iterator += 1

    def remove_selected_items(self):
        """Xóa các mục được tick"""
        checked_items = []
        iterator = QTreeWidgetItemIterator(self.file_tree)
        while iterator.value():
            item = iterator.value()
            if item.checkState(0) == Qt.Checked:
                checked_items.append(item)
            iterator += 1
            
        if not checked_items:
            QMessageBox.information(self, "Thông báo", "Vui lòng tick chọn (✓) vào các mục cần xóa!")
            return

        confirm = QMessageBox.question(
            self, "Xác nhận", 
            f"Bạn có chắc muốn xóa {len(checked_items)} mục đã chọn?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return

        items_to_delete = []
        for item in checked_items:
            parent = item.parent()
            if parent is None or parent.checkState(0) != Qt.Checked:
                items_to_delete.append(item)

        root = self.file_tree.invisibleRootItem()
        for item in items_to_delete:
            (item.parent() or root).removeChild(item)

        self.update_file_count()

    def update_file_count(self):
        """Cập nhật số lượng file"""
        total_files = 0
        total_folders = 0
        iterator = QTreeWidgetItemIterator(self.file_tree)
        while iterator.value():
            item = iterator.value()
            item_type = item.data(0, Qt.UserRole)
            if item_type == "file": total_files += 1
            elif item_type == "folder": total_folders += 1
            iterator += 1
        
        if total_files == 0 and total_folders == 0:
            self.file_count_lbl.setText("<i>Chưa có tài liệu nào được chọn</i>")
        else:
            text = f"📊 Tổng: <b>{total_folders}</b> folder, <b>{total_files}</b> file PDF"
            self.file_count_lbl.setText(text)
        
        self.emit_file_count(total_files)

    def get_selected_files(self):
        """Lấy danh sách items và gom nhóm thông minh"""
        all_checked_pdfs = []

        def traverse(item):
            if item.checkState(0) == Qt.Unchecked: return
            item_type = item.data(0, Qt.UserRole)
            
            if item_type == "file" and item.checkState(0) == Qt.Checked:
                all_checked_pdfs.append(item.text(1))
            elif item_type == "folder":
                for i in range(item.childCount()):
                    traverse(item.child(i))

        root = self.file_tree.invisibleRootItem()
        for i in range(root.childCount()):
            traverse(root.child(i))
            
        all_checked_pdfs = sorted(list(set(all_checked_pdfs)))
        
        if not all_checked_pdfs:
            return {}

        return _smart_group_files(all_checked_pdfs)

    # def _smart_group_files(self, file_paths):
    #     """Gom nhóm thông minh dựa trên tên file"""
    #     groups = {}
    #     pending_files = sorted(file_paths)

    #     distinct_pattern = r"(?i)(?:chủ đề|bài|chương|phần|unit|chapter|topic|tuần|tiết|vol|tập)\s*[\d]+"

    #     def clean_name_for_compare(name):
    #         name = os.path.splitext(name)[0].lower()
    #         name = re.sub(r'\(\d+.*?\)', '', name)
    #         name = re.sub(r'[_\-\(\)\[\]]', ' ', name)
    #         name = re.sub(r'\b(kntt|sgv|cd|sbt|sgk|hdtn|hoat dong trai nghiem)\b', '', name)
    #         return " ".join(name.split())

    #     while pending_files:
    #         seed = pending_files.pop(0)
    #         seed_name = os.path.basename(seed)
    #         seed_base = os.path.splitext(seed_name)[0]
            
    #         seed_numbers = re.findall(distinct_pattern, seed_base)
    #         seed_clean = clean_name_for_compare(seed_name)

    #         current_group = [seed]
            
    #         i = 0
    #         while i < len(pending_files):
    #             candidate = pending_files[i]
    #             cand_name = os.path.basename(candidate)
    #             cand_base = os.path.splitext(cand_name)[0]
                
    #             cand_numbers = re.findall(distinct_pattern, cand_base)
    #             cand_clean = clean_name_for_compare(cand_name)

    #             should_merge = False
                
    #             if seed_numbers and cand_numbers:
    #                 last_seed_id = seed_numbers[-1].lower().replace(" ", "")
    #                 last_cand_id = cand_numbers[-1].lower().replace(" ", "")
    #                 if last_seed_id == last_cand_id:
    #                     should_merge = True

    #             if not should_merge:
    #                 suffix_len = min(len(seed_clean), len(cand_clean), 20)
    #                 if suffix_len > 5:
    #                     if seed_clean[-suffix_len:] == cand_clean[-suffix_len:]:
    #                         should_merge = True

    #             if not should_merge:
    #                 import difflib
    #                 matcher = difflib.SequenceMatcher(None, seed_clean, cand_clean)
    #                 if matcher.ratio() > 0.8: 
    #                     should_merge = True
                    
    #                 if os.path.dirname(seed) == os.path.dirname(candidate):
    #                     if matcher.ratio() > 0.6:
    #                         should_merge = True

    #             if should_merge:
    #                 current_group.append(candidate)
    #                 pending_files.pop(i)
    #             else:
    #                 i += 1
            
    #         if len(current_group) > 1:
    #             folder_path = os.path.dirname(current_group[0])
    #             folder_name = os.path.basename(folder_path)
    #             is_same_folder = all(os.path.dirname(f) == folder_path for f in current_group)
                
    #             if is_same_folder:
    #                 group_name = folder_name
    #             elif seed_numbers:
    #                 match = re.search(distinct_pattern, seed_base)
    #                 if match:
    #                     # Cắt chuỗi từ vị trí tìm thấy đến hết
    #                     # Ví dụ: "SBT_Hoa_10_Bài 3. Cấu trúc..." -> "Bài 3. Cấu trúc..."
    #                     group_name = seed_base[match.start():].strip(" _-.")
    #                 else:
    #                     # Fallback nếu không tìm thấy (giữ logic cũ ở mức tối thiểu)
    #                     group_name = seed_numbers[-1].title()
    #                 if len(group_name) < 10:
    #                     parent_name = os.path.basename(folder_path)
    #                     if group_name.lower() not in parent_name.lower():
    #                         group_name = f"{parent_name}_{group_name}"
    #                     else:
    #                         group_name = parent_name
    #             else:
    #                 name1 = os.path.splitext(os.path.basename(current_group[0]))[0]
    #                 name2 = os.path.splitext(os.path.basename(current_group[1]))[0]
    #                 common = os.path.commonprefix([name1, name2]).strip(" .-_")
    #                 group_name = common if len(common) > 5 else folder_name
    #         else:
    #             group_name = seed_base

    #         base_key = group_name
    #         counter = 1
    #         while group_name in groups:
    #             group_name = f"{base_key}_{counter}"
    #             counter += 1

    #         groups[group_name] = current_group
            
    #     return groups

    # --- LOGIC PROMPT ---
    def select_prompt_file(self, prompt_type):
        """Chọn file prompt tùy chỉnh"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Chọn file prompt cho {prompt_type}", 
            "", 
            "Text Files (*.txt)"
        )
        if isinstance(file_path, list): 
            if not file_path: return
            file_path = file_path[0]
        elif isinstance(file_path, tuple):
             file_path = file_path[0]
        if file_path:
            try:
                # Đọc nội dung để lưu vào bộ nhớ
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if prompt_type == "trac_nghiem":
                    self.prompt_tn_content = content
                    self.current_prompt_tn = file_path 
                    self.prompt_tn_label.setText(os.path.basename(file_path))
                    self.settings.setValue("path_prompt_tn", file_path)
                elif prompt_type == "dung_sai":
                    self.prompt_ds_content = content
                    self.current_prompt_ds = file_path 
                    self.prompt_ds_label.setText(os.path.basename(file_path))
                    self.settings.setValue("path_prompt_ds", file_path)
                elif prompt_type == "tra_loi_ngan":
                    self.prompt_tln_content = content
                    self.current_prompt_tln = file_path
                    self.prompt_tln_label.setText(os.path.basename(file_path))
                    self.settings.setValue("path_prompt_tln", file_path)
                elif prompt_type == "tu_luan":
                    self.prompt_tl_content = content
                    self.current_prompt_tl = file_path
                    self.prompt_tl_label.setText(os.path.basename(file_path))
                    self.settings.setValue("path_prompt_tl", file_path)
                
                self.emit_status(f"Đã chọn prompt: {os.path.basename(file_path)}", "success")
                
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể đọc file: {str(e)}")
    
    def edit_prompt(self, p_type):
        dialog = QDialog(self)
        title_map = {
            'trac_nghiem': 'Trắc nghiệm',
            'dung_sai': 'Đúng/Sai',
            'tra_loi_ngan': 'Trả lời ngắn',
            'tu_luan': 'Tự luận'
        }
        dialog.setWindowTitle(f"Sửa Prompt - {title_map.get(p_type, p_type)}")
        dialog.resize(750, 600)
        
        layout = QVBoxLayout()
        
        label = QLabel(f"📝 Chỉnh sửa nội dung prompt ({title_map.get(p_type, p_type)}):")
        label.setFont(QFont("Arial", 10, QFont.Bold))
        
        txt_edit = QTextEdit()
        txt_edit.setFont(QFont("Consolas", 10))
        
        content = ""
        if p_type == "trac_nghiem": content = self.prompt_tn_content
        elif p_type == "dung_sai": content = self.prompt_ds_content
        elif p_type == "tra_loi_ngan": content = self.prompt_tln_content
        elif p_type == "tu_luan": content = self.prompt_tl_content
        
        txt_edit.setPlainText(content)
        
        btn_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Lưu & Ghi File")
        btn_save.setFixedSize(120, 35)
        btn_save.setStyleSheet("background-color: #4CAF50; color: white;")
        
        btn_cancel = QPushButton("❌ Hủy")
        btn_cancel.setFixedSize(100, 35)
        btn_cancel.setStyleSheet("background-color: #f44336; color: white;")
        
        btn_reset = QPushButton("🔄 Reset về mặc định")
        btn_reset.setFixedSize(150, 35)
        btn_reset.setStyleSheet("background-color: #ff9800; color: white;")
        
        btn_layout.addWidget(btn_reset)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        layout.addWidget(label)
        layout.addWidget(txt_edit)
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)

        def save_prompt():
            new_content = txt_edit.toPlainText()
            file_path = ""
            
            if p_type == "trac_nghiem":
                self.prompt_tn_content = new_content
                file_path = self.current_prompt_tn
                self.prompt_tn_label.setText("✏️ " + os.path.basename(file_path) + " (đã chỉnh sửa)")
            elif p_type == "dung_sai":
                self.prompt_ds_content = new_content
                file_path = self.current_prompt_ds
                self.prompt_ds_label.setText("✏️ " + os.path.basename(file_path) + " (đã chỉnh sửa)")
            elif p_type == "tra_loi_ngan":
                self.prompt_tln_content = new_content
                file_path = self.current_prompt_tln
                self.prompt_tln_label.setText("✏️ " + os.path.basename(file_path) + " (đã chỉnh sửa)")
            elif p_type == "tu_luan":
                self.prompt_tl_content = new_content
                file_path = self.current_prompt_tl
                self.prompt_tl_label.setText("✏️ " + os.path.basename(file_path) + " (đã chỉnh sửa)")

            try:
                if file_path:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    QMessageBox.information(dialog, "Thành công", f"Đã lưu thay đổi vào file:\n{os.path.basename(file_path)}")
                    self.emit_status(f"Đã lưu prompt: {os.path.basename(file_path)}", "success")
                else:
                    QMessageBox.warning(dialog, "Cảnh báo", "Không xác định được đường dẫn file để lưu!")
            except Exception as e:
                QMessageBox.critical(dialog, "Lỗi Ghi File", f"Không thể ghi file txt:\n{str(e)}")
                return

            dialog.accept()
        
        def reset_prompt():
            default_files = {
                'trac_nghiem': self.default_prompt_tn,
                'dung_sai': self.default_prompt_ds,
                'tra_loi_ngan': self.default_prompt_tln,
                'tu_luan': self.default_prompt_tl
            }
            setting_keys = {
                'trac_nghiem': 'path_prompt_tn',
                'dung_sai': 'path_prompt_ds',
                'tra_loi_ngan': 'path_prompt_tln',
                'tu_luan': 'path_prompt_tl'
            }
            default_file = default_files.get(p_type, self.default_prompt_tn)
            
            if os.path.isfile(default_file):
                try:
                    with open(default_file, "r", encoding="utf-8") as f:
                        default_content = f.read()
                    txt_edit.setPlainText(default_content)
                    
                    # Reset current path & Label
                    if p_type == "trac_nghiem":
                        self.current_prompt_tn = default_file
                        self.prompt_tn_label.setText(os.path.basename(default_file))
                    elif p_type == "dung_sai":
                        self.current_prompt_ds = default_file
                        self.prompt_ds_label.setText(os.path.basename(default_file))
                    elif p_type == "tra_loi_ngan":
                        self.current_prompt_tln = default_file
                        self.prompt_tln_label.setText(os.path.basename(default_file))
                    elif p_type == "tu_luan":
                        self.current_prompt_tl = default_file
                        self.prompt_tl_label.setText(os.path.basename(default_file))
                    
                    # --- [THÊM] Xóa config đã lưu để quay về mặc định ---
                    self.settings.remove(setting_keys.get(p_type)) 
                    
                    QMessageBox.information(dialog, "Thành công", "Đã reset về prompt mặc định gốc!")
                    self.emit_status(f"Đã reset prompt về mặc định", "info")
                except Exception as e:
                    QMessageBox.warning(dialog, "Lỗi", f"Không thể load prompt: {str(e)}")
        
        btn_save.clicked.connect(save_prompt)
        btn_cancel.clicked.connect(dialog.reject)
        btn_reset.clicked.connect(reset_prompt)
        
        dialog.exec_()

    def update_process_button_state(self):
        """Cập nhật trạng thái button"""
        has_selection = (self.chk_tn.isChecked() or self.chk_ds.isChecked() or self.chk_tln.isChecked() or self.chk_tl.isChecked())
        self.btn_process.setEnabled(has_selection)
        if not has_selection: 
            self.btn_process.setText("⚠️ Vui lòng chọn ít nhất 1 dạng đề")
        else: 
            self.btn_process.setText("BẮT ĐẦU XỬ LÝ")

    # --- LOGIC CHẠY (PROCESS) ---
    def process_files(self):
        # 1. Kiểm tra đã chọn PDF chưa
        selected = self.get_selected_files()
        if not selected:
            QMessageBox.warning(self, "Thiếu dữ liệu", "⚠️ Vui lòng chọn ít nhất 1 file tài liệu PDF!")
            return

        # 2. VALIDATION PROMPT (Bước quan trọng mới thêm vào)
        # Kiểm tra xem các mục được tick có file prompt hợp lệ không
        missing_prompts = []
        prompt_paths = {}

        # Hàm kiểm tra nhanh
        def check_path(is_checked, path, key, label):
            if is_checked:
                # Kiểm tra đường dẫn có trống hoặc file không tồn tại
                if not path or not os.path.exists(path):
                    missing_prompts.append(label)
                else:
                    prompt_paths[key] = path

        check_path(self.chk_tn.isChecked(), self.current_prompt_tn, "trac_nghiem", "Trắc nghiệm")
        check_path(self.chk_ds.isChecked(), self.current_prompt_ds, "dung_sai", "Đúng / Sai")
        check_path(self.chk_tln.isChecked(), self.current_prompt_tln, "tra_loi_ngan", "Trả lời ngắn")
        check_path(self.chk_tl.isChecked(), self.current_prompt_tl, "tu_luan", "Tự luận")

        # Nếu có lỗi thiếu prompt -> Dừng ngay, không cho chạy Thread
        if missing_prompts:
            msg = "⛔ Các loại đề sau chưa có file Prompt hợp lệ (hoặc file không tồn tại):\n\n"
            msg += "\n".join([f"• {name}" for name in missing_prompts])
            msg += "\n\n👉 Vui lòng bấm nút [📂 Chọn] để nạp file prompt txt."
            QMessageBox.critical(self, "Lỗi Prompt", msg)
            return

        # 3. Nếu mọi thứ OK -> Mới bắt đầu khóa nút và chạy Thread
        self.btn_process.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_lbl.setText("⏳ Đang khởi tạo quá trình xử lý đa luồng...")
        
        max_workers = self.spin_worker.value()
        
        self.processing_thread = ProcessingThread(
            selected,
            prompt_paths, # Dict này đảm bảo chỉ chứa các path đã tồn tại
            self.project_id,
            self.credentials,
            self.processor_module,
            max_workers
        )
        
        self.processing_thread.progress.connect(lambda s: self.status_lbl.setText(s))
        self.processing_thread.progress_update.connect(lambda c, t: self.progress_bar.setValue(int(c/t*100) if t else 0))
        self.processing_thread.finished.connect(self.on_finished)
        
        # Thêm xử lý lỗi để mở lại nút nếu Thread chết bất đắc kỳ tử
        def on_thread_error(e):
            QMessageBox.critical(self, "Lỗi xử lý", f"❌ Có lỗi xảy ra trong quá trình chạy:\n{e}")
            self.btn_process.setEnabled(True) # Mở lại nút để user bấm lại
            self.progress_bar.setVisible(False)
            self.status_lbl.setText("Đã dừng do lỗi.")

        self.processing_thread.error_signal.connect(on_thread_error)
        
        self.processing_thread.start()

    def on_finished(self, files):
        self.generated_files = files
        self.res_list.clear()
        for f in files:
            self.res_list.addItem(os.path.basename(f))
        
        self.btn_process.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_lbl.setText(f"Hoàn thành! Tạo được {len(files)} file.")
        self.tab_widget.setCurrentIndex(1)
        
        self.emit_status(f"Completed! Generated {len(files)} files", "success")
        self.emit_file_count(len(files))
        self.emit_progress(100, False)

    # --- LOGIC PREVIEW ---
    def preview_docx(self, item):
        fname = item.text()
        fpath = next((f for f in self.generated_files if os.path.basename(f) == fname), None)
        
        self.btn_open_word.setEnabled(True)
        
        if fpath and os.path.exists(fpath):
            try:
                with open(fpath, "rb") as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    html = f"<html><body>{result.value}</body></html>"
                    self.web_view.setHtml(html)
            except Exception as e:
                self.web_view.setHtml(f"Lỗi đọc file: {e}")
        else:
            self.btn_open_word.setEnabled(False)

    def open_word(self):
        item = self.res_list.currentItem()
        if item:
            fname = item.text()
            fpath = next((f for f in self.generated_files if os.path.basename(f) == fname), None)
            if fpath and os.path.exists(fpath):
                try:
                    os.startfile(fpath)
                except Exception as e:
                    QMessageBox.warning(self, "Lỗi", f"Không thể mở file: {str(e)}")

    # --- EMIT SIGNALS ---
    def emit_status(self, message, status_type="info"):
        self.status_changed.emit(message, status_type)
    
    def emit_progress(self, value, visible=True):
        self.progress_changed.emit(value, visible)
    
    def emit_file_count(self, count):
        self.file_count_changed.emit(count)