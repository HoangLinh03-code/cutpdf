import json
import os
import vertexai
import io
import time
import multiprocessing
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from PIL import Image
from modules.chuyendang.config import ARRAY_BASED_SCHEMA
from modules.chuyendang.ai_handle.checkjson_structure import compare_json_in_markdown

# Tải các biến môi trường từ file .env
load_dotenv()

def generate_vertex_ai_token(service_account_data):
    """Generates a Vertex AI access token using service account data."""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            service_account_data,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        if not credentials.valid:
            credentials.refresh(Request())
        token = credentials.token
        return token
    except Exception as e:
        return f"Lỗi khi tạo token Vertex AI: {e}"

# --- Khởi tạo biến từ file .env và tạo token ---

key = generate_vertex_ai_token({
    "type": "service_account",
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY"),
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_x509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_x509_CERT_URL"),
    "universe_domain": os.getenv("UNIVERSE_DOMAIN")
})

def handle_gemini_model(prompt_content, vertex_ai_access_token, model_name: str = "gemini-2.5-pro", image_links=None, role: str = None, log_messages=None, response_schema = None):
    """
    Xử lý gọi các mô hình Gemini trên Vertex AI.
    Hàm này hỗ trợ đầu vào đa phương tiện và schema đầu ra cụ thể.
    """
    if log_messages is None:
        log_messages = []

    project_id = os.getenv("PROJECT_ID")
    region = os.getenv("REGION")

    if not project_id:
        log_messages.append("Lỗi: Không tìm thấy Project ID trong file .env.\n")
        return None
    if not region:
        region = "us-central1"
        log_messages.append(f"Cảnh báo: Không tìm thấy Region trong file .env, đang sử dụng mặc định: {region}\n")

    try:
        credentials = Credentials(token=vertex_ai_access_token)
        vertexai.init(project=project_id, location=region, credentials=credentials)
        model = GenerativeModel(model_name)
        
        # Cấu hình GenerationConfig, bao gồm response_schema
        generation_config = GenerationConfig(
            temperature=0.5,
            top_p=0.8,
            response_mime_type="application/json",
            response_schema=response_schema
        )
        
        # Chuẩn bị nội dung cho lời gọi API
        contents = []
        if role:
            processed_prompt_text = f"Với vai trò là một {role}, hãy phân tích nội dung được cung cấp."
        else:
            processed_prompt_text = ""

        if isinstance(prompt_content, list):
            processed_prompt_text += "".join([part['text'] for part in prompt_content if 'text' in part])
        else:
            processed_prompt_text += prompt_content
        
        contents.append(processed_prompt_text)

        # Xử lý hình ảnh nếu có
        allowed_image_formats = ['png', 'jpeg', 'jpg', 'gif', 'webp']
        if image_links:
            if os.path.exists(image_links):
                try:
                    img = Image.open(image_links)
                    format = img.format.lower() if img.format else None
                    if format not in allowed_image_formats:
                        log_messages.append(f"Đang chuyển đổi ảnh '{image_links}' từ {format} sang WEBP.\n")
                        img_output = io.BytesIO()
                        img.save(img_output, format='WEBP')
                        img_output.seek(0)
                        img_bytes = img_output.getvalue()
                    else:
                        with open(image_links, "rb") as image_file:
                            img_bytes = image_file.read()
                    
                    image_part = Part.from_data(img_bytes, mime_type=f'image/{format}')
                    contents.append(image_part)
                except Exception as image_err:
                    log_messages.append(f"Lỗi khi xử lý hình ảnh '{image_links}': {image_err}\n")
            else:
                log_messages.append(f"Cảnh báo: Không tìm thấy file hình ảnh tại '{image_links}'\n")

        log_messages.append(f"Đang gọi Vertex AI Gemini model '{model_name}' với prompt: ...\n")
        response = model.generate_content(contents, generation_config=generation_config, stream=False)

        if response and response.text:
            return response.text.strip()
        else:
            log_messages.append(f"Cảnh báo (Vertex AI): Không có phản hồi văn bản từ mô hình '{model_name}'\n")
            return None

    except Exception as e:
        log_messages.append(f"Lỗi khi gọi API Vertex AI Gemini cho mô hình '{model_name}': {e}\n")
        return None

