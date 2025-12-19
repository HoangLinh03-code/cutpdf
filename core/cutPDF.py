import pypdf
from pypdf.generic import NullObject
import subprocess
import os
from PyPDF2.generic import NullObject
import re
def cut_pdf_by_pages(input_path, output_path, start_page, end_page):
    """
    Cắt PDF với cơ chế xử lý lỗi Null Object và tương thích tiếng Trung.
    """
    # 1. Làm sạch tên file đầu ra
    directory = os.path.dirname(output_path)
    filename = os.path.basename(output_path)
    # Giữ lại ký tự tiếng Trung, chỉ loại bỏ ký tự cấm của hệ thống
    safe_filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
    final_output_path = os.path.join(directory, safe_filename)

    try:
        with open(input_path, 'rb') as input_file:
            reader = pypdf.PdfReader(input_file)
            writer = pypdf.PdfWriter()
            
            total_pages = len(reader.pages)
            s_page = max(1, int(start_page))
            e_page = min(total_pages, int(end_page))

            for page_num in range(s_page - 1, e_page):
                try:
                    page = reader.pages[page_num]
                    
                    # Kiểm tra đối tượng trang
                    if page is None or isinstance(page, NullObject):
                        print(f"⚠️ Bỏ qua trang {page_num + 1}: Dữ liệu Null.")
                        continue
                    
                    # Thêm trang vào writer
                    writer.add_page(page)
                    
                except Exception as e:
                    # Bắt lỗi "Null object" phát sinh bên trong add_page của pypdf
                    print(f"⚠️ Lỗi tại trang {page_num + 1}: {e}. Đang bỏ qua...")
                    continue

            # 2. Ghi file nếu có trang hợp lệ
            if len(writer.pages) > 0:
                with open(final_output_path, 'wb') as output_file:
                    writer.write(output_file)
                return True
            else:
                print(f"❌ Không có trang nào hợp lệ cho file: {safe_filename}")
                return False

    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng khi đọc file PDF: {e}")
        return False
def compress_pdf_ghostscript(input_path, output_path, quality='ebook'):
    """
    Nén PDF bằng Ghostscript
    quality options:
    - screen: 72dpi, nhỏ nhất
    - ebook: 150dpi, vừa phải 
    - printer: 300dpi, chất lượng cao
    - prepress: 300dpi, chất lượng tốt nhất
    """
    if not os.path.isfile(input_path):
        print(f"File nguồn không tồn tại: {input_path}")
        return False

    try:
        # Tự động detect Ghostscript path
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
        
        if result.returncode == 0:
            print(f"✅ Nén thành công: {output_path}")
            return True
        else:
            print(f"❌ Lỗi nén PDF: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout khi nén PDF")
        return False
    except FileNotFoundError:
        print("❌ Ghostscript chưa được cài đặt hoặc không tìm thấy")
        return False
    except Exception as e:
        print(f"❌ Lỗi nén PDF: {e}")
        return False

def cut_and_compress_pdf(input_path, output_path, start_page, end_page, compress=True, quality='ebook'):
    """
    Cắt PDF và tùy chọn nén
    """
    try:
        if compress:
            # Tạo file tạm để cắt trước
            temp_path = output_path.replace('.pdf', '_temp.pdf')
            
            # Bước 1: Cắt PDF
            cut_pdf_by_pages(input_path, temp_path, start_page, end_page)
            
            # Bước 2: Nén file đã cắt
            success = compress_pdf_ghostscript(temp_path, output_path, quality)
            
            # Xóa file tạm
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return success
        else:
            # Chỉ cắt, không nén
            cut_pdf_by_pages(input_path, output_path, start_page, end_page)
            return True
            
    except Exception as e:
        print(f"❌ Lỗi cut_and_compress_pdf: {e}")
        return False

def get_file_size_mb(file_path):
    """Lấy kích thước file tính bằng MB"""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    return 0