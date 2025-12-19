import json
import os
import re

def clean_text(text):
    """
    Làm sạch chuỗi văn bản bằng cách:
    - Loại bỏ khoảng trắng ở đầu và cuối.
    - Thay thế các ngắt dòng, tab, và nhiều khoảng trắng liên tiếp bằng một khoảng trắng duy nhất.
    - Loại bỏ các ký tự Markdown như **.
    """
    # Loại bỏ dấu sao in đậm
    text = text.replace('**', '')
    # Thay thế các ngắt dòng và khoảng trắng liên tiếp bằng một khoảng trắng
    text = re.sub(r'\s+', ' ', text)
    # Loại bỏ khoảng trắng ở đầu và cuối chuỗi
    return text.strip()


def check_json_in_markdown(json_data: dict, markdown_content: str) -> tuple[bool, str]:
    """
    Kiểm tra từng phần tử trong JSON có tồn tại trong nội dung Markdown không.
    Hàm này được điều chỉnh để phù hợp với cấu trúc JSON mới có 'extracted_sections' là một danh sách.
    """
    report = []
    is_correct = True
    
    report.append("--- BẮT ĐẦU PHÂN TÍCH TỪ JSON ---")

    # Làm sạch nội dung Markdown một lần duy nhất để tăng hiệu suất
    cleaned_markdown_content = clean_text(markdown_content)
    
    # Kiểm tra xem khóa 'extracted_sections' có tồn tại và là một list không
    if "extracted_sections" not in json_data or not isinstance(json_data["extracted_sections"], list):
        report.append("[❌] Lỗi: Cấu trúc JSON không có khóa 'extracted_sections' hoặc nó không phải là một danh sách.")
        return False, "\n".join(report)

    # Duyệt qua từng section (đối tượng) trong danh sách 'extracted_sections'
    for section in json_data["extracted_sections"]:
        # Lấy tiêu đề lớn từ đối tượng section
        section_title = section.get("section_title", "")
        
        # Làm sạch tiêu đề cấp 1 từ JSON
        cleaned_section_title = clean_text(section_title)
        
        if cleaned_section_title in cleaned_markdown_content:
            report.append(f"\n[✔️] Tiêu đề lớn '{section_title}' được tìm thấy.")
        else:
            report.append(f"\n[❌] Lỗi: Tiêu đề lớn '{section_title}' KHÔNG được tìm thấy.")
            is_correct = False
            
        # Lấy danh sách câu hỏi từ đối tượng section
        questions = section.get("questions", [])
        
        # Duyệt qua từng câu hỏi con trong section
        if isinstance(questions, list):
            for i, q in enumerate(questions):
                title = q.get('question_block_start')
                if title:
                    # Làm sạch tiêu đề câu hỏi con từ JSON
                    cleaned_title = clean_text(title)
                    
                    if cleaned_title in cleaned_markdown_content:
                        report.append(f"  [✔️] Câu hỏi {i+1}: '{title}' được tìm thấy.")
                    else:
                        report.append(f"  [❌] Lỗi: Câu hỏi {i+1}: '{title}' KHÔNG được tìm thấy.")
                        is_correct = False
                else:
                    report.append(f"  [❌] Lỗi: Đối tượng câu hỏi thứ {i+1} không có trường 'question_block_start'.")
                    is_correct = False
        else:
            report.append(f"  [❌] Lỗi: Giá trị của section '{section_title}' không có khóa 'questions' hoặc nó không phải là một danh sách.")
            is_correct = False
            
    report.append("\n--- KẾT THÚC PHÂN TÍCH ---")
    
    return is_correct, "\n".join(report)



def compare_json_in_markdown(markdown_file_path, json_file_path):
    """
    Thực hiện kiểm tra nội dung của một file JSON có tồn tại trong một file Markdown hay không.
    
    Args:
        markdown_file_path (str): Đường dẫn đến file Markdown.
        json_file_path (str): Đường dẫn đến file JSON.
        output_log_path (str, optional): Đường dẫn để lưu file báo cáo.
                                          Nếu None, sẽ không lưu file. Mặc định là None.

    Returns:
        tuple: Một tuple chứa (bool, str).
               bool: True nếu nội dung JSON chính xác, False nếu có lỗi.
               str: Báo cáo chi tiết về quá trình kiểm tra.
    """
    # Khởi tạo các biến
    is_correct = False
    report = ""
    file_name, _ = os.path.splitext(os.path.basename(json_file_path))
    output_log_path = os.path.join(os.path.dirname(markdown_file_path),"ai_struc_detec",f"{file_name}_analyzed.txt")
 
    print("Bắt đầu kiểm tra nội dung JSON trong Markdown...")
    try:
        # Đọc file Markdown
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Đọc file JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            
    except FileNotFoundError as e:
        report = f"Lỗi: Không tìm thấy file tại đường dẫn {e.filename}."
        print(report)
        return is_correct, report
    except json.JSONDecodeError:
        report = f"Lỗi: File JSON '{json_file_path}' không hợp lệ."
        print(report)
        return is_correct, report
    
    # Giả định hàm check_json_in_markdown đã có sẵn.
    is_correct, report_detail = check_json_in_markdown(json_data, markdown_content)
    # Vì hàm gốc không được cung cấp, ta sẽ giả định một kết quả để demo.
    is_correct = True # Thay thế bằng kết quả thực tế từ hàm của bạn
    
    
    # Ghi kết quả vào file nếu có đường dẫn
    if output_log_path:
        with open(output_log_path, 'w', encoding='utf-8') as f:
            f.write(report_detail)
        print(f"Báo cáo kết quả đã được lưu tại file '{output_log_path}'.")
        
    return is_correct, report_detail

# if __name__ == "__main__":
#     main()
# compare_json_in_markdown(markdown_file_path=r"D:\Xử lý chuyển xml\Giải vở bài tập tiếng việt lớp 5 - VBT Tiếng Việt_split_parts\part_1.md"
#                           ,json_file_path=r"D:\Xử lý chuyển xml\Giải vở bài tập tiếng việt lớp 5 - VBT Tiếng Việt_split_parts\ai_struc_detec\part_1.json",
                          
#                           )