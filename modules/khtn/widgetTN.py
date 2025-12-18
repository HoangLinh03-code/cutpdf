import sys
import os

# Import Class cha từ thư mục common
from modules.common.base_gen_widget import BaseGenWidget

# Import module xử lý logic riêng của KHTN (ToolGen cũ)
# Lưu ý: Đảm bảo bạn đã copy file response2docx.py của ToolGen vào modules/khtn/process/
import modules.khtn.response2docxTN as khtn_processor

class KHTNWidget(BaseGenWidget):
    """
    Widget chuyên biệt cho sinh câu hỏi KHTN (Toán, Lý, Hóa, Sinh).
    Kế thừa toàn bộ giao diện từ BaseGenWidget.
    """
    def __init__(self):
        # Gọi hàm khởi tạo của cha:
        # 1. prompt_folder_name="khtn" -> Để tìm file testTN.txt trong thư mục modules/khtn/
        # 2. processor_module=khtn_processor -> Để Thread gọi đúng hàm xử lý của KHTN
        super().__init__(
            prompt_folder_name="khtn", 
            processor_module=khtn_processor
        )