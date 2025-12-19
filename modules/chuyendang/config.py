  # Các từ khóa dùng để xác định bắt đầu một section mới
SECTION_KEYWORDS = [
    "Câu", "CH", "BT", "LT", "Thực hành Câu", "Chuẩn bị", "Trong khi đọc", "Sau khi đọc", "Luyện tập", "Hoạt động", "Bài", "Bài tập",
    "Phần", "Toán lớp", "Nội dung bài đọc", "Mục", "Trắc nghiệm", "Dao động điều hòa", "Mô tả sóng", "LỰC TƯƠNG TÁC",
]

REFERENCE_PATTERN = r"\btrang\s+\d+\s+SGK\b"
DECIMAL_SECTION_PATTERN = r"^\d+[\.,]\d+\b"
STANDALONE_NUMBER_PATTERN = r"^\d+$"

HEADING_STYLE_NAMES = [
    "Heading 1", "heading 1", "Tiêu đề 1", "Tiêu đề1",
    "Heading 2", "heading 2", "Tiêu đề 2", "Tiêu đề2",
    "Heading 3", "heading 3", "Tiêu đề 3", "Tiêu đề3",
    "Heading 4", "heading 4", "Tiêu đề 4", "Tiêu đề4",
]
MAIN_TITLE_STYLES = [
    "Heading 1", "heading 1", "Tiêu đề 1", "Tiêu đề1",
]
SUB_TITLE_STYLES = [
    "Heading 2", "heading 2", "Tiêu đề 2", "Tiêu đề2",
]



# Từ khóa xác định phần phương pháp giải
METHOD_HEADINGS_ORIGINAL = [
    "Phương pháp giải - Xem chi tiết",
    "Phương pháp giải",
    "Phương pháp",
]

METHOD_HEADING_NEW = "####"

# Từ khóa xác định phần lời giải (bản gốc)
SOLUTION_HEADINGS_ORIGINAL = [
    "Lời giải chi tiết",
    "Trả lời",
]

