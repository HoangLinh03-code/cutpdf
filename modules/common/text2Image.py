import os
from google import genai
from google.genai import types
from modules.common.callAPI import get_vertex_ai_credentials 

def generate_image_from_text(prompt, aspect_ratio="1:1", lang="vi"):
    """
    Sinh ảnh từ prompt text.
    - lang: 'vi' (Mặc định) hoặc 'en'.
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
        
        # --- TỐI ƯU HÓA PROMPT THEO NGÔN NGỮ ---
        if lang == 'en':
            # Instruction tiếng Anh -> Kích hoạt mode vẽ text tiếng Anh chuẩn xác
            final_prompt = f"Generate a high-quality, accurate illustration based on the following description. Ensure all text labels inside the image are in ENGLISH: {prompt}"
        else:
            # Instruction tiếng Việt
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
                print(f"✅ Sinh ảnh thành công")
                return part.inline_data.data

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