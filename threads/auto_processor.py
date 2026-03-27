import os
import json
import re
import xlsxwriter
import sys
from PyQt5.QtCore import QThread, pyqtSignal

from core.client_driver import GoogleDriveAPI
from core.callAPI import VertexClient
from core.cutPDF import cut_pdf_by_pages

class AutoProcessor(QThread):
    """
    Class xử lý tự động: Google Drive → AI Analysis → Cut PDF
    """
    progress = pyqtSignal(str, int)  # message, percent
    error = pyqtSignal(str)
    finished = pyqtSignal(list)  # danh sách tất cả file đã tạo
    file_completed = pyqtSignal(str, list)  # file_name, generated_files

    def __init__(self, drive_folder_url, prompt_path, project_id, creds, base_download_path=None):
        super().__init__()
        self.drive_folder_url = drive_folder_url
        self.prompt_path = prompt_path
        self.project_id = project_id
        self.creds = creds
        
        # Tạo thư mục download mặc định
        if base_download_path is None:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_download_path = os.path.join(app_dir, "auto_processed")
        else:
            self.base_download_path = base_download_path
        
        os.makedirs(self.base_download_path, exist_ok=True)
        
        # Client secrets file path
        self.client_secrets_file = r'D:\CutPdfByDrive\client_secret_409523926306-7tu8v8tqs22mq812nv9tuktiapfct823.apps.googleusercontent.com.json'
        
        self.all_generated_files = []
        # ⭐ THÊM BIẾN LƯU CẤU TRÚC FOLDER ⭐
        self.pdf_folder_mapping = {}  # {pdf_path: relative_folder_path}
    
    def run(self):
        """Main processing pipeline"""
        try:
            # Step 1: Initialize clients
            self.progress.emit("Khởi tạo kết nối...", 5)
            drive_api = GoogleDriveAPI(self.client_secrets_file)
            vertex_client = VertexClient(self.project_id, self.creds, "gemini-2.5-pro")
            
            # Step 2: Download PDFs from Drive (và lưu cấu trúc folder)
            self.progress.emit("Đang tải PDF từ Google Drive...", 10)
            downloaded_files = self._download_pdfs_from_drive_with_structure(drive_api)
            
            if not downloaded_files:
                self.error.emit("Không tìm thấy file PDF nào trong folder Google Drive")
                return
            
            self.progress.emit(f"Đã tải {len(downloaded_files)} file PDF", 20)
            
            # Step 3: Process each PDF với cấu trúc folder
            total_files = len(downloaded_files)
            for i, pdf_path in enumerate(downloaded_files):
                base_progress = 20 + int((i / total_files) * 70)  # 20-90%
                
                file_name = os.path.basename(pdf_path)
                self.progress.emit(f"Đang xử lý: {file_name} ({i+1}/{total_files})", base_progress)
                
                try:
                    # Process single PDF với cấu trúc folder
                    generated_files = self._process_single_pdf_with_structure(pdf_path, vertex_client, base_progress)
                    
                    if generated_files:
                        self.all_generated_files.extend(generated_files)
                        self.file_completed.emit(file_name, generated_files)
                        self.progress.emit(f"✓ Hoàn thành: {file_name}", base_progress + int(70/total_files))
                    else:
                        self.progress.emit(f"✗ Lỗi: {file_name}", base_progress + int(70/total_files))
                
                except Exception as e:
                    self.progress.emit(f"✗ Lỗi {file_name}: {str(e)}", base_progress + int(70/total_files))
            
            # Step 4: Finish
            self.progress.emit(f"Hoàn tất! Tạo ra {len(self.all_generated_files)} file", 100)
            self.finished.emit(self.all_generated_files)
            
        except Exception as e:
            self.error.emit(f"Lỗi trong quá trình xử lý: {str(e)}")
    
    def _download_pdfs_from_drive_with_structure(self, drive_api):
        """Download all PDFs from Google Drive folder và lưu cấu trúc folder"""
        try:
            # Extract folder ID
            folder_id = drive_api.extract_folder_id(self.drive_folder_url)
            
            # Create download folder
            download_folder = os.path.join(self.base_download_path, "downloaded_pdfs")
            
            # ⭐ LẤY CẤU TRÚC FOLDER TRƯỚC KHI DOWNLOAD ⭐
            root_folder_name = drive_api.get_folder_name(folder_id)
            all_folders = drive_api.list_all_folders(folder_id)
            all_folders[folder_id] = ""  # Thêm folder gốc
            
            # Download with structure
            drive_api.download_all_pdfs_with_structure(folder_id, download_folder)
            
            # ⭐ BUILD PDF-FOLDER MAPPING ⭐
            pdf_files = []
            root_download_path = os.path.join(download_folder, root_folder_name)
            
            for root, dirs, files in os.walk(root_download_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_path = os.path.join(root, file)
                        
                        # Tính relative path từ root_download_path
                        relative_path = os.path.relpath(os.path.dirname(pdf_path), root_download_path)
                        if relative_path == ".":
                            relative_path = ""  # File ở root folder
                        
                        # Lưu mapping
                        self.pdf_folder_mapping[pdf_path] = relative_path
                        pdf_files.append(pdf_path)
            
            return pdf_files
            
        except Exception as e:
            raise Exception(f"Lỗi khi tải từ Google Drive: {str(e)}")
    
    def _process_single_pdf_with_structure(self, pdf_path, vertex_client, base_progress):
        """Process single PDF: AI analysis → Cut PDF với cấu trúc folder"""
        try:
            # Read prompt
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            
            # Send to AI
            self.progress.emit(f"Gửi lên AI: {os.path.basename(pdf_path)}", base_progress + 10)
            ai_result = vertex_client.send_data_to_AI(prompt, pdf_path)
            
            # Parse JSON response
            self.progress.emit(f"Phân tích kết quả AI: {os.path.basename(pdf_path)}", base_progress + 20)
            json_data = self._parse_ai_response(ai_result)
            
            if not json_data:
                raise ValueError("Không thể phân tích kết quả từ AI")
            
            # ⭐ TạO OUTPUT FOLDER THEO CẤU TRÚC GỐC ⭐
            file_name = os.path.splitext(os.path.basename(pdf_path))[0]
            
            # Lấy relative folder path của file PDF này
            relative_folder = self.pdf_folder_mapping.get(pdf_path, "")
            
            # Tạo output path với cấu trúc tương tự
            if relative_folder:
                output_folder = os.path.join(self.base_download_path, "processed", relative_folder, file_name)
            else:
                output_folder = os.path.join(self.base_download_path, "processed", file_name)
            
            os.makedirs(output_folder, exist_ok=True)
            
            # Save JSON result
            json_path = os.path.join(output_folder, f"{file_name}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            # Cut PDF into parts
            self.progress.emit(f"Cắt PDF: {os.path.basename(pdf_path)}", base_progress + 30)
            generated_files = self._cut_pdf_by_ai_result(pdf_path, json_data, output_folder, file_name)
            
            # Create Excel summary
            self._create_excel_summary(json_data, output_folder, file_name)
            
            return generated_files
            
        except Exception as e:
            raise Exception(f"Lỗi xử lý {os.path.basename(pdf_path)}: {str(e)}")
    
    def _parse_ai_response(self, ai_result):
        """
        Xử lý chuyên sâu cho tiếng Trung và cấu trúc JSON từ Gemini.
        """
        try:
            # 1. Loại bỏ các khối code markdown (```json ... ```) nếu có
            clean_content = re.sub(r"```json|```", "", ai_result).strip()
            
            # 2. Tìm mảng JSON [...]
            match = re.search(r"\[[\s\S]*\]", clean_content)
            if not match:
                print("❌ Không tìm thấy mảng JSON trong phản hồi AI.")
                return None
                
            json_str = match.group(0)
            
            # 3. Parse JSON với strict=False để chấp nhận các ký tự điều khiển (control characters) 
            # thường xuất hiện khi AI trả về văn bản tiếng Trung
            data = json.loads(json_str, strict=False)
            
            processed_data = []
            for item in data:
                name = item.get('name', 'Untitled')
                start = item.get('start_page')
                end = item.get('end_page')
                
                if start is not None and end is not None:
                    # 4. Làm sạch tên bài tiếng Trung để dùng làm tên file
                    # Loại bỏ các ký tự cấm của OS: \ / : * ? " < > | 
                    clean_name = re.sub(r'[\\/:*?"<>|]', '_', name)
                    # Loại bỏ các ký tự điều khiển ẩn và chuẩn hóa khoảng trắng
                    clean_name = "".join(ch for ch in clean_name if ch.isprintable())
                    clean_name = " ".join(clean_name.split()).strip(". ")
                    
                    item['name'] = clean_name
                    processed_data.append(item)
                    
            return processed_data
        except Exception as e:
            print(f"❌ Lỗi xử lý JSON/Tiếng Trung: {e}")
            return None
    
    def _cut_pdf_by_ai_result(self, pdf_path, json_data, output_folder, book_name):
        """Cut PDF based on AI analysis result (không nén)"""
        generated_files = []
        
        for idx, bai in enumerate(json_data):
            try:
                safe_name = re.sub(r"[:\\/\"*?<>|]", ".", bai['name'])
                output_filename = f"{safe_name}.pdf"
                output_path = os.path.join(output_folder, output_filename)
                
                # ⭐ CHỈ CẮT, KHÔNG NÉN ⭐
                cut_pdf_by_pages(
                    pdf_path, 
                    output_path, 
                    bai['start_page'], 
                    bai['end_page']
                )
                
                generated_files.append(output_path)
                print(f"✅ Tạo file: {output_filename}")
                
            except Exception as e:
                print(f"❌ Lỗi khi cắt bài '{bai['name']}': {str(e)}")

        return generated_files
    
    def _create_excel_summary(self, json_data, output_folder, file_name):
        """Create Excel summary file"""
        try:
            excel_path = os.path.join(output_folder, f"{file_name}_summary.xlsx")
            workbook = xlsxwriter.Workbook(excel_path)
            worksheet = workbook.add_worksheet()
            
            # Headers
            headers = ["STT", "Tên bài", "Trang bắt đầu", "Trang kết thúc", "Số trang"]
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)
            
            # Data
            for idx, bai in enumerate(json_data):
                row = idx + 1
                worksheet.write(row, 0, idx + 1)
                worksheet.write(row, 1, bai['name'])
                worksheet.write(row, 2, bai['start_page'])
                worksheet.write(row, 3, bai['end_page'])
                worksheet.write(row, 4, bai['end_page'] - bai['start_page'] + 1)
            
            workbook.close()
            
        except Exception as e:
            print(f"Lỗi tạo Excel summary: {str(e)}")


class AutoProcessorWidget:
    """
    Widget helper để tích hợp vào main.py
    """
    @staticmethod
    def add_auto_process_ui(main_window):
        """Thêm UI cho auto processing vào main window"""
        from PyQt5.QtWidgets import QPushButton
        
        # Auto process button
        auto_process_btn = QPushButton("🤖 Tự động xử lý từ Drive")
        auto_process_btn.setFixedHeight(40)
        auto_process_btn.setStyleSheet("border: 1px solid black; background-color: #e6ffe6;")
        auto_process_btn.clicked.connect(lambda: main_window.start_auto_processing())
        
        return auto_process_btn