"""
GenQues Widget cho KHOA HỌC XÃ HỘI (Sử, Địa, GDCD)
"""
from ui.gen_ques import GenQuesWidget
from modules.khxh import response2docxXH as khxh_processor

class GenQuesKHXHWidget(GenQuesWidget):
    """
    Widget chuyên biệt cho sinh câu hỏi KHXH.
    Kế thừa toàn bộ giao diện từ GenQuesWidget.
    """
    def __init__(self):
        super().__init__(
            prompt_folder_name="khxh", 
            processor_module=khxh_processor,
            widget_title="Sinh Câu Hỏi KHXH"
        )