from PyQt5.QtCore import QThread, pyqtSignal
from process import ProcessingThread
import os

class BatchProcessingThread(QThread):
    progress = pyqtSignal(str, int)
    error = pyqtSignal(str)
    finished = pyqtSignal(list)  # Tất cả file đã tạo

    def __init__(self, pdf_files, prompt_path, project_id, creds):
        super().__init__()
        self.pdf_files = pdf_files
        self.prompt_path = prompt_path
        self.project_id = project_id
        self.creds = creds

    def run(self):
        try:
            all_generated_files = []
            total_files = len(self.pdf_files)
            
            for i, pdf_file in enumerate(self.pdf_files):
                file_name = os.path.basename(pdf_file)
                self.progress.emit(f"Đang xử lý: {file_name} ({i+1}/{total_files})", 
                                 int((i / total_files) * 100))
                
                # Xử lý từng file bằng ProcessingThread logic
                # (Bạn có thể tách logic xử lý ra thành function riêng)
                from process import ProcessingThread
                
                # Tạo thread con cho từng file
                single_thread = ProcessingThread(
                    pdf_file, self.prompt_path, self.project_id, self.creds
                )
                
                # Chạy đồng bộ (không dùng thread để tránh conflict)
                single_thread.run()
                
                # Giả sử kết quả được lưu trong thuộc tính result
                if hasattr(single_thread, 'result_files'):
                    all_generated_files.extend(single_thread.result_files)
            
            self.finished.emit(all_generated_files)
            
        except Exception as e:
            self.error.emit(str(e))