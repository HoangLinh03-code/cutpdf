import os
import sys
import json
import re
from PyQt5.QtCore import QThread, pyqtSignal
from core.callAPI import VertexClient
from core.cutPDF import cut_and_compress_pdf, get_file_size_mb

class BatchProcessingThread(QThread):
    progress = pyqtSignal(str, int)
    error = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, pdf_files, prompt_path, project_id, creds, compress_enabled=True, quality='ebook'):
        super().__init__()
        self.pdf_files = pdf_files
        self.prompt_path = prompt_path
        self.project_id = project_id
        self.creds = creds
        self.compress_enabled = compress_enabled
        self.quality = quality

    def run(self):
        try:
            all_generated_files = []
            total_files = len(self.pdf_files)
            
            for i, pdf_file in enumerate(self.pdf_files):
                file_name = os.path.basename(pdf_file)
                base_progress = int((i / total_files) * 100)
                self.progress.emit(f"Đang xử lý: {file_name} ({i+1}/{total_files})", base_progress)
                
                try:
                    # Đọc prompt
                    with open(self.prompt_path, 'r', encoding='utf-8') as f:
                        prompt = f.read()

                    # Tạo AI client
                    client = VertexClient(self.project_id, self.creds, "gemini-2.5-pro")
                    
                    # Gửi lên AI
                    result = client.send_data_to_AI(prompt, pdf_file)
                    
                    # Parse JSON
                    clean = re.search(r"\[[\s\S]*\]", result)
                    if clean:
                        json_str = clean.group(0)
                        exercises = json.loads(json_str)
                        
                        # Tạo output folder
                        file_name_base = os.path.splitext(os.path.basename(pdf_file))[0]
                        if getattr(sys, 'frozen', False):
                            app_dir = os.path.dirname(sys.executable)
                        else:
                            app_dir = os.path.dirname(os.path.abspath(__file__))
                        
                        output_folder = os.path.join(app_dir, file_name_base)
                        os.makedirs(output_folder, exist_ok=True)
                        
                        # Cắt PDF với nén
                        file_generated = []
                        for idx, bai in enumerate(exercises):
                            safe_name = re.sub(r"[:\\/\"*?<>|]", ".", bai['name'])
                            output_filename = f"{idx+1:02d}. {safe_name}.pdf"
                            output_path = os.path.join(output_folder, output_filename)
                            
                            # Sử dụng cut_and_compress
                            success = cut_and_compress_pdf(
                                pdf_file,
                                output_path,
                                bai['start_page'],
                                bai['end_page'],
                                compress=self.compress_enabled,
                                quality=self.quality
                            )
                            
                            if success:
                                file_generated.append(output_path)
                                size_mb = get_file_size_mb(output_path)
                                print(f"✅ Tạo file: {output_filename} ({size_mb}MB)")
                        
                        all_generated_files.extend(file_generated)
                
                except Exception as e:
                    print(f"Lỗi xử lý {file_name}: {str(e)}")
                    continue
            
            self.finished.emit(all_generated_files)
            
        except Exception as e:
            self.error.emit(str(e))