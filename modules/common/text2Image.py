import os
import sys
import io

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
    """
    try:
        credentials = get_vertex_ai_credentials()
        project_id = os.getenv("PROJECT_ID")
        location = "global" 

        if not credentials or not project_id:
            print("❌ Lỗi: Thiếu Credentials/Project ID")
            return None

        client = genai.Client(vertexai=True, project=project_id, location=location, credentials=credentials)
        model_name = "gemini-3-pro-image-preview" 

        print(f"🎨 Đang sinh ảnh ({lang.upper()}): {prompt[:50]}...")
        
        if lang == 'en':
            final_prompt = f"Generate a high-quality, accurate illustration based on the following description. Ensure all text labels inside the image are in ENGLISH: {prompt}"
        else:
            final_prompt = f"Vẽ hình ảnh minh họa chính xác cho mô tả sau. Đảm bảo các chữ/nhãn trong hình là TIẾNG VIỆT: {prompt}"

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

        print("❌ API không trả về dữ liệu ảnh.")
        return None
            
    except Exception as e:
        print(f"❌ Lỗi sinh ảnh: {str(e)}")
        return None

def get_image_size_for_aspect_ratio(aspect_ratio, base_width_inches=3.0):
    try:
        w, h = map(float, aspect_ratio.split(":"))
        return base_width_inches, base_width_inches * (h / w)
    except:
        return base_width_inches, base_width_inches

# ============================================================
# TEST MÔ ĐUN
# ============================================================
if __name__ == "__main__":
    from dotenv import load_dotenv
    env_path = os.path.join(project_root, ".env.gen")
    load_dotenv(env_path, override=True)

    print("--- TEST SINH VÀ NÉN ẢNH ---")
    test_prompt = "Một cuốn sách lập trình Python đặt trên bàn làm việc."
    image_data = generate_image_from_text(test_prompt)

    if image_data:
        test_output_path = os.path.join(current_dir, "test_image_compressed.jpg")
        with open(test_output_path, "wb") as f:
            f.write(image_data)
        print(f"🎉 Test thành công! Đã lưu: {test_output_path}")