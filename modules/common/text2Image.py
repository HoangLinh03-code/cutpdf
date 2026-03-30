import os
import sys
import io
import time
import random

# --- XỬ LÝ ĐƯỜNG DẪN ĐỂ TRÁNH LỖI MODULE ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ------------------------------------------

from google import genai
from google.genai import types
from PIL import Image
from modules.common.callAPI import get_vertex_ai_credentials 

def compress_image_to_min(image_bytes, max_size=(1024,1024), quality=75):
    """
    Ép dung lượng ảnh xuống mức tối thiểu dùng cho tài liệu Word.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Chuyển đổi RGBA/P sang RGB để lưu được dưới dạng JPEG nén
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Thu nhỏ kích thước ảnh
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Xuất ảnh ra buffer mới
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="JPEG", quality=quality, optimize=True)
        
        return output_buffer.getvalue()
    except Exception as e:
        print(f"⚠️ [CẢNH BÁO] Lỗi nén ảnh, sử dụng ảnh gốc: {e}")
        return image_bytes

def generate_image_from_text(prompt, aspect_ratio="1:1", lang="vi"):
    """
    Sinh ảnh từ prompt text và trả về byte ảnh đã được nén tối ưu.
    Có hỗ trợ Phân luồng Model theo ngôn ngữ và Fallback khi bị lỗi 429.
    """
    try:
        credentials = get_vertex_ai_credentials()
        project_id = os.getenv("PROJECT_ID")
        location = "global" 

        if not credentials or not project_id:
            print("❌ Lỗi: Thiếu Credentials/Project ID")
            return None

        client = genai.Client(vertexai=True, project=project_id, location=location, credentials=credentials)
        
        print(f"🎨 Đang sinh ảnh ({lang.upper()}): {prompt[:50]}...")
        
        # --- PHÂN LUỒNG MODEL & PROMPT THEO NGÔN NGỮ ---
        if lang == 'en':
            final_prompt = f"Generate a high-quality, accurate illustration based on the following description. Ensure all text labels inside the image are in ENGLISH: {prompt}"
            # Tiếng Anh chỉ sử dụng 2.5 flash
            models_to_try = [
                "gemini-2.5-flash-image"
            ]
        else:
            final_prompt = f"Vẽ hình ảnh minh họa chính xác cho mô tả sau. Đảm bảo các chữ/nhãn trong hình là TIẾNG VIỆT: {prompt}"
            # Tiếng Việt ưu tiên 3 pro, fallback sang 3.1 flash preview nếu 429
            models_to_try = [
                "gemini-3-pro-image-preview", 
                "gemini-3.1-flash-image-preview"
            ]
        
        max_retries = 3   # Khai báo số lần thử lại tối đa
        base_delay = 8    # Thời gian chờ cơ sở (giây)

        # Lặp qua từng model trong danh sách đã được phân luồng
        for model_name in models_to_try:
            print(f"🔄 Đang gọi API với model: {model_name}")
            
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=final_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
                            candidate_count=1,
                            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                        )
                    )
                    
                    for part in response.parts:
                        if part.inline_data and part.inline_data.data:
                            raw_bytes = part.inline_data.data
                            compressed_bytes = compress_image_to_min(raw_bytes)
                            print(f"✅ Sinh & Nén ảnh thành công ({len(raw_bytes)/1024:.1f} KB -> {len(compressed_bytes)/1024:.1f} KB)")
                            return compressed_bytes

                    print(f"❌ API ({model_name}) không trả về dữ liệu ảnh. Chuyển model dự phòng...")
                    break # Thoát khỏi retry để đổi sang model tiếp theo (nếu có)

                except Exception as api_err:
                    error_str = str(api_err).lower()
                    
                    # Xử lý riêng biệt cho lỗi 429 / Quota
                    if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                        if attempt < max_retries - 1:
                            sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0.1, 1.5)
                            print(f"⚠️ [Lỗi 429 - {model_name}] Quá tải API. Thử lại lần {attempt + 1}/{max_retries} sau {sleep_time:.2f}s...")
                            time.sleep(sleep_time)
                            continue # Thử lại với chính model này
                        else:
                            print(f"❌ Hết lượt thử lại ({max_retries} lần) cho {model_name}.")
                            break # Thoát vòng lặp retry, vòng lặp ngoài sẽ thử model tiếp theo (nếu có)
                    else:
                        print(f"❌ Lỗi ({model_name} - Không thể phục hồi): {api_err}. Thử model khác...")
                        break # Nếu là lỗi khác 429 (như sai prompt, safety filter chặn), thử luôn model tiếp theo
                        
        print("❌ Đã thử tất cả các model nhưng đều thất bại do lỗi API/Quota.")
        return None
            
    except Exception as e:
        print(f"❌ Lỗi sinh ảnh toàn cục: {str(e)}")
        return None

def get_image_size_for_aspect_ratio(aspect_ratio, base_width_inches=3.0):
    try:
        w, h = map(float, aspect_ratio.split(":"))
        return base_width_inches, base_width_inches * (h / w)
    except:
        return base_width_inches, base_width_inches

if __name__ == "__main__":
    from dotenv import load_dotenv
    env_path = os.path.join(project_root, ".env.gen")
    load_dotenv(env_path, override=True)

    print("--- TEST SINH VÀ NÉN ẢNH (TIẾNG ANH) ---")
    test_prompt_en = "A tiny robot writing Python code on a laptop, bright 3D cartoon style."
    image_data_en = generate_image_from_text(test_prompt_en, lang="en")

    if image_data_en:
        test_output_path_en = os.path.join(current_dir, "test_image_en_compressed.jpg")
        with open(test_output_path_en, "wb") as f:
            f.write(image_data_en)
        print(f"🎉 Test EN thành công! Đã lưu: {test_output_path_en}\n")

    print("--- TEST SINH VÀ NÉN ẢNH (TIẾNG VIỆT) ---")
    test_prompt_vi = "Một cuốn sách lập trình Python đặt trên bàn làm việc."
    image_data_vi = generate_image_from_text(test_prompt_vi, lang="vi")

    if image_data_vi:
        test_output_path_vi = os.path.join(current_dir, "test_image_vi_compressed.jpg")
        with open(test_output_path_vi, "wb") as f:
            f.write(image_data_vi)
        print(f"🎉 Test VI thành công! Đã lưu: {test_output_path_vi}")