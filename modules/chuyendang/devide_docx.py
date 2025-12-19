import os
import pypandoc
import re
from docx import Document # Chỉ dùng để tạo file DOCX mẫu nếu cần
import win32com.client # Dùng cho tiền xử lý DOCX trên Windows
import shutil
import uuid

def preprocess_docx(docx_path):
    """
    Mở và lưu lại file .docx bằng MS Word để chuẩn hóa cấu trúc XML.
    Chỉ hoạt động trên Windows và yêu cầu cài đặt Microsoft Word.
    """
    try:
        word = win32com.client.Dispatch("Word.Application")
        doc = word.Documents.Open(os.path.abspath(docx_path))
        doc.Save()
        doc.Close()
        word.Quit()
        print(f"Đã tiền xử lý file: '{docx_path}'")
    except Exception as e:
        print(f"Lỗi khi tiền xử lý file .docx (chỉ hoạt động trên Windows với MS Word): {e}")
        print("Bỏ qua bước tiền xử lý và tiếp tục.")

def convert_docx_to_md(docx_path: str, output_dir: str = "temp_md"):
    """
    Chuyển đổi file DOCX sang Markdown bằng Pandoc, trích xuất hình ảnh.

    Args:
        docx_path (str): Đường dẫn đến file DOCX đầu vào.
        output_dir (str): Thư mục để lưu file Markdown tạm thời và ảnh.

    Returns:
        tuple: (Đường dẫn file Markdown, Đường dẫn thư mục media) nếu thành công,
               ngược lại (None, None).
    """
    if not os.path.exists(docx_path):
        print(f"Lỗi: File '{docx_path}' không tồn tại.")
        return None, None

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(docx_path))[0]
    md_path = os.path.join(output_dir, base_name + '.md')
    media_dir = os.path.join(output_dir, "media")

    print(f"Bắt đầu chuyển đổi file DOCX sang Markdown: '{docx_path}'...")

    # --extract-media=media sẽ tạo thư mục 'media' trong output_dir
    extra_args = [f'--extract-media={media_dir}']
    output_format = 'markdown'

    try:
        pypandoc.convert_file(
            source_file=docx_path,
            to=output_format,
            outputfile=md_path,
            extra_args=extra_args,
            # encoding='utf-8'
        )
        print("-" * 30)
        print("🎉 Chuyển đổi DOCX sang Markdown thành công!")
        print(f"✔️ File Markdown đã được lưu tại: '{md_path}'")
        print(f"✔️ Ảnh đã được lưu trong thư mục: '{media_dir}'")
        print("-" * 30)
        remove_md_alt_text(md_path)
        return md_path, media_dir
    except Exception as e:
        print(f"Đã xảy ra lỗi khi chuyển đổi DOCX sang Markdown: {e}")
        print("Hãy đảm bảo Pandoc đã được cài đặt và có trong PATH.")
        return None, None
