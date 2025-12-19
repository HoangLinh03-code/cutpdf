import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
    QFileDialog, QMessageBox, QGroupBox, QScrollArea, QFrame,
    QDialog, QDialogButtonBox, QFormLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QIntValidator, QTextCharFormat, QTextCursor, QColor, QBrush
import shutil
from datetime import datetime, timedelta
import subprocess
from multiprocessing import Queue, Event, Process

from modules.chuyendang.devide_docx import split_docx_to_parts
from modules.chuyendang.ai_handle.vertex_ai import process_folder_of_markdown_files
from modules.chuyendang.concurent_process import process_batch_files
def get_timestamp():
    """Hàm giả định cho ví dụ."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# Lớp để chuyển hướng stdout tới QTextEdit và lưu log
class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.log_buffer = []

    def write(self, text):
        self.log_buffer.append(text)

    def flush(self):
        pass

    def save_log(self, file_path):
        if self.log_buffer:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(self.log_buffer)
                print(f"[{get_timestamp()}] Đã lưu file log: {file_path}")
            except Exception as e:
                print(f"[{get_timestamp()}] LỖI: Không thể lưu file log: {e}")


# HÀM SẼ CHẠY TRONG TIẾN TRÌNH CON
class ProcessWorker:
    def __init__(self, log_queue, finished_queue):
        self.log_queue = log_queue
        self.finished_queue = finished_queue

    def run(self, docx_path, subject, grade, list_string, stop_event, process_id):
        original_stdout = sys.stdout
        sys.stdout = self

        try:
            print(f"[{get_timestamp()}] [{process_id}] Bắt đầu quy trình xử lý tài liệu trong tiến trình con.\n")
            
            output_docx_processed_dir,output_docx_parts_dir,output_md_parts_dir,md_file, media_folder,temp_md_dir= split_docx_to_parts(docx_path, stop_patterns=list_string)
            if(output_docx_processed_dir is None or output_docx_parts_dir is None or output_md_parts_dir is None):
                print(f"[{get_timestamp()}] [{process_id}] LỖI: Không thể chia file DOCX thành các phần con.")
                self.finished_queue.put({"success": False, "output_dir": "", "process_id": process_id})
                return
            print(f"[{get_timestamp()}] [{process_id}] Đã chia file DOCX thành các phần con.")
            print(f"[{get_timestamp()}] [{process_id}] Đường dẫn đầu ra đã được tạo: {output_docx_processed_dir}, {output_docx_parts_dir}, {output_md_parts_dir}")  

            
            json_directory= process_folder_of_markdown_files(output_md_parts_dir, log_file_path="final_report.txt",num_processes=3)
            if json_directory is None:
                print(f"[{get_timestamp()}] [{process_id}] LỖI: Không thể xử lý các file Markdown.")
                self.finished_queue.put({"success": False, "output_dir": "", "process_id": process_id})
                return
            output_base_dir=process_batch_files( output_docx_parts_dir, subject, grade, json_directory)



            print(f"[{get_timestamp()}] [{process_id}] Hoàn thành quy trình xử lý tài liệu.")
            
            if os.path.exists(output_base_dir):
                shutil.rmtree(output_md_parts_dir, ignore_errors=True)
            if os.path.exists("media"):
                shutil.rmtree("media", ignore_errors=True)
            if os.path.exists(temp_md_dir):
                shutil.rmtree(temp_md_dir, ignore_errors=True)
            if os.path.exists(md_file):
                shutil.rmtree(md_file, ignore_errors=True)
            if os.path.exists(media_folder):
                shutil.rmtree(media_folder, ignore_errors=True)
            self.finished_queue.put({"success": True, "output_dir": output_base_dir, "process_id": process_id})
            print(self.log_queue)
        except Exception as e:
            print(f"[{get_timestamp()}] [{process_id}] LỖI trong tiến trình con: {str(e)}\n")
            self.finished_queue.put({"success": False, "output_dir": "", "process_id": process_id})
        finally:
            self.log_queue.put(f"PROCESS_FINISHED_LOGGING_SIGNAL_{process_id}")
            sys.stdout = original_stdout

    def write(self, text):
        self.log_queue.put(text)
    
    def flush(self):
        pass

# Lớp QThread để đọc log từ multiprocessing.Queue
class LogReaderThread(QThread):
    log_signal = pyqtSignal(str, str)   # text, process_id
    
    def __init__(self, log_queue, process_id):
        super().__init__()
        self.log_queue = log_queue
        self.process_id = process_id
        self._running = True

    def run(self):
        while self._running:
            try:
                message = self.log_queue.get(timeout=0.1)
                if message == f"PROCESS_FINISHED_LOGGING_SIGNAL_{self.process_id}":
                    print(f"[{get_timestamp()}] LogReaderThread [{self.process_id}]: Nhận tín hiệu kết thúc log từ tiến trình con.")
                    break
                self.log_signal.emit(message, self.process_id)
            except Exception:
                continue
        print(f"[{get_timestamp()}] LogReaderThread [{self.process_id}] đã dừng.")

    def stop(self):
        self._running = False
        self.wait()

# Lớp QDialog cho form nhập liệu popup
class DataFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Form Nhập Tên chương để đánh dấu tách file DOCX")
        self.setFixedSize(600, 500)

        # Tạo layout chính
        main_layout = QVBoxLayout(self)

        # Hướng dẫn người dùng
        instruction_label = QLabel("Nhập một chuỗi và nhấn 'Thêm':")
        main_layout.addWidget(instruction_label)

        # Ô nhập liệu và nút Thêm
        input_layout = QHBoxLayout()
        self.input_line_edit = QLineEdit()
        self.input_line_edit.setPlaceholderText("Nhập chuỗi...")
        add_button = QPushButton("Thêm")
        add_button.clicked.connect(self.add_item)
        input_layout.addWidget(self.input_line_edit)
        input_layout.addWidget(add_button)
        main_layout.addLayout(input_layout)

        # Danh sách các chuỗi đã nhập
        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)

        # Nút xóa mục
        remove_button = QPushButton("Xóa mục đã chọn")
        remove_button.clicked.connect(self.remove_item)
        main_layout.addWidget(remove_button)

        # Thêm các nút OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def add_item(self):
        """Thêm chuỗi từ QLineEdit vào QListWidget với màu nền xen kẽ."""
        text = self.input_line_edit.text().strip()
        if text:
            item = QListWidgetItem(text)
            
            # Gán màu nền xen kẽ dựa trên số mục hiện có
            if self.list_widget.count() % 2 == 0:
                item.setBackground(QBrush(QColor("#f0f0f0"))) # Màu xám nhạt
            else:
                item.setBackground(QBrush(QColor("#e0e0e0"))) # Màu xám đậm hơn
            
            item.setForeground(QBrush(QColor("black"))) # Đặt màu chữ là đen
            self.list_widget.addItem(item)
            self.input_line_edit.clear()

    def remove_item(self):
        """Xóa mục đã chọn khỏi QListWidget và cập nhật lại màu nền."""
        list_items = self.list_widget.selectedItems()
        if not list_items:
            return
        
        # Xóa các mục đã chọn
        for item in list_items:
            self.list_widget.takeItem(self.list_widget.row(item))
            
        # Cập nhật lại màu nền cho các mục còn lại
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if i % 2 == 0:
                item.setBackground(QBrush(QColor("#f0f0f0")))
            else:
                item.setBackground(QBrush(QColor("#e0e0e0")))

    def get_data(self):
        """Trả về dữ liệu từ form dưới dạng một list các chuỗi."""
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]


# Widget cho mỗi file DOCX
class DocxProcessWidget(QFrame):
    def __init__(self, main_window, process_id):
        super().__init__()
        self.main_window = main_window
        self.process_id = process_id
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        
        self.workflow_process = None
        self.stop_process_event = None
        self.log_queue = None
        self.finished_queue = None
        self.log_reader_thread = None
        self.start_time = None
        self.stdout_redirector = None
        self.log_file_path = None
        self.check_finished_timer = None
        self.data_form_dialog=[]
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header với ID
        header_layout = QHBoxLayout()
        header_label = QLabel(f"Tiến trình #{self.process_id[:8]}")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(header_label)
        
        # Nút xóa
        remove_button = QPushButton("✕")
        remove_button.setMaximumSize(25, 25)
        remove_button.clicked.connect(self.remove_self)
        remove_button.setStyleSheet("QPushButton { background-color: #ff4444; color: white; font-weight: bold; }")
        header_layout.addWidget(remove_button)
        layout.addLayout(header_layout)

        # Input settings
        input_group = QGroupBox("Cài đặt đầu vào")
        input_layout = QVBoxLayout()
        input_group.setLayout(input_layout)

        # File DOCX
        docx_layout = QHBoxLayout()
        self.docx_path_input = QLineEdit()
        self.docx_path_input.setPlaceholderText("Chọn file DOCX...")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_docx)
        docx_layout.addWidget(QLabel("File DOCX:"))
        docx_layout.addWidget(self.docx_path_input)
        docx_layout.addWidget(browse_button)
        input_layout.addLayout(docx_layout)

        # Options
        options_layout = QHBoxLayout()
        
        # Môn học
        subject_layout = QVBoxLayout()
        subject_layout.addWidget(QLabel("Môn học:"))
        self.subject_combo = QComboBox()
        self.subject_combo.addItems(["Toán", "Văn", "Anh", "Lý", "Hóa", "Sinh", "KHTN", "Sử",
                                     "Địa", "Lịch sử Địa lý", "Tin học", "Âm nhạc", "Mỹ thuật",
                                     "GDTC", "Hướng nghiệp, HĐTN", "Giáo dục Thể chất",
                                     "Giáo dục Quốc phòng","Giáo dục Công dân", "Kinh tế Pháp luật","Công nghệ"])
        subject_layout.addWidget(self.subject_combo)
        options_layout.addLayout(subject_layout)

        # Lớp
        grade_layout = QVBoxLayout()
        grade_layout.addWidget(QLabel("Lớp:"))
        self.grade_combo = QComboBox()
        self.grade_combo.addItems([ "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])
        grade_layout.addWidget(self.grade_combo)
        options_layout.addLayout(grade_layout)

        # Test kí tự
        marker_layout = QVBoxLayout()
        marker_layout.addWidget(QLabel("Đánh dấu tách file (Sử dụng tên chương):"))
        popup_button = QPushButton("Mở Form Popup")
        popup_button.clicked.connect(self.show_data_form_popup)


        marker_layout.addWidget(popup_button)
        
        options_layout.addLayout(marker_layout)
        input_layout.addLayout(options_layout)
        layout.addWidget(input_group)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Arial", 9))
        self.log_display.setMaximumHeight(750)
        layout.addWidget(QLabel("Theo dõi log:"))
        layout.addWidget(self.log_display)

        # Buttons
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.start_workflow)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_workflow)
        self.stop_button.setEnabled(False)
        
        # THÊM NÚT MỚI CHO POPUP
        # self.popup_button = QPushButton("Mở Form Popup")
        # self.popup_button.clicked.connect(self.show_data_form_popup)

        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setStyleSheet("color: blue;")
        
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
       
        button_layout.addWidget(self.status_label)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Khởi tạo stdout redirector
        self.stdout_redirector = StdoutRedirector(self.log_display)

    def browse_docx(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file DOCX", "", "Word Files (*.docx)")
        if file_path:
            self.docx_path_input.setText(file_path)

    # PHƯƠNG THỨC MỚI ĐỂ HIỂN THỊ POPUP
    def show_data_form_popup(self):
        """Hiển thị cửa sổ dialog chứa form nhập liệu và xử lý dữ liệu trả về."""
        dialog = DataFormDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data_list = dialog.get_data()
            if data_list:
                # Hiển thị danh sách các chuỗi đã nhập
                list_str = "\n".join([f"{item}" for item in data_list])
                QMessageBox.information(
                    self,
                    "Dữ liệu đã nhận",
                    f"Các chuỗi đã nhập:\n{list_str}"
                )
                self.data_form_dialog = data_list  # Lưu form để truy cập sau này
            else:
                QMessageBox.warning(self, "Không có dữ liệu", "Bạn chưa nhập chuỗi nào.")
        else:
            print("Form đã bị hủy.")

    def start_workflow(self):
        self.log_display.clear()
        self.start_time = datetime.now()
        
        docx_path = self.docx_path_input.text()
        subject = self.subject_combo.currentText()
        grade = self.grade_combo.currentText()
       

        if not os.path.exists(docx_path):
            QMessageBox.critical(self, "Lỗi", "Vui lòng chọn file DOCX hợp lệ!")
            return

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Đang chạy...")
        self.status_label.setStyleSheet("color: orange;")

        input_base_name_no_ext = os.path.splitext(os.path.basename(docx_path))[0].replace(" ", "_")
        log_output_dir = os.path.join(os.getcwd(), "logdir", f"{input_base_name_no_ext}_{grade}")
        os.makedirs(log_output_dir, exist_ok=True)
        self.log_file_path = os.path.join(log_output_dir, f"log.txt")

        self.log_queue = Queue()
        self.finished_queue = Queue()
        self.stop_process_event = Event()

        self.workflow_process = Process(
            target=ProcessWorker(self.log_queue, self.finished_queue).run,
            args=(
                docx_path, subject, grade,
                self.data_form_dialog,  # Lấy dữ liệu từ form popup
                self.stop_process_event,
                self.process_id
            )
        )
        self.workflow_process.start()

        self.log_reader_thread = LogReaderThread(self.log_queue, self.process_id)
        self.log_reader_thread.log_signal.connect(self.append_log)
        self.log_reader_thread.start()

        self.check_finished_timer = QTimer(self)
        self.check_finished_timer.setInterval(100)
        self.check_finished_timer.timeout.connect(self._check_finished_queue)
        self.check_finished_timer.start()

    def _check_finished_queue(self):
        try:
            result = self.finished_queue.get_nowait()
            if result and result.get("process_id") == self.process_id:
                self.check_finished_timer.stop()
                self.on_workflow_finished(result["success"], result["output_dir"])
        except Exception:
            pass

    def stop_workflow(self):
        if self.workflow_process and self.workflow_process.is_alive():
            if self.start_time:
                duration = datetime.now() - self.start_time
                duration_str = self.format_duration(duration)
                self.append_log(f"[{get_timestamp()}] [{self.process_id[:8]}] Quy trình nhận được yêu cầu dừng bởi người dùng. Thời gian: {duration_str}\n", self.process_id)
            
            self.stop_process_event.set()
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Đã dừng")
            self.status_label.setStyleSheet("color: red;")
            
            if self.log_reader_thread and self.log_reader_thread.isRunning():
                self.log_reader_thread.stop()

    def format_duration(self, duration: timedelta) -> str:
        total_seconds = int(duration.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds} giây"
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes} phút {seconds} giây"

    def append_log(self, text, process_id):
        if process_id != self.process_id:
            return
            
        self.stdout_redirector.log_buffer.append(text)

        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.End)

        current_format = cursor.charFormat()
        new_format = QTextCharFormat(current_format)
        
        if "LỖI" in text or "thất bại" in text:
            new_format.setForeground(Qt.red)
        elif "Hoàn thành" in text or "thành công" in text:
            new_format.setForeground(Qt.darkGreen)
        else:
            new_format.setForeground(Qt.black)
        
        cursor.setCharFormat(new_format)
        cursor.insertText(text)
        self.log_display.setTextCursor(cursor)
        self.log_display.ensureCursorVisible()
        cursor.setCharFormat(current_format)

    def on_workflow_finished(self, success, output_dir):
        if self.check_finished_timer and self.check_finished_timer.isActive():
            self.check_finished_timer.stop()

        if self.log_reader_thread and self.log_reader_thread.isRunning():
            self.log_reader_thread.stop()

        if self.start_time:
            duration = datetime.now() - self.start_time
            duration_str = self.format_duration(duration)
            self.append_log(f"[{get_timestamp()}] [{self.process_id[:8]}] Tổng thời gian thực hiện: {duration_str}\n", self.process_id)
        
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if self.stdout_redirector:
            self.stdout_redirector.save_log(self.log_file_path)

        if success:
            self.status_label.setText("Hoàn thành")
            self.status_label.setStyleSheet("color: green;")
            QMessageBox.information(
                self, "Thành công",
                f"Tiến trình {self.process_id[:8]} hoàn thành!\nKết quả: {output_dir}"
            )
            if os.path.exists(output_dir):
                if sys.platform == "win32":
                    os.startfile(output_dir)
                elif sys.platform == "darwin":
                    subprocess.run(["open", output_dir])
                else:
                    subprocess.run(["xdg-open", output_dir])
        else:
            self.status_label.setText("Thất bại")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Lỗi", f"Tiến trình {self.process_id[:8]} thất bại!")

    def remove_self(self):
        if self.workflow_process and self.workflow_process.is_alive():
            reply = QMessageBox.question(self, "Xác nhận", 
                                         "Tiến trình đang chạy. Bạn có muốn dừng và xóa không?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.stop_workflow()
            else:
                return
        
        self.main_window.remove_docx_widget(self)

    def cleanup(self):
        if self.check_finished_timer and self.check_finished_timer.isActive():
            self.check_finished_timer.stop()

        if self.workflow_process and self.workflow_process.is_alive():
            self.stop_process_event.set()
            self.workflow_process.join(timeout=3)
            if self.workflow_process.is_alive():
                self.workflow_process.terminate()
                self.workflow_process.join()

        if self.log_reader_thread and self.log_reader_thread.isRunning():
            self.log_reader_thread.stop()

        if self.stdout_redirector and self.stdout_redirector.log_buffer and self.log_file_path:
            self.stdout_redirector.save_log(self.log_file_path)

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.docx_widgets_layout = QVBoxLayout()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Ứng dụng PyQt5")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.add_docx_widget()
        add_button = QPushButton("Thêm một tiến trình mới")
        add_button.clicked.connect(self.add_docx_widget)
        main_layout.addLayout(self.docx_widgets_layout)
        main_layout.addWidget(add_button)

    def add_docx_widget(self):
        widget = DocxProcessWidget(self, str(os.urandom(16).hex()))
        self.docx_widgets_layout.addWidget(widget)

    def remove_docx_widget(self, widget):
        widget.cleanup()
        self.docx_widgets_layout.removeWidget(widget)
        widget.deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())