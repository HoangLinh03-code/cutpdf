from PyQt5.QtCore import QThread, pyqtSignal
import os
import re
import json
import sys
import xlsxwriter
from cutPDF import cut_pdf_by_pages  # cut_pdf_by_pages là hàm bạn sẽ viết để cắt từng bài
from callAPI import VertexClient

class ProcessingThread(QThread):
    progress = pyqtSignal(str, int)  # message, percent
    error = pyqtSignal(str)
    finished = pyqtSignal(list)      # danh sách file PDF đã cắt

    def __init__(self, pdf_file, prompt_path, project_id, creds):
        super().__init__()
        self.pdf_file = pdf_file
        self.prompt_path = prompt_path
        self.project_id = project_id
        self.creds = creds

    def run(self):
        try:
            # 1. Đọc prompt
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()

            self.progress.emit("Đang gửi lên AI...", 10)
            # 2. Gửi lên AI, nhận về kết quả JSON


            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))


            file_name = os.path.splitext(os.path.basename(self.pdf_file))[0]
            output_folder = os.path.join(app_dir,file_name)
            os.makedirs(output_folder, exist_ok=True)
            
            client = VertexClient(self.project_id, self.creds, "gemini-2.5-pro")
            result = client.send_data_to_AI(prompt, self.pdf_file)
            self.progress.emit("Đã nhận kết quả từ AI", 30)
            
            # 3. Lưu kết quả JSON
            json_path = f"{file_name}.json"
            clean = re.search(r"\[[\s\S]*\]", result)
            if clean:
                with open(json_path, 'w', encoding='utf-8') as f:
                    f.write(clean.group(0))
            else:
                raise ValueError("Không tìm thấy mảng JSON hợp lệ trong kết quả trả về từ AI.")

            # 4. Đọc danh sách bài từ JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Giả sử data là list các dict: [{"name": ..., "start_page": ..., "end_page": ...}, ...]
            output_files = []
            workbook = xlsxwriter.Workbook(os.path.join(output_folder, f"{file_name}.xlsx"))
            worksheet = workbook.add_worksheet()


            for idx, bai in enumerate(data):
                # Ghi tiêu đề cột
                worksheet.write(0, 0, "Tên bài")
                worksheet.write(0, 1, "Trang bắt đầu")
                worksheet.write(0, 2, "Trang kết thúc")
                # Ghi dữ liệu
                worksheet.write(idx + 1, 0, bai['name'])
                worksheet.write(idx + 1, 1, bai['start_page'])
                worksheet.write(idx + 1, 2, bai['end_page'])
            
            total = len(data)
            for idx, bai in enumerate(data):
            # Thay tất cả dấu ":" bằng "."
                safe_name = re.sub(r":", ".", bai['name'])
                # out_pdf = f"{file_name}_{safe_name}.pdf"
                out_pdf = os.path.join(output_folder,f"{file_name}_{safe_name}.pdf")
                cut_pdf_by_pages(self.pdf_file, out_pdf, bai['start_page'], bai['end_page'])
                output_files.append(out_pdf)
                percent = 30 + int(70 * (idx + 1) / total)
                self.progress.emit(f"Đã cắt: {bai['name']}", percent)
            workbook.close()
            self.finished.emit(output_files)
        except Exception as e:
            self.error.emit(str(e))