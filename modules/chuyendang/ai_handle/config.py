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
                                "question_block_start": {"type": "STRING"},
                                "type_ques": {
                                    "type": "STRING",
                                    "description": "Type of question block, TRUE FALSE :ĐS , MULTIPLE CHOICE:DD, 1 ANSWER ANSWER:TN, SHORT ANSWER:TLN",
                                    "enum": ["ĐS", "DD", "TN", "TLN"]
                                }
                            },
                            # BỔ SUNG Ở ĐÂY: Yêu cầu bắt buộc 2 trường này phải xuất hiện
                            "required": ["question_block_start", "type_ques"]
                        }
                    }
                },
                # (Tùy chọn) Bạn cũng nên yêu cầu có danh sách câu hỏi
                "required": ["questions"]
            }
        }
    },
    # (Tùy chọn) Yêu cầu bắt buộc phải có mảng extracted_sections
    "required": ["extracted_sections"]
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

