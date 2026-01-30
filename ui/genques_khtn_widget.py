"""
GenQues Widget cho KHOA HỌC TỰ NHIÊN (Toán, Lý, Hóa, Sinh)
"""
from ui.gen_ques import GenQuesWidget
from modules.khtn import response2docxTN as khtn_processor

class GenQuesKHTNWidget(GenQuesWidget):
    """
    Widget chuyên biệt cho sinh câu hỏi KHTN.
    Kế thừa toàn bộ giao diện từ GenQuesWidget.
    """
    def __init__(self):
        super().__init__(
            prompt_folder_name="khtn", 
            processor_module=khtn_processor,
            widget_title="TẠO CÂU HỎI BẰNG AI"
        )