def remove_md_alt_text(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Regex: ![alt text](image_path) => ![](image_path)
    content = re.sub(r'!\[[^\]]*\]\(([^)]+)\)', r'![](\1)', content)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
import os
import re

def split_markdown_by_patterns(md_path: str, stop_patterns: list, output_dir: str = "output_parts"):
    """
    Chia file Markdown thành nhiều file con dựa trên các stop patterns.

    Args:
        md_path (str): Đường dẫn đến file Markdown đầu vào.
        stop_patterns (list): Danh sách các chuỗi văn bản đánh dấu điểm tách.
        output_dir (str): Thư mục để lưu các file Markdown con.

    Returns:
        list: Danh sách các đường dẫn đến các file Markdown con đã tạo.
    """
    if not os.path.exists(md_path):
        print(f"Lỗi: File Markdown '{md_path}' không tồn tại.")
        return []

    os.makedirs(output_dir, exist_ok=True)
    parts = []
   
    print(f"Bắt đầu chia file Markdown: '{md_path}' theo các stop patterns: {stop_patterns}")

    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Xử lý trường hợp stop_patterns rỗng
    if not stop_patterns:
        print("Danh sách stop patterns rỗng, sẽ tạo một file duy nhất.")
        part_filename = os.path.join(output_dir, "part_1.md")
        with open(part_filename, 'w', encoding='utf-8') as out_f:
            out_f.writelines(lines)
        parts.append(part_filename)
        print(f"Đã tạo file Markdown con: '{part_filename}'")

    else:
        # Tạo regex pattern từ danh sách stop_patterns
        combined_pattern = re.compile('|'.join(re.escape(p) for p in stop_patterns), re.IGNORECASE)
        current_part_content = []
        part_index = 1

        for line in lines:
            # Nếu tìm thấy stop pattern và phần hiện tại không rỗng, lưu phần hiện tại
            if combined_pattern.search(line) and current_part_content:
                part_filename = os.path.join(output_dir, f"part_{part_index}.md")
                with open(part_filename, 'w', encoding='utf-8') as out_f:
                    out_f.writelines(current_part_content)
                parts.append(part_filename)
                print(f"Đã tạo file Markdown con: '{part_filename}'")
                
                current_part_content = []  # Reset nội dung cho phần mới
                part_index += 1
            
            current_part_content.append(line)

        # Lưu phần cuối cùng còn lại (nếu có)
        if current_part_content:
            part_filename = os.path.join(output_dir, f"part_{part_index}.md")
            with open(part_filename, 'w', encoding='utf-8') as out_f:
                out_f.writelines(current_part_content)
            parts.append(part_filename)
            print(f"Đã tạo file Markdown con: '{part_filename}' (phần cuối cùng)")

    print("-" * 30)
    print("✅ Chia file Markdown hoàn tất.")
    print("-" * 30)
    return parts

def convert_md_to_docx(md_path: str, media_dir: str, output_dir: str = "output_docx"):
    """
    Chuyển đổi file Markdown sang DOCX bằng Pandoc, bao gồm cả hình ảnh.

    Args:
        md_path (str): Đường dẫn đến file Markdown đầu vào.
        media_dir (str): Thư mục chứa các file ảnh được trích xuất.
        output_dir (str): Thư mục để lưu các file DOCX con.

    Returns:
        str: Đường dẫn file DOCX đã tạo nếu thành công, ngược lại None.
    """
    if not os.path.exists(md_path):
        print(f"Lỗi: File Markdown '{md_path}' không tồn tại.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(md_path))[0]
    docx_path = os.path.join(output_dir, base_name + '.docx')

    print(f"Bắt đầu chuyển đổi Markdown sang DOCX: '{md_path}'...")

    # --resource-path sẽ giúp Pandoc tìm thấy các ảnh trong thư mục media
    # Đảm bảo đường dẫn media_dir là tương đối hoặc tuyệt đối chính xác
    extra_args = [f'--resource-path={media_dir}',
                #   '--reference-doc=C:\\Users\\Administrator\\Downloads\\Xử lý chuyển xml\\reference.docx'
]
    output_format = 'docx'

    try:
        pypandoc.convert_file(
            source_file=md_path,
            to=output_format,
            outputfile=docx_path,
            extra_args=extra_args,
            # encoding='utf-8'
        )
       
        print(f"✔️ File DOCX đã được lưu tại: '{docx_path}'")
        return docx_path
    except Exception as e:
        print(f"Đã xảy ra lỗi khi chuyển đổi Markdown sang DOCX: {e}")
        return None
    
def split_docx_to_parts(input_docx_file, stop_patterns,temp_md_dir = "temp_markdown_conversion"):
    """
    Tiền xử lý, chuyển đổi DOCX sang Markdown, tách Markdown thành các phần nhỏ.
    Trả về đường dẫn thư mục chứa các file Markdown parts.
    """
    # preprocess_docx(input_docx_file)

    
    md_file, media_folder = convert_docx_to_md(input_docx_file, temp_md_dir)

    if md_file:
        base_name = os.path.splitext(os.path.basename(md_file))[0]
        output_md_parts_dir = f"{base_name}_split_parts"
        output_docx_parts_dir = f"{base_name}_parts_docx_files"
        output_docx_processed_dir = f"{base_name}_processed_docx_files"
        split_md_files = split_markdown_by_patterns(md_file, stop_patterns, output_md_parts_dir)
        for part_md_file in split_md_files:
            convert_md_to_docx(part_md_file, media_folder, output_docx_parts_dir)
        # shutil.rmtree(md_file)  # Xóa file Markdown tạm thời
        # shutil.rmtree(media_folder)  # Xóa thư mục media tạm thời
        # shutil.rmtree(temp_md_dir)  # Xóa thư mục media tạm thời
        
        return output_docx_processed_dir,output_docx_parts_dir,output_md_parts_dir,md_file, media_folder,temp_md_dir
    else:
        return None

# # # Ví dụ sử dụng:
# if __name__ == "__main__":
#     subject = "Toán"
#     level = "Lớp 5"
#     input_docx_file = r"D:\Xử lý chuyển xml\input_docx\Giải vở bài tập tiếng việt lớp 5 - VBT Tiếng Việt.docx"
#     stop_patterns = [
#        "Giải Bài 1. Trạng nguyên nhỏ tuổi VBT Tiếng Việt 5 tập 1 Chân trời sáng tạo",
#        "Giải Tiết 3 VBT Tiếng Việt 5 tập 1 Chân trời sáng tạo",
#        "Giải Bài 1. Tiếng rao đêm VBT Tiếng Việt 5 tập 1 Chân trời sáng tạo",
#        "Giải Bài 6: Thiên đường của các loài động vật hoang dã  VBT Tiếng Việt 5 tập 2 Chân trời sáng tạo",
#        "Giải Bài 5. Lớp học trên đường VBT Tiếng Việt 5 tập 1 Chân trời sáng tạo",
#        "Giải Bài 7. Về ngôi nhà đang xây VBT Tiếng Việt 5 tập 1 Chân trời sáng tạo",
#        "Giải Bài 1: Sự tích con Rồng cháu Tiên  VBT Tiếng Việt 5 tập 2 Chân trời sáng tạo",
#        "Giải Bài 4: Miền đất xanh VBT Tiếng Việt 5 tập 2 Chân trời sáng tạo",
#     ]
#     output_md_parts_dir = split_docx_to_parts(input_docx_file, stop_patterns)
#     print(f"Thư mục chứa các file Markdown parts: {output_md_parts_dir}")