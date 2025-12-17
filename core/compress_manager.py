import os
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

class CompressThread(QThread):
    """Thread để nén PDF không blocking UI"""
    progress = pyqtSignal(str, int)  # message, percent
    error = pyqtSignal(str)
    finished = pyqtSignal(list)  # danh sách file đã nén
    file_completed = pyqtSignal(str, str, float, float)  # original_path, compressed_path, original_size, compressed_size

    def __init__(self, pdf_files, quality='ebook', output_suffix='_compressed'):
        super().__init__()
        self.pdf_files = pdf_files
        self.quality = quality
        self.output_suffix = output_suffix
        self.compressed_files = []

    def run(self):
        """Nén từng file PDF"""
        try:
            total_files = len(self.pdf_files)
            
            for i, pdf_path in enumerate(self.pdf_files):
                base_progress = int((i / total_files) * 90)
                
                file_name = os.path.basename(pdf_path)
                self.progress.emit(f"Đang nén: {file_name} ({i+1}/{total_files})", base_progress)
                
                try:
                    # Tạo đường dẫn output
                    dir_path = os.path.dirname(pdf_path)
                    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                    output_path = os.path.join(dir_path, f"{base_name}{self.output_suffix}.pdf")
                    
                    # Lấy kích thước file gốc
                    original_size = self.get_file_size_mb(pdf_path)
                    
                    # Nén file
                    success = self.compress_pdf_ghostscript(pdf_path, output_path, self.quality)
                    
                    if success and os.path.exists(output_path):
                        # Lấy kích thước file sau nén
                        compressed_size = self.get_file_size_mb(output_path)
                        
                        self.compressed_files.append(output_path)
                        self.file_completed.emit(pdf_path, output_path, original_size, compressed_size)
                        
                        compression_ratio = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
                        self.progress.emit(f"✅ {file_name}: {original_size}MB → {compressed_size}MB (-{compression_ratio:.1f}%)", 
                                         base_progress + int(90/total_files))
                    else:
                        self.progress.emit(f"❌ Lỗi nén: {file_name}", base_progress + int(90/total_files))
                        
                except Exception as e:
                    self.progress.emit(f"❌ Lỗi {file_name}: {str(e)}", base_progress + int(90/total_files))
            
            self.progress.emit(f"Hoàn tất nén {len(self.compressed_files)}/{total_files} file", 100)
            self.finished.emit(self.compressed_files)
            
        except Exception as e:
            self.error.emit(f"Lỗi trong quá trình nén: {str(e)}")

    def compress_pdf_ghostscript(self, input_path, output_path, quality='ebook'):
        """Nén PDF bằng Ghostscript"""
        if not os.path.isfile(input_path):
            return False

        try:
            gs_command = 'gswin64c'  # Windows 64-bit
            if os.name == 'posix':
                gs_command = 'gs'  # Linux/Mac
            
            cmd = [
                gs_command,
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                f'-dPDFSETTINGS=/{quality}',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                f'-sOutputFile={output_path}',
                input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Lỗi nén PDF: {e}")
            return False

    def get_file_size_mb(self, file_path):
        """Lấy kích thước file tính bằng MB"""
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        return 0


class CompressManager:
    """Manager để xử lý nén PDF"""
    
    @staticmethod
    def compress_single_file(input_path, output_path=None, quality='ebook'):
        """Nén một file PDF đơn lẻ"""
        if output_path is None:
            dir_path = os.path.dirname(input_path)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(dir_path, f"{base_name}_compressed.pdf")
        
        try:
            gs_command = 'gswin64c' if os.name == 'nt' else 'gs'
            
            cmd = [
                gs_command,
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                f'-dPDFSETTINGS=/{quality}',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                f'-sOutputFile={output_path}',
                input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return output_path
            else:
                return None
                
        except Exception as e:
            print(f"Lỗi nén file: {e}")
            return None
    
    @staticmethod
    def get_compression_info(original_path, compressed_path):
        """Lấy thông tin về tỷ lệ nén"""
        if not os.path.exists(original_path) or not os.path.exists(compressed_path):
            return None
        
        original_size = os.path.getsize(original_path) / (1024 * 1024)  # MB
        compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)  # MB
        
        compression_ratio = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
        
        return {
            'original_size_mb': round(original_size, 2),
            'compressed_size_mb': round(compressed_size, 2),
            'compression_ratio': round(compression_ratio, 1),
            'size_saved_mb': round(original_size - compressed_size, 2)
        }