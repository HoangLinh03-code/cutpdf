# config/settings.py
import os
import sys
from dotenv import load_dotenv
from google.oauth2 import service_account

# 1. Xác định đường dẫn gốc
if getattr(sys, 'frozen', False):
    # Nếu chạy từ file EXE đã đóng gói
    # sys._MEIPASS là thư mục tạm chứa các file đã được nhúng (add-data)
    base_path = sys._MEIPASS
else:
    # Nếu chạy code Python bình thường
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. Load file .env và in ra đường dẫn để kiểm tra (Debug)
env_path = os.path.join(base_path, '.env')
print(f"📂 Đang đọc file .env tại: {env_path}")
load_dotenv(env_path)

class Config:
    MATHPIX_APP_KEY = os.getenv("MATHPIX_APP_KEY")
    MATHPIX_APP_ID = os.getenv("MATHPIX_APP_ID")
    GOOGLE_PROJECT_ID = os.getenv("PROJECT_ID")

    @staticmethod
    def get_google_credentials():
        private_key = os.getenv("PRIVATE_KEY")
        
        # --- QUAN TRỌNG: Kiểm tra và xử lý Key ---
        if not private_key:
            print("❌ Lỗi: Không tìm thấy PRIVATE_KEY trong .env")
            return None
            
        # FIX LỖI: Thay thế ký tự \n dạng chuỗi thành xuống dòng thật
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
        # ------------------------------------------

        service_account_info = {
            "type": os.getenv("TYPE"),
            "project_id": os.getenv("PROJECT_ID"),
            "private_key_id": os.getenv("PRIVATE_KEY_ID"),
            "private_key": private_key,  # Sử dụng key đã xử lý
            "client_email": os.getenv("CLIENT_EMAIL"),
            "client_id": os.getenv("CLIENT_ID"),
            "auth_uri": os.getenv("AUTH_URI"),
            "token_uri": os.getenv("TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("UNIVERSE_DOMAIN")
        }

        # Debug: Kiểm tra xem client_email có load được không
        if not service_account_info["client_email"]:
            print("❌ Lỗi: Không đọc được CLIENT_EMAIL từ .env")
            return None

        try:
            creds = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=[
                    "https://www.googleapis.com/auth/cloud-platform",
                    "https://www.googleapis.com/auth/drive.readonly"
                ]
            )
            print("✅ Tạo Google Credentials thành công!")
            return creds
        except Exception as e:
            print(f"❌ Lỗi tạo credentials (thường do sai format Private Key): {e}")
            return None

credential_manager = Config()