ARRAY_BASED_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "extracted_sections": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "section_title": {"type": "STRING"},
                    "questions": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "question_block_start": {
                                    "type": "STRING",
                                    "description": "Là chỉ số, nhãn hoặc cụm từ định danh đứng ngay trước nội dung của một câu hỏi đơn lẻ. Nó đánh dấu điểm bắt đầu của một khối câu hỏi hoàn chỉnh (bao gồm nội dung, đáp án và lời giải). Ví dụ: 'Câu 1:', 'Bài 2.', '1)', 'a)', hoặc 'Đề bài:'."
                                },
                                 "type_ques": {
                                    "type": "STRING",
                                    "description": "Type of question block, TRUE FALSE :ĐS , MULTIPLE CHOICE:DD, 1 ANSWER ANSWER:TN, SHORT ANSWER:TLN",
                                    "enum": ["ĐS", "DD", "TN", "TLN"]
                                }
                            },
                             "required": ["question_block_start", "type_ques"]
                        }
                    }
                }
            }
        }
    }
}
# 2. Schema cho Vertex AI response format
VERTEX_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": {
                                "type": "string",
                                "description": "JSON string matching the OUTPUT_SCHEMA format"
                            }
                        }
                    ]
                }
            }
        ]
    }
}
# Từ khóa xác định phần lời giải (sau khi thay thế)
SOLUTION_HEADING_NEW = "Lời giải"
GEMINI_API_KEYS = [
    "AIzaSyC3i5rJrRhGIQJkldAuHrGq5R-lAPzWUuM",
    "AIzaSyCKAdrWN-HRQvHggdItNIuV9MZBfmaprzE",
    "AIzaSyBcJdcJ_7HQkhhAUXG95UJ8tZAyxN6-D_Y",
    "AIzaSyCt4oSDQPX8-YK-UrIDY3wT_Do_K52sOYA",
    "AIzaSyA913U7CFK-gdjWCvm5tVIy3qGgJNoRN3c",
    "AIzaSyASlUYT5KMxrtMLVLtUpL7mn4MWOtWf29c",
    "AIzaSyCsjhdfB8isd2quVbkmgNZkTgd6ZhMZB9U",
    "AIzaSyDVBGEozWXNDptAeaZN2AMlNtp0lxMPYzU",
    "AIzaSyC8VTkreQM3cwFiV8z70ju6V0f0u-3UgNQ",
    "AIzaSyAUh7P-Zx7TegzSQ31CkpTEWDZzf9_7kcY",
    "AIzaSyBMc0NYGvRkr3t_SGXWw1IWD1gE5rmsQX4",
    "AIzaSyCHEhmMG3Olcb-nw0K6hIn8MF9eFagspQQ",
    "AIzaSyDX_boeR-9xR1Doqq2IC4I5nFBJ6Frr5e4",
    "AIzaSyAPBf9yuSz1w4-T0AW--1h-7U5lUaGzeb8",
    "AIzaSyCHiGsj_hM0SsCrUX5rcWWaes3-KTvNvOw",
    "AIzaSyDGiXPips__Xn_xoZ9pthfGexuWDkI42f4",
    "AIzaSyCKN-RcSGCrzEPT_MvAYFSFeT3YYbOHMcI",
    "AIzaSyDsI0ouJq94mOTosiCgUAtvbQEiB-QiPD8",
    "AIzaSyANln8eny_DE5X_cGMsUyLAefUj0w1Nl08",
    "AIzaSyAjoobHVRyRsFgwJEmW7NXzhANg78mMc9M",
    "AIzaSyArOo27u0wO8CInTht6ed_NSAMM6y19hzo",
    "AIzaSyB1zHNC2oZ9TG0MQJBCxu14xS_F8QqJkrs",
    "AIzaSyC6sEHr1Z3MC1damV6kvO8AD7zk1EW0KYo",
    "AIzaSyA8R1ksZU9OB6TVGvGdcCBmzaXBsRfO5OY",
    "AIzaSyAKYxBKQPPBLWYp-ktsDXPtamslnRUoMHc"
]
# Từ khóa xác định đáp án TN
CHOICE_LINE_REGEX_PATTERNS = [
    r"^\s*Chọn\s+phương\s+án\s+([ABCD])\.(.*)",         # Chọn phương án A.
    r"^\s*Chọn\s+phương\s+án\s+([ABCD])\s*(.*)",       # Chọn phương án A
    r"^\s*Chọn\s+đáp\s+án\s+([ABCD])\.(.*)",           # Chọn đáp án A.
    r"^\s*Chọn\s+đáp\s+án\s+([ABCD])\s*(.*)",         # Chọn đáp án A
    r"^\s*Chọn\s+([ABCD])\.?\s*(.*)",                  # Chọn A / Chọn A.
    r"^\s*=>\s*Chọn\s+([ABCD])\.?\s*(.*)",             # => Chọn A / => Chọn A.
    r"^\s*→\s*Chọn\s*([ABCD])\.?\s*(.*)",
    r"^\s*→\s*Đáp\s+án\s+đúng(?:\s+là)?\s*:?\s*([a-dA-D])\.?\s*(.*)",
    r"^\s*(?:[a-zA-Z]\)\s+)?Chọn\s+([ABCD])\.?\s*(.*)",
    r"^\s*Phương\s+án\s+đúng\s+là\s+([ABCD])[:\.]?(.*)",# Phương án đúng là A / A. / A:
    r"^\s*Lựa\s+chọn\s+([ABCD])\s+là\s+đáp\s+án\s+đúng\.?(.*)", # Lựa chọn A là đáp án đúng / đúng.
    r"^\s*Đáp\s+án\s*:\s*([ABCD])\.?(.*)",
    r"^\s*Đáp\s+án\s+đúng\s+là\s*:\s*([ABCD])\.?\s*(.*)",
    r"^\s*Đáp\s+án\s+đúng\s+là\s+([ABCD])\.(.*)",
    r"^\s*Đáp\s+án\s+([ABCD])\.?\s*(.*)",
]

# Mapping từ chữ cái lựa chọn sang số (giữ nguyên)
CHOICE_LETTER_TO_NUMBER = {
    'A': '1',
    'B': '2',
    'C': '3',
    'D': '4',
}

