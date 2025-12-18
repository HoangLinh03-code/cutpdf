import sys
import os

# Import Class cha từ thư mục common
from modules.common.base_gen_widget import BaseGenWidget

# Import module xử lý logic riêng của KHXH
# (File này chứa hàm response2docx_json, response2docx_dung_sai_json...)
import modules.khxh.response2docxXH as khxh_processor

class KHXHWidget(BaseGenWidget):
    """
    Widget chuyên biệt cho sinh câu hỏi KHXH (Sử, Địa, GDCD...).
    Kế thừa toàn bộ giao diện từ BaseGenWidget.
    """
    def __init__(self):
        # Gọi hàm khởi tạo của cha với 2 tham số quan trọng:
        # 1. prompt_folder_name="khxh" -> Để tìm file testTN.txt trong thư mục modules/khxh/
        # 2. processor_module=khxh_processor -> Để Thread gọi đúng hàm xử lý của KHXH
        super().__init__(
            prompt_folder_name="khxh", 
            processor_module=khxh_processor
        )