def process_markdown_with_vertex_ai(markdown_file_path: str) -> tuple[str, str, list[str]] | tuple[str, None, list[str]]:
    """
    Xử lý một file Markdown bằng Vertex AI để trích xuất các tiêu đề thành cấu trúc JSON.
    Hàm này được thiết kế để chạy trong một tiến trình riêng.

    Args:
        markdown_file_path: Đường dẫn tới file Markdown cần xử lý.

    Returns:
        Một tuple chứa (đường dẫn file Markdown, đường dẫn file JSON kết quả, danh sách các log).
        Đường dẫn file JSON sẽ là None nếu có lỗi.
    """
    log_messages = []
    
    if key is None:
        log_messages.append(f"Lỗi: Không thể xác thực với Vertex AI. Bỏ qua file '{markdown_file_path}'.")
        return (markdown_file_path, None, log_messages)

    # Kiểm tra xem file có tồn tại không
    if not os.path.exists(markdown_file_path):
        log_messages.append(f"Lỗi: Không tìm thấy file tại đường dẫn '{markdown_file_path}'.")
        return (markdown_file_path, None, log_messages)
    
    # Tạo đường dẫn output_json_path
    file_name, _ = os.path.splitext(os.path.basename(markdown_file_path))
    output_json_path = os.path.join(os.path.dirname(markdown_file_path), "ai_struc_detec", f"{file_name}.json")
    try:
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        log_messages.append(f"Đã tạo FILE JSON: {os.path.dirname(output_json_path)}\n")
        time.sleep(10)
        log_messages.append(f"Đang xử lý file: {os.path.basename(markdown_file_path)}...\n")
    except Exception as e:
        log_messages.append(f"Lỗi khi tạo file json: {e}\n")
    try:
        # Định nghĩa prompt dựa trên yêu cầu của bạn
        prompt_text = """
        Bạn là một chuyên gia xử lý dữ liệu Markdown. Nhiệm vụ của bạn là phân tích một văn bản và trích xuất các tiêu đề thành một cấu trúc JSON đã định nghĩa.

        Hướng dẫn chi tiết:
        Cấp độ 1: Xác định các section lớn. Tiêu đề bắt đầu bằng dấu thăng (#) sẽ là các khóa chính (key) của đối tượng JSON,trong trường hợp không có tiêu đề thì sẽ để là "".
        Cấp độ 2: Trong mỗi section lớn, tìm kiếm các khối câu hỏi con bắt đầu bằng các dấu hiệu như "Trả lời câu hỏi...","Đề bài", HĐ,....Trích xuất tiêu đề này và đưa vào mảng của khóa tương ứng, dưới khóa "question_block_start".
        Lưu ý:  Các câu hỏi thường có cấu trúc sau câu hỏi, đáp án, hướng dẫn giải. 
        Bạn hãy phân tích file Markdown được cung cấp và chỉ trả về đối tượng JSON hợp lệ, không có nội dung giải thích nào khác.
        """
        
        # Đọc nội dung file Markdown để gửi đi cùng prompt
        with open(markdown_file_path, 'r', encoding='utf-8') as file:
            markdown_content = file.read()
        with open("prompt_chonDang.txt", 'r', encoding='utf-8') as file:
            PROMT_CHON_DANG = file.read()
        print(ARRAY_BASED_SCHEMA)
        # Gửi prompt và nội dung file qua hàm xử lý chung
        response_text = handle_gemini_model(
            prompt_content=f"{prompt_text}\nyÊU CẦU CHỌN DẠNG{PROMT_CHON_DANG} \nNội dung Markdown:\n---\n{markdown_content}\n---",
            vertex_ai_access_token=key,
            model_name="gemini-2.5-pro",
            log_messages=log_messages,
            response_schema=ARRAY_BASED_SCHEMA
        )

        if not response_text:
            return (markdown_file_path, None, log_messages)

        # Phân tích kết quả JSON
        json_string = response_text
        if json_string.startswith('```json') and json_string.endswith('```'):
            json_string = json_string[7:-3].strip()
        json_object = json.loads(json_string)
        print(json_object)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(json_object, f, ensure_ascii=False, indent=4)
        
        log_messages.append(f"✔️ Kết quả từ AI đã được lưu thành công tại '{output_json_path}'.\n")
        return (markdown_file_path, output_json_path, log_messages)

    except json.JSONDecodeError as e:
        log_messages.append(f"Lỗi: Không thể phân tích chuỗi JSON trả về cho file '{markdown_file_path}'. Lỗi: {e}\n")
        return (markdown_file_path, None, log_messages)
    except Exception as e:
        log_messages.append(f"Đã xảy ra lỗi không xác định khi xử lý file '{markdown_file_path}': {e}\n")
        return (markdown_file_path, None, log_messages)