# Dấu ngăn cách mới (giữ nguyên)
CHOICE_SEPARATOR = "####"





# REGXEX_FROM_OBJEBCTS
# REGXEX_FROM_OBJEBCTS
REGXEX_FROM_OBJEBCTS = [
    {
        "name": "Toán",
        "pattern":
            {
                "QUESTION_PATTERNS": [
                    r"Đề bài",
                    r"Luyện tập 1 "
                    r"Câu (?:\d+|[a-z])",
                    r"(?:HĐ|TH|LT|CH|VD|KP|LG)\d+",
                    r"(?:HĐ|TH|LT|CH|VD|KP|LG) \d+",
                    r"LG [a-z](?:,[a-z])*",
                    r"Thực hành(?:\s+\d+|)",
                    r"Hoạt động khám phá",
                    r"HOẠT ĐỘNG(?:\s+\d+|)",
                    r"Hoạt động(?:\s+\d+|)",
                    r"Tranh luận(?:\s+\d+|)",
                    r"Luyện tập(?:\s+\d+|)",
                    r"Vận dụng(?:\s+\d+|)",
                    r"Câu hỏi(?:\s+\d+|)",
                    r"Thử thách nhỏ",
                    r"TTN",
                    r"HĐ Khởi động(?:\s+\d+|)",
                    r"HĐ Khám phá(?:\s+\d+|)",
                    r"Trả lời\s+.*?"
                ],
                "METHOD_PATTERNS": [
                    r"Phương pháp giải - Xem chi tiết",
                    r"Phương pháp giải",
                    r"Phương pháp",
                    r"Phương pháp giải - Xem chi tiết:",
                    r"Phương pháp giải:",
                    r"Phương pháp:"
                ],
                "SOLUTION_PATTERNS": [
                    r"Lời giải chi tiết",
                    r"Lời giải",
                    r"Trả lời",
                    r"Lời giải chi tiết:",
                    r"Lời giải:",
                    r"Trả lời:"
                ]
            }
    },
    {
        "name": "Văn",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Đề bài",
                r"Đề bài:",
                r"Đề bài: ",
                r"Đề bài:", # Lặp lại, có thể bỏ
                r"Câu \d+",
                r"Câu \d+[:\.]",
                r"Câu \d+\.",
                r"Câu \d+ [a-zA-Z]",
                
                r"[A-Z]+\. Bài tập .+? Câu \d+",
                r"[A-Z]+\. Câu hỏi .+? \d+",
                r"[A-Z]+[:\.] Câu hỏi .+? \d+",
                r"Phần [a-zA-Z]+ Câu \d+",
                r"Chuẩn bị đọc",
                r"Chuẩn bị đọc \d+",
                r"Trước khi đọc",
                r"Trước khi đọc \d+",
                r"Trước khi đọc .+?",
                r"Trong khi đọc",
                r"Trong khi đọc \d+",
                r"Trong khi đọc .+? \d+",
                r"Trong khi đọc .+?",
                r"Đọc văn bản",
                r"Đọc văn bản \d+",
                r"Sau khi đọc",
                r"Sau khi đọc \d+",
                r"Sau khi đọc .+? \d+",
                r"Sau khi đọc .+?",
                r"Viết kết nối với đọc",
                r"Trải nghiệm cùng VB \d+",
                r"Suy ngẫm và phản hồi \d+",
                r"Hướng dẫn viết bài",
                r"Hướng dẫn quy trình viết",
                r"Hướng dẫn phân tích VB \d+",
                r"Từ đọc đến viết",
                r"Nói",
                r"Bài tập sáng tạo",
                r"Kết nối đọc - viết",
                r"Nội dung \d+",
                r"Biện pháp chêm xen \d+",
                r"Biện pháp liệt kê \d+",
                r"Đề \d+:",
                r"Đề \d+: ",
                r"Đọc ngữ liệu tham khảo .+?",
                r"Ngữ liệu tham khảo .+?",
                r"Đọc Câu \d+",
                r"Đọc \d+",
                r"Nói và nghe",
                r"Bài viết tham khảo \d+",
                r"Chuẩn bị viết",
                r"Chuẩn bị viết \d+",
                r"\d+\. Đọc \d+"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải - Xem chi tiết:",
                r"Phương pháp giải:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết",
                r"Lời giải chi tiết:",
                r"Lời giải:"
            ]
        }
    },
    {
        "name": "Tin học",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Đề bài",
                r"Câu \d+",
                r"CH tr \d+",
                r"CH tr \d+ .+?",
                r"Hoạt động \d+",
                r"Khởi động",
                r"Mở đầu",
                r"Khám phá",
                r"Luyện tập",
                r"Vận dụng",
                r"Khám phá \d+",
                r"Luyện tập \d+",
                r"Vận dụng \d+",
                r"Khám phá \d+[a-zA-Z]* .+?",
                r"Luyện tập \d+ .+?",
                r"Vận dụng \d+ .+?",
                r"\? mục .+?",
                r"\d+\.\d+",
                r"\d+\.\d+\.",
                r"\d+[a-zA-Z]\.\d+",
                r"\d+\."
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết",
                r"Lời giải chi tiết:",
                r"Lời giải:"
            ]
        }
    },
    {
        "name": "Lý",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Trắc nghiệm \d+\.\d+",
                r"Tự luận \d+\.\d+",
                r"Câu \d+\.",
                r"\d+\.\d+",
                r"[IVXLCDM]+\.\d+",
                r"\*Đề bài:",
                r"\*\d+\.\d+",
                r"Câu hỏi tr \d+ .+?",
                r"Câu hỏi tr \d+",
                r"Bài tập Bài \d+",
                r"Bài tập .+? Bài \d+"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải:",
                r"Phương pháp :",
                r"\*Phương pháp giải"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết :",
                r"\*Lời giải chi tiết"
            ]
        }
    },
    {
        "name": "Sinh",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"CH tr \d+ .+?",
                r"CH tr \d+",
                r"Câu \d+",
                r"Câu \d+\.",
                r"CH\d+\.",
                r"CH\d+:",
                r"CH \d+:",
                r"CH \d+: ",
                r"CH\d+: ",
                r"MĐ: ",
                r"MĐ:",
                r"Bài tập \d+",
                r"Câu hỏi tr \d+",
                r"\d+\.\d+"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải:",
                r"Phương pháp giải",
                r"Phương pháp:",
                r"Hướng dẫn giải:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết",
                r"Giải chi tiết:",
                r"Giải chi tiết"
            ]
        }
    },
    {
        "name": "Lịch sử Địa lý",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Đề bài",
                r"\d+\.\d+",
                r"\? mục .+?",
                r"\?mục .+?",
                r"\? mục \d+ \d+",
                r"Mở đầu",
                r"Vận dụng",
                r"Vận Dụng",
                r"Vận dụng \d+",
                r"Vận dụng.+?",
                r"Luyện tập",
                r"Luyện tập \d+",
                r"Luyện tập .+?",
                r"\d+ Bài tập \d+",
                r"\d+",
                r"\d+\.",
                r"\d+\. ",
                r"\d+\.\d+\.",
                r"[A-Z]+ Bài tập \d+",
                r"Câu \d+ \d+",
                r"Câu \d+",
                r"1 Luyện tập",
                r"1 Vận dụng",
                r"\d+ [a-zA-Z]\)",
                r"Bài tập \d+",
                r"Câu \d+ [a-zA-Z]"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:",
                r"Phương pháp giải"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết",
                r"Lời giải chi tiết:",
                r"Giải chi tiết:",
                r"Lời giải:"
            ]
        }
    },
    {
        "name": "Lịch sử",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Câu \d+\. .+?\*",
                r"Câu \d+\. .+?",
                r"Câu \d+",
                r"Câu \d+ .+?",
                r"Mở đầu",
                r"\? mục \d+ .+?",
                r"\? mục \d+\.[a-zA-Z] .+?",
                r"\? mục .+?",
                r"\? Mục .+?",
                r"Vận dụng",
                r"Vận Dụng",
                r"Vận dụng \d+",
                r"Vận dụng .+?",
                r"Luyện tập",
                r"Luyện tập \d+",
                r"Luyện tập .+?",
                r"Bài tập \d+",
                r"Bài tập \d+ \d+"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải:",
                r"Phương pháp giải"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải:",
                r"Lời giải chi tiết:"
            ]
        }
    },
    {
        "name": "KHTN",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Đề bài",
                r"Đề bài:",
                r"Câu \d+",
                r"Câu hỏi \d+",
                r"CH\d*(?:\.|:)",
                r"\d+\.\d+",
                r"CH tr \d+ (?:CH|MĐ|LT|BT|VD|TL)\d*",
                r"CH tr \d+ (?:CH|MĐ|LT|BT|VD|TL)?(?: \d+)?",
                r"CH tr \d+(?: .+?)?",
                r"CH trang \d+ (?:CH|MĐ|LT|BT|VD|TL)\d*",
                r"CH trang \d+ (?:CH|MĐ|LT|BT|VD|TL)?(?: \d+)?",
                r"CH trang \d+(?: .+?)?",
                r"Bài \d+",
                r"CH|HĐ|MĐ(?:\.|:)",
                r"CH|HĐ|MĐ \d+(?:\.|:)",
                r"CH|HĐ|MĐ\d*(?:\.|:)",
                r"Câu hỏi tr \d+ .+?",
                r"Khởi động",
                r"Mở đầu",
                r"Khám phá",
                r"Khám phá \d+",
                r"Khám phá \d+ .+?",
                r"Luyện tập",
                r"Luyện tập \d+",
                r"Luyện tập \d+ .+?",
                r"Vận dụng",
                r"Vận dụng \d+",
                r"Vận dụng \d+ .+?",
                r"Hoạt động \d+",
                r"\d+[a-zA-Z]\.\d+",
                r"\d+\. .+?"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:",
                r"Phương pháp giải"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết",
                r"Lời giải:"
            ]
        }
    },
    {
        "name": "Hóa",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"CH tr \d+ .+?",
                r"CH tr \d+",
                r"Bài tập \d+",
                r"Bài tập Bài \d+",
                r"Câu \d+",
                r"\d+\.\d+",
                r"Nhận biết \d+\.\d+",
                r"Thông hiểu \d+\.\d+",
                r"Vận dụng \d+\.\d+",
                r"BT \d+",
                r"OT \d+"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải:",
                r"Phương pháp giải"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết"
            ]
        }
    },
    {
        "name": "Địa",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Câu \d+\.",
                r"Câu \d+",
                r"Câu \d+ \d+",
                r"Câu \d+ .+?",
                r".+? Câu \d+",
                r"\? mục \d+ .+?",
                r"\? mục \d+\.[a-zA-Z] .+?",
                r"\? mục .+?",
                r"\? Mục .+?",
                r"\? mục [IVXLCDM]+ \d+",
                r"\? mục [IVXLCDM]+",
                r"Vận dụng",
                r"Vận Dụng",
                r"Vận dụng \d+",
                r"Vận dụng .+?",
                r"Luyện tập",
                r"Luyện tập \d+",
                r"Luyện tập .+?",
                r"Giải bài .+? Địa lí \d+"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải:",
                r"Phương pháp giải"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải:"
            ]
        }
    },
    {
        "name": "Anh",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"(?:Bài|Bài) \d+",
                r"(?:Bài|Bài) \d+[a-zA-Z]",
                r"\d+\.\d+ .+? (?:Bài|Bài) \d+",
                r"[IVXLCDM]+\.\d+ .+? (?:Bài|Bài) \d+",
                r"Pronunciation \d+",
                r"Pronunciation",
                r"Vocabulary",
                r"Vocabulary \d+",
                r"Grammar",
                r"Grammar \d+",
                r"Speaking \d+",
                r"Reading",
                r"Reading \d+",
                r"Writing",
                r"Writing .+?",
                r"Đề bài",
                r"[IVXLCDM]+\. (?:Pronunciation|Vocabulary|Grammar|Speaking|Reading|Writing)",
                r"[IVXLCDM]+\. (?:Pronunciation|Vocabulary|Grammar|Speaking|Reading|Writing) \d+",
                r"[IVXLCDM]+\. (?:Pronunciation|Vocabulary|Grammar|Speaking|Reading|Writing) Câu \d+: .+?",
                r"Câu \d+: .+?",
                r"Câu \d+"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:"
            ]
        }
    },
    {
        "name": "Hướng nghiệp, HĐTN",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"\d+",
                r"Hoạt động \d+",
                r"HĐ \d+",
                r"Câu \d+:",
                r"Câu \d+ :",
                r"CH \d+",
                r"Câu \d+",
                r"Bài tập \d+",
                r"Đề bài",
                r"HĐ \d+ CH \d+"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:",
                r"\*Phương pháp giải:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết",
                r"\*Lời giải chi tiết:"
            ]
        }
    },
    {
        "name": "Giáo dục Thể chất",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Đề bài",
                r"Câu \d+"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết"
            ]
        }
    },
    {
        "name": "Giáo dục Quốc phòng",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Khởi động \d+",
                r"Khởi động \d+\.\d+",
                r"Đề bài",
                r"Kiểm tra \d+",
                r"Kiểm tra \d+\.\d+",
                r"Bài tập \d+:",
                r"Bài tập \d+\.",
                r"Bài tập \d+: .+?",
                r"\d+\.",
                r"\d+\. .+?",
                r"\d+\. .+?" # Lặp lại, có thể bỏ
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết",
                r"Lời giải:",
                r"Lời giải:" # Lặp lại, có thể bỏ
            ]
        }
    },
    {
        "name": "Giáo dục Công dân",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Đề bài",
                r"Câu \d+",
                r"Tình huống \d+",
                r"Mở đầu",
                r"Khám phá",
                r"Luyện tập",
                r"Vận dụng",
                r"Khám phá \d+",
                r"Luyện tập \d+",
                r"Vận dụng \d+",
                r"Khám phá \d+.+?",
                r"Luyện tập \d+.+?",
                r"Vận dụng \d+.+?",
                r"Bài tập \d+",
                r"Bài tập \d+ Câu .+?"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:",
                r"Phương pháp:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết",
                r"Lời giải chi tiết:" # Lặp lại, có thể bỏ
            ]
        }
    },
    {
        "name": "Kinh tế Pháp luật",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Câu \d+[a-zA-Z]",
                r"Câu \d+",
                r"Mở đầu",
                r"Khám phá",
                r"Luyện tập",
                r"Vận dụng",
                r"Khám phá \d+",
                r"Luyện tập \d+",
                r"Vận dụng \d+",
                r"Khám phá \d+.+?",
                r"Luyện tập \d+.+?",
                r"Vận dụng \d+.+?",
                r"\? mục .+?",
                r"[a-zA-Z]",
                r"Câu \d+\.",
                r"Bài tập \d+\."
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết",
                r"Lời giải:"
            ]
        }
    },
    {
        "name": "Công nghệ",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Đề bài",
                r"Mở đầu",
                r"Khám phá",
                r"Luyện tập",
                r"Vận dụng",
                r"Câu hỏi",
                r"Câu hỏi ôn tập",
                r"Câu \d+",
                r"Kết nối năng lực",
                r"Câu hỏi tr\d+ .+?",
                r"Câu hỏi tr\d+",
                r"MĐ",
                r"CH trang \d+",
                r"CH trang \d+ .+?"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:",
                r"Phương pháp giải: "
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết",
                r"Lời giải chi tiết: "
            ]
        }
    },
    {
        "name": "Âm nhạc",
        "pattern": {
            "QUESTION_PATTERNS": [
                r"Đề bài",
                r"Câu \d+",
                r"\d+\.",
                r"Hát",
                r"Nghe nhạc",
                r"Hát theo .+?",
                r"Câu hỏi \d+",
                r"Câu hỏi"
            ],
            "METHOD_PATTERNS": [
                r"Phương pháp giải - Xem chi tiết",
                r"Phương pháp giải:"
            ],
            "SOLUTION_PATTERNS": [
                r"Lời giải chi tiết:",
                r"Lời giải chi tiết"
            ]
        }
    }
]
