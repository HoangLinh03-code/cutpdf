import sys
import os
import glob
import threading
import concurrent.futures
import mammoth
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QGroupBox, QCheckBox, QProgressBar, QMessageBox, QListWidget, 
    QFileDialog, QTreeWidget, QTreeWidgetItem, QHeaderView, 
    QTabWidget, QTextEdit, QTreeWidgetItemIterator, QSpinBox, QDialog, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFont
from google.oauth2 import service_account
from dotenv import load_dotenv

# Import API dùng chung
# Lưu ý: Đảm bảo bạn đã tạo file modules/common/callAPI.py như hướng dẫn trước
try:
    from modules.common.callAPI import VertexClient
except ImportError:
    # Fallback nếu chạy debug lẻ
    pass

# ============================================================
# CLASS ĐA LUỒNG (WORKER) - ĐÃ TỐI ƯU HÓA ĐỂ NHẬN PROCESSOR
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
        self.processor_module = processor_module # <--- Module xử lý (KHXH hoặc KHTN) được truyền vào
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
        for key in ["trac_nghiem", "dung_sai", "tra_loi_ngan"]:
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
            # Task Trắc nghiệm
            if "trac_nghiem" in prompts:
                all_tasks.append(TaskInfo(output_name, pdf_files, "TN", prompts["trac_nghiem"]))
            # Task Đúng/Sai
            if "dung_sai" in prompts:
                all_tasks.append(TaskInfo(output_name, pdf_files, "DS", prompts["dung_sai"]))
            # Task Trả lời ngắn
            if "tra_loi_ngan" in prompts:
                all_tasks.append(TaskInfo(output_name, pdf_files, "TLN", prompts["tra_loi_ngan"]))

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
                time.sleep(0.1) # Tránh spam API

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
        MODEL_NAME = "gemini-1.5-pro" # Cấu hình model chuẩn tại đây
        
        try:
            # Gọi hàm tương ứng trong module processor (KHXH hoặc KHTN)
            # Lưu ý: Các file response2docx.py phải có tên hàm giống nhau
            if task.task_type == "TN":
                func = getattr(self.processor_module, 'response2docx_json', None)
                suffix = "_TN"
            elif task.task_type == "DS":
                func = getattr(self.processor_module, 'response2docx_dung_sai_json', None)
                suffix = "_DS"
            else: # TLN
                func = getattr(self.processor_module, 'response2docx_tra_loi_ngan_json', None)
                suffix = "_TLN"

            if not func:
                return None, f"Module không hỗ trợ loại đề {task.task_type}"

            output_filename = f"{task.output_name}{suffix}"
            
            # Gọi hàm xử lý
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
class BaseGenWidget(QWidget):
    def __init__(self, prompt_folder_name, processor_module):
        super().__init__()
        self.processor_module = processor_module
        self.generated_files = []
        self.processing_thread = None
        
        # Thiết lập đường dẫn Prompt
        # Logic: modules/common/base.py -> modules -> prompt_folder_name
        current_dir = os.path.dirname(os.path.abspath(__file__)) # modules/common
        modules_dir = os.path.dirname(current_dir) # modules
        self.prompt_base_dir = os.path.join(modules_dir, prompt_folder_name)
        
        # Đường dẫn file mặc định
        # Lưu ý: Cần đảm bảo file txt nằm đúng trong modules/khxh/ hoặc modules/khtn/
        self.default_prompt_tn = os.path.join(self.prompt_base_dir, "testTN.txt")
        self.default_prompt_ds = os.path.join(self.prompt_base_dir, "testDS.txt")
        self.default_prompt_tln = os.path.join(self.prompt_base_dir, "testTLN.txt")

        # Load nội dung prompt
        self.load_default_prompts()
        self.current_prompt_tn = self.default_prompt_tn
        self.current_prompt_ds = self.default_prompt_ds
        self.current_prompt_tln = self.default_prompt_tln

        # Setup Credentials
        self.setup_credentials()
        
        # Setup UI
        self.setup_theme()
        self.init_ui()

    def setup_theme(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; }
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QPushButton { padding: 5px 15px; border-radius: 3px; border: 1px solid #bbb; background: #f9f9f9; }
            QPushButton:hover { background: #e0e0e0; }
            QPushButton#ProcessBtn { background-color: #2ecc71; color: white; border: none; font-weight: bold; padding: 10px; }
            QPushButton#ProcessBtn:hover { background-color: #27ae60; }
            QPushButton#ProcessBtn:disabled { background-color: #95a5a6; }
        """)

    def setup_credentials(self):
        # Load từ .env.gen đã được load ở callAPI
        # Tuy nhiên response2docx cũ vẫn cần creds object
        try:
            # Lấy thông tin từ env (đã load bởi callAPI hoặc main)
            # Tạo dummy credentials hoặc load thật nếu cần thiết cho thư viện google
            # Ở đây ta giả định dùng API Key là chính, nhưng giữ code cũ để tương thích
            self.project_id = os.getenv("PROJECT_ID")
            self.credentials = None # API Key mode của Gemini không cần service account object
        except Exception:
            self.project_id = "unknown"
            self.credentials = None

    def load_default_prompts(self):
        self.prompt_tn_content = ""
        self.prompt_ds_content = ""
        self.prompt_tln_content = ""
        
        def read_safe(path):
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f: return f.read()
            return ""

        self.prompt_tn_content = read_safe(self.default_prompt_tn)
        self.prompt_ds_content = read_safe(self.default_prompt_ds)
        self.prompt_tln_content = read_safe(self.default_prompt_tln)

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        # TAB 1: CẤU HÌNH & XỬ LÝ
        proc_tab = QWidget()
        proc_layout = QVBoxLayout()
        
        # 1. Nguồn tài liệu
        file_group = QGroupBox("1. Chọn Tài Liệu (PDF đã cắt)")
        file_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_add_file = QPushButton("📄 Thêm File")
        self.btn_add_folder = QPushButton("📁 Thêm Folder")
        self.btn_clear = QPushButton("🗑️ Xóa List")
        self.btn_add_file.clicked.connect(self.add_pdf_files)
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_clear.clicked.connect(lambda: self.file_tree.clear() or self.update_file_count())
        
        btn_layout.addWidget(self.btn_add_file)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear)
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Tên File", "Đường dẫn"])
        self.file_tree.setColumnWidth(0, 400)
        self.file_count_lbl = QLabel("Chưa chọn file nào")
        
        file_layout.addLayout(btn_layout)
        file_layout.addWidget(self.file_tree)
        file_layout.addWidget(self.file_count_lbl)
        file_group.setLayout(file_layout)

        # 2. Cấu hình Prompt
        conf_group = QGroupBox("2. Cấu Hình Loại Đề")
        conf_layout = QVBoxLayout()
        
        # Trắc nghiệm
        tn_row = QHBoxLayout()
        self.chk_tn = QCheckBox("Trắc nghiệm (4 đáp án)")
        self.chk_tn.setChecked(True)
        self.btn_edit_tn = QPushButton("✏️ Sửa Prompt TN")
        self.btn_edit_tn.clicked.connect(lambda: self.edit_prompt("trac_nghiem"))
        tn_row.addWidget(self.chk_tn)
        tn_row.addWidget(self.btn_edit_tn)
        tn_row.addStretch()

        # Đúng sai
        ds_row = QHBoxLayout()
        self.chk_ds = QCheckBox("Đúng / Sai")
        self.chk_ds.setChecked(True)
        self.btn_edit_ds = QPushButton("✏️ Sửa Prompt ĐS")
        self.btn_edit_ds.clicked.connect(lambda: self.edit_prompt("dung_sai"))
        ds_row.addWidget(self.chk_ds)
        ds_row.addWidget(self.btn_edit_ds)
        ds_row.addStretch()

        # Trả lời ngắn
        tln_row = QHBoxLayout()
        self.chk_tln = QCheckBox("Trả lời ngắn")
        self.chk_tln.setChecked(True)
        self.btn_edit_tln = QPushButton("✏️ Sửa Prompt TLN")
        self.btn_edit_tln.clicked.connect(lambda: self.edit_prompt("tra_loi_ngan"))
        tln_row.addWidget(self.chk_tln)
        tln_row.addWidget(self.btn_edit_tln)
        tln_row.addStretch()

        conf_layout.addLayout(tn_row)
        conf_layout.addLayout(ds_row)
        conf_layout.addLayout(tln_row)
        conf_group.setLayout(conf_layout)

        # 3. Action
        act_layout = QHBoxLayout()
        self.spin_worker = QSpinBox()
        self.spin_worker.setRange(1, 10)
        self.spin_worker.setValue(3)
        self.spin_worker.setPrefix("Luồng xử lý: ")
        
        self.btn_process = QPushButton("🚀 BẮT ĐẦU SINH CÂU HỎI")
        self.btn_process.setObjectName("ProcessBtn")
        self.btn_process.clicked.connect(self.process_files)
        
        act_layout.addWidget(self.spin_worker)
        act_layout.addWidget(self.btn_process)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_lbl = QLabel("Sẵn sàng")

        proc_layout.addWidget(file_group, 5)
        proc_layout.addWidget(conf_group, 3)
        proc_layout.addLayout(act_layout)
        proc_layout.addWidget(self.progress_bar)
        proc_layout.addWidget(self.status_lbl)
        proc_tab.setLayout(proc_layout)

        # TAB 2: KẾT QUẢ
        res_tab = QWidget()
        res_layout = QHBoxLayout()
        
        self.res_list = QListWidget()
        self.res_list.itemClicked.connect(self.preview_docx)
        
        right_panel = QVBoxLayout()
        self.web_view = QWebEngineView()
        self.btn_open_word = QPushButton("Mở bằng Word")
        self.btn_open_word.clicked.connect(self.open_word)
        
        right_panel.addWidget(QLabel("Xem trước (Preview):"))
        right_panel.addWidget(self.web_view)
        right_panel.addWidget(self.btn_open_word)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.res_list)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 3)

        res_layout.addWidget(splitter)
        res_tab.setLayout(res_layout)

        self.tab_widget.addTab(proc_tab, "Cấu hình & Chạy")
        self.tab_widget.addTab(res_tab, "Kết quả")
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    # --- LOGIC QUẢN LÝ FILE ---
    def add_pdf_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn PDF", "", "PDF Files (*.pdf)")
        if files:
            for f in files:
                item = QTreeWidgetItem(self.file_tree)
                item.setText(0, os.path.basename(f))
                item.setText(1, f)
                item.setCheckState(0, Qt.Checked)
            self.update_file_count()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục")
        if folder:
            pdfs = glob.glob(os.path.join(folder, "*.pdf"))
            for f in pdfs:
                item = QTreeWidgetItem(self.file_tree)
                item.setText(0, os.path.basename(f))
                item.setText(1, f)
                item.setCheckState(0, Qt.Checked)
            self.update_file_count()

    def update_file_count(self):
        count = self.file_tree.topLevelItemCount()
        self.file_count_lbl.setText(f"Đang có {count} file")

    def get_selected_files(self):
        # Logic gom nhóm file (đơn giản hóa)
        # Nếu muốn dùng logic smart_group phức tạp, copy từ GenQues cũ vào đây
        groups = {}
        root = self.file_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.checkState(0) == Qt.Checked:
                path = item.text(1)
                name = os.path.splitext(os.path.basename(path))[0]
                groups[name] = [path] # Tạm thời mỗi file 1 group để test
        return groups

    # --- LOGIC PROMPT ---
    def edit_prompt(self, p_type):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sửa Prompt {p_type}")
        dialog.resize(600, 500)
        layout = QVBoxLayout()
        
        txt_edit = QTextEdit()
        content = ""
        if p_type == "trac_nghiem": content = self.prompt_tn_content
        elif p_type == "dung_sai": content = self.prompt_ds_content
        elif p_type == "tra_loi_ngan": content = self.prompt_tln_content
        
        txt_edit.setPlainText(content)
        
        btn_save = QPushButton("Lưu tạm thời (RAM)")
        def save():
            new_text = txt_edit.toPlainText()
            if p_type == "trac_nghiem": self.prompt_tn_content = new_text
            elif p_type == "dung_sai": self.prompt_ds_content = new_text
            elif p_type == "tra_loi_ngan": self.prompt_tln_content = new_text
            dialog.accept()
            
        btn_save.clicked.connect(save)
        layout.addWidget(txt_edit)
        layout.addWidget(btn_save)
        dialog.setLayout(layout)
        dialog.exec_()

    # --- LOGIC CHẠY (PROCESS) ---
    def process_files(self):
        selected = self.get_selected_files()
        if not selected:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn file nào!")
            return

        # Map prompt hiện tại
        prompts = {}
        if self.chk_tn.isChecked(): prompts["trac_nghiem"] = "RAM" # Logic thread sẽ đọc từ RAM variable nếu cần sửa lại
        # Để đơn giản, ta ghi tạm ra file temp hoặc sửa Thread để nhận string
        # Ở đây tôi sửa Thread nhận path, nên ta cần lưu nội dung ra file temp nếu đã sửa
        # ... (Để code gọn, giả định user sửa file gốc hoặc ta dùng biến self.prompt_paths trỏ tới file gốc)
        
        prompt_paths = {}
        if self.chk_tn.isChecked(): prompt_paths["trac_nghiem"] = self.default_prompt_tn
        if self.chk_ds.isChecked(): prompt_paths["dung_sai"] = self.default_prompt_ds
        if self.chk_tln.isChecked(): prompt_paths["tra_loi_ngan"] = self.default_prompt_tln

        self.btn_process.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_lbl.setText("Đang xử lý...")

        # KHỞI TẠO THREAD VỚI MODULE PROCESSOR
        self.processing_thread = ProcessingThread(
            selected,
            prompt_paths,
            self.project_id,
            self.credentials,
            self.processor_module, # <--- QUAN TRỌNG: Truyền module vào
            self.spin_worker.value()
        )
        
        # Override nội dung prompt trong thread (Hack để dùng nội dung RAM)
        # Bạn có thể sửa logic Thread sạch hơn, đây là cách nhanh
        # ...

        self.processing_thread.progress.connect(lambda s: self.status_lbl.setText(s))
        self.processing_thread.progress_update.connect(lambda c, t: self.progress_bar.setValue(int(c/t*100) if t else 0))
        self.processing_thread.finished.connect(self.on_finished)
        self.processing_thread.start()

    def on_finished(self, files):
        self.generated_files = files
        self.res_list.clear()
        for f in files:
            self.res_list.addItem(os.path.basename(f))
        
        self.btn_process.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_lbl.setText(f"Hoàn thành! Tạo được {len(files)} file.")
        self.tab_widget.setCurrentIndex(1) # Chuyển tab kết quả

    # --- LOGIC PREVIEW ---
    def preview_docx(self, item):
        fname = item.text()
        fpath = next((f for f in self.generated_files if os.path.basename(f) == fname), None)
        if fpath and os.path.exists(fpath):
            try:
                with open(fpath, "rb") as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    html = f"<html><body>{result.value}</body></html>"
                    self.web_view.setHtml(html)
            except Exception as e:
                self.web_view.setHtml(f"Lỗi đọc file: {e}")

    def open_word(self):
        item = self.res_list.currentItem()
        if item:
            fname = item.text()
            fpath = next((f for f in self.generated_files if os.path.basename(f) == fname), None)
            if fpath:
                os.startfile(fpath)