def process_folder_of_markdown_files(folder_path: str, log_file_path: str = "batch_processing_log.txt",num_processes: int = multiprocessing.cpu_count()) -> None:
    """
    Xử lý tất cả các file Markdown trong một thư mục cụ thể bằng multiprocessing.
    Ghi tất cả log vào một file duy nhất sau khi hoàn thành.
    
    Args:
        folder_path: Đường dẫn đến thư mục chứa các file Markdown.
        log_file_path: Đường dẫn tới file log để lưu kết quả. Mặc định là "batch_processing_log.txt".
    """
    if not os.path.isdir(folder_path):
        print(f"Lỗi: Đường dẫn '{folder_path}' không phải là một thư mục hợp lệ.")
        return

    print(f"Bắt đầu xử lý hàng loạt các file Markdown trong thư mục: '{folder_path}'")
    print(f"Toàn bộ log sẽ được lưu vào file '{log_file_path}' sau khi hoàn thành.")
    
    markdown_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.md') and os.path.isfile(os.path.join(folder_path, f))]
    
    if not markdown_files:
        print("Không tìm thấy file Markdown nào để xử lý.")
        return
        
    print(f"Tìm thấy {len(markdown_files)} file Markdown để xử lý.")
    
    start_time = time.time()
    try:
        num_processes = num_processes
        print(f"Sử dụng {num_processes} tiến trình để xử lý...")
        
        with multiprocessing.Pool(processes=num_processes) as pool:
            results = pool.map(process_markdown_with_vertex_ai, markdown_files)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write(f"--- Báo cáo xử lý hàng loạt ({time.ctime()}) ---\n")
            log_file.write(f"Tổng thời gian xử lý: {total_time:.2f} giây.\n\n")

            for markdown_file_path, json_file_path, log_messages in results:
                filename = os.path.basename(markdown_file_path)
                log_file.write(f"### Báo cáo chi tiết cho file: {filename}\n")
                
                # Ghi các log từ tiến trình con
                log_file.write("".join(log_messages))
                
                if json_file_path:
                    # Ghi báo cáo so sánh vào file log
                    is_correct, report = compare_json_in_markdown(markdown_file_path, json_file_path=json_file_path)
                    log_file.write(f"\n{report}\n")
                    if is_correct:
                        log_file.write("  [✔️] Kiểm tra cấu trúc JSON thành công.\n")
                    else:
                        log_file.write("  [❌] Kiểm tra cấu trúc JSON thất bại.\n")
                else:
                    log_file.write("  [❌] Trích xuất JSON thất bại.\n")
                log_file.write("---" * 20 + "\n\n")
        output_json_dir = os.path.join(os.path.dirname(markdown_file_path), "ai_struc_detec")
        print(output_json_dir)
        return output_json_dir  # Trả về đường dẫn thư mục chứa JSON kết quả
    except Exception as e:
        print(f"\n--- Đã xảy ra lỗi trong quá trình xử lý hàng loạt: {e} ---")
        
    print("\n--- Hoàn thành xử lý hàng loạt ---")
    print(f"Toàn bộ log chi tiết đã được lưu vào file '{log_file_path}'.")

    
