import os
import sys
from dotenv import load_dotenv

def setup_chuyen_dang_env():
    # 1. Thêm đường dẫn module vào sys.path để các import nội bộ hoạt động
    module_root = os.path.dirname(os.path.abspath(__file__))
    if module_root not in sys.path:
        sys.path.insert(0, module_root)
    
    # 2. Nạp file .env riêng của module này
    env_path = os.path.join(module_root, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    
    # 3. Kỹ thuật "Virtual CWD": Vì code gốc dùng open("file.txt")
    # Chúng ta sẽ thay đổi thư mục làm việc hiện tại sang đây
    # Lưu ý: Sẽ được gọi trước khi khởi tạo Widget
    os.chdir(module_root)