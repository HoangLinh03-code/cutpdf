import os
import json
import re
import xlsxwriter
import sys
from PyQt5.QtCore import QThread, pyqtSignal

from callAPI import VertexClient
from cutPDF import cut_pdf_by_pages

class LocalProcessor(QThread):
    """
    Class xử lý PDF từ folder local
    """
    progress = pyqtSignal(str, int)  # message, percent
    error = pyqtSignal(str)
    finished = pyqtSignal(list)  # danh sách tất cả file đã tạo
    file_completed = pyqtSignal(str, list)  # file_name, generated_files

    def __init__(self, local_folder_path, pdf_files, prompt_path, project_id, creds):
        super().__init__()
        self.local_folder_path = local_folder_path
        self.pdf_files = pdf_files
        self.prompt_path = prompt_path
        self.project_id = project_id
        self.creds = creds
        
        # Tạo thư mục output
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.output_base_path = os.path.join(app_dir, "local_processed")
        os.makedirs(self.output_base_path, exist_ok=True)
        
        self.all_generated_files = []
        # Build folder structure mapping
        self.pdf_folder_mapping = {}
        self._build_folder_mapping()
    
    def _build_folder_mapping(self):
        """Build mapping của PDF files với relative folder paths"""
        for pdf_path in self.pdf_files:
            relative_path = os.path.relpath(os.path.dirname(pdf_path), self.local_folder_path)
            if relative_path == ".":
                relative_path = ""
            self.pdf_folder_mapping[pdf_path] = relative_path
    
    def run(self):
        """Main processing pipeline"""
        try:
            # Initialize AI client
            self.progress.emit("Khởi tạo AI client...", 5)
            vertex_client = VertexClient(self.project_id, self.creds, "gemini-2.5-pro")
            
            # Process each PDF
            total_files = len(self.pdf_files)
            self.progress.emit(f"Bắt đầu xử lý {total_files} file PDF...", 10)
            
            for i, pdf_path in enumerate(self.pdf_files):
                base_progress = 10 + int((i / total_files) * 80)  # 10-90%
                
                file_name = os.path.basename(pdf_path)
                self.progress.emit(f"Đang xử lý: {file_name} ({i+1}/{total_files})", base_progress)
                
                try:
                    # Process single PDF
                    generated_files = self._process_single_pdf(pdf_path, vertex_client, base_progress)
                    
                    if generated_files:
                        self.all_generated_files.extend(generated_files)
                        self.file_completed.emit(file_name, generated_files)
                        self.progress.emit(f"✓ Hoàn thành: {file_name}", base_progress + int(80/total_files))
                    else:
                        self.progress.emit(f"✗ Lỗi: {file_name}", base_progress + int(80/total_files))
                
                except Exception as e:
                    self.progress.emit(f"✗ Lỗi {file_name}: {str(e)}", base_progress + int(80/total_files))
            
            # Finish
            self.progress.emit(f"Hoàn tất! Tạo ra {len(self.all_generated_files)} file", 100)
            self.finished.emit(self.all_generated_files)
            
        except Exception as e:
            self.error.emit(f"Lỗi trong quá trình xử lý: {str(e)}")
    
    def _process_single_pdf(self, pdf_path, vertex_client, base_progress):
        """Process single PDF: AI analysis → Cut PDF"""
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
            
            # Create output folder với cấu trúc tương tự
            file_name = os.path.splitext(os.path.basename(pdf_path))[0]
            relative_folder = self.pdf_folder_mapping.get(pdf_path, "")
            
            if relative_folder:
                output_folder = os.path.join(self.output_base_path, "processed", relative_folder, file_name)
            else:
                output_folder = os.path.join(self.output_base_path, "processed", file_name)
            
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
        """Parse JSON array from AI response"""
        try:
            clean = re.search(r"\[[\s\S]*\]", ai_result)
            if clean:
                json_str = clean.group(0)
                return json.loads(json_str)
            else:
                return None
        except Exception:
            return None
    
    def _cut_pdf_by_ai_result(self, pdf_path, json_data, output_folder, book_name):
        """Cut PDF based on AI analysis result"""
        generated_files = []
        
        for idx, bai in enumerate(json_data):
            try:
                # Clean filename
                safe_name = re.sub(r"[:\\/\"*?<>|]", ".", bai['name'])
                
                # Đặt tên file: "Tên sách + Tên bài.pdf"
                output_filename = f"{book_name} - {safe_name}.pdf"
                output_path = os.path.join(output_folder, output_filename)
                
                # Cut PDF
                cut_pdf_by_pages(
                    pdf_path, 
                    output_path, 
                    bai['start_page'], 
                    bai['end_page']
                )
                
                generated_files.append(output_path)
                
            except Exception as e:
                print(f"Lỗi khi cắt bài '{bai['name']}': {str(e)}")
        
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