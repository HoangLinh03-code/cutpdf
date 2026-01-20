schema_trac_nghiem = {
    "type": "OBJECT",
    "properties": {
        "loai_de": {"type": "STRING", "enum": ["trac_nghiem_4_dap_an"]},
        "tong_so_cau": {"type": "INTEGER"},
        "ma_bai": {"type": "STRING"},
        "cau_hoi": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "stt": {"type": "INTEGER"},
                    # "enum": ["nhan_biet", "thong_hieu", "van_dung", "van_dung_cao"]
                    "muc_do": {"type": "STRING"},
                    "ma_dang": {"type": "STRING"},
                    "phan": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Mảng chứa phân cấp: [Tên Bài, Tên Phần/Mục, Tên Dạng]"
                    },
                    # --- CẬP NHẬT: Tách riêng Tiếng Việt và Tiếng Anh ---
                    "noi_dung": {"type": "STRING"},      # Câu hỏi Tiếng Việt
                    "noi_dung_en": {"type": "STRING"},   # Câu hỏi Tiếng Anh (translate_en)
                    "hinh_anh": {
                        "type": "OBJECT",
                        "properties": {
                            "co_hinh": {"type": "BOOLEAN"},
                            "loai": {"type": "STRING"},
                            "mo_ta": {"type": "STRING"}
                        }
                    },
                    "cac_lua_chon": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "ky_hieu": {"type": "STRING"},
                                "noi_dung": {"type": "STRING"},    # Lựa chọn Tiếng Việt
                                "noi_dung_en": {"type": "STRING"}  # Lựa chọn Tiếng Anh
                            },
                            "required": ["ky_hieu", "noi_dung"]
                        }
                    },
                    "dap_an_dung": {"type": "INTEGER"},
                    "dap_an": {"type": "STRING"},     # Đáp án rút gọn (nếu cần)
                   
                    # --- CẬP NHẬT: Tách riêng Lời giải ---
                    "giai_thich": {"type": "STRING"},    # Lời giải Tiếng Việt
                    "giai_thich_en": {"type": "STRING"},
                    "goi_y": {"type": "STRING"},
                    "goi_y_en": {"type": "STRING"}
                },
                "required": ["stt", "muc_do","ma_dang", "phan", "noi_dung", "cac_lua_chon", "dap_an_dung", "giai_thich"]
            }
        }
    },
    "required": ["loai_de", "ma_bai", "tong_so_cau", "cau_hoi"]
}

schema_dung_sai = {
    "type": "OBJECT",
    "properties": {
        "loai_de": {"type": "STRING", "enum": ["dung_sai"]},
        "tong_so_cau": {"type": "INTEGER"},
        "ma_bai": {"type": "STRING"},
        "cau_hoi": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "stt": {"type": "INTEGER"},
                    "muc_do": {"type": "STRING", "enum": ["nhan_biet", "thong_hieu", "van_dung", "van_dung_cao"]},
                    "ma_dang": {"type": "STRING"},
                    "phan": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Mảng 3 phần tử: [Tên Bài, Tên Mục, Tên Dạng]"
                    },
                    "doan_thong_tin": {"type": "STRING"},
                    "doan_thong_tin_en": {"type": "STRING"},
                    "hinh_anh": {
                        "type": "OBJECT",
                        "properties": {
                            "co_hinh": {"type": "BOOLEAN"},
                            "loai": {"type": "STRING"},
                            "mo_ta": {"type": "STRING"}
                        }
                    },
                    "cac_y": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "ky_hieu": {"type": "STRING"},
                                "noi_dung": {"type": "STRING"},
                                "noi_dung_en": {"type": "STRING"},
                                "dung": {"type": "BOOLEAN"}
                            },
                            "required": ["ky_hieu", "noi_dung", "dung"]
                        }
                    },
                    "dap_an_dung_sai": {"type": "STRING"},
                   
                    # --- CẬP NHẬT: GIẢI THÍCH DẠNG MẢNG ĐỐI TƯỢNG ---
                    "giai_thich": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "ky_hieu": {"type": "STRING", "description": "a, b, c, d"},
                                "ket_luan": {"type": "STRING", "description": "ĐÚNG hoặc SAI"},
                                "noi_dung": {"type": "STRING", "description": "Giải thích Tiếng Việt 90-100 từ"},
                                "noi_dung_en": {"type": "STRING", "description": "Explanation in English 90-100 words"}
                            },
                            "required": ["ky_hieu", "ket_luan", "noi_dung", "noi_dung_en"]
                        }
                    },
                    "giai_thich_en": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "ky_hieu": {"type": "STRING"},
                                "ket_luan": {"type": "STRING", "description": "TRUE or FALSE"},
                                "noi_dung": {"type": "STRING", "description": "Explanation in English 90-100 words"}
                            },
                            "required": ["ky_hieu", "ket_luan", "noi_dung"]
                        }
                    }
                },
                "required": ["stt","ma_dang", "phan", "doan_thong_tin", "cac_y", "dap_an_dung_sai", "giai_thich"]
            }
        }
    },
    "required": ["loai_de","ma_bai", "tong_so_cau", "cau_hoi"]
}
schema_tra_loi_ngan = {
    "type": "OBJECT",
    "properties": {
        "loai_de": {"type": "STRING", "enum": ["tra_loi_ngan"]},
        "tong_so_cau": {"type": "INTEGER"},
        "ma_bai": {"type": "STRING"},
        "cau_hoi": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "stt": {"type": "INTEGER"},
                    "muc_do": {"type": "STRING"},
                    "ma_dang": {"type": "STRING"},
                    "phan": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Mảng phân cấp 3 phần tử: [Tên Bài, Tên Mục, Tên Dạng]"
                    },
                   
                    "noi_dung": {"type": "STRING", "description": "Câu hỏi Tiếng Việt"},
                    "noi_dung_en": {"type": "STRING", "description": "Câu hỏi Tiếng Anh"},
                   
                    "dap_an": {
                        "type": "STRING",
                        "description": "CHỈ CHỨA số nguyên hoặc số thập phân (VD: 5; -2; 3,5). CẤM chữ, đơn vị và các kí tự thường và đặc biệt."
                    },
                   
                    "hinh_anh": {
                        "type": "OBJECT",
                        "properties": {
                            "co_hinh": {"type": "BOOLEAN"},
                            "loai": {"type": "STRING"},
                            "mo_ta": {"type": "STRING"}
                        }
                    },
                   
                    # --- GIẢI THÍCH SONG NGỮ ---
                    "giai_thich": {"type": "STRING", "description": "Giải thích Tiếng Việt"},
                    "giai_thich_en": {"type": "STRING", "description": "Giải thích Tiếng Anh"}
                },
                "required": ["stt", "muc_do", "ma_dang", "phan", "noi_dung", "noi_dung_en", "dap_an", "hinh_anh", "giai_thich", "giai_thich_en"]
            }
        }
    },
    "required": ["loai_de", "ma_bai", "tong_so_cau", "cau_hoi"]
}
 
schema_tu_luan = {
    "type": "OBJECT",
    "properties": {
        "loai_de": {"type": "STRING", "enum": ["tu_luan"]},
        "tong_so_cau": {"type": "INTEGER"},
        "ma_bai": {"type": "STRING"},
        "cau_hoi": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "stt": {"type": "INTEGER"},
                    "muc_do": {"type": "STRING"},
                    "ma_dang": {"type": "STRING"},
                   
                    # --- CẬP NHẬT: PHAN LÀ ARRAY ---
                    "phan": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Mảng phân cấp 3 phần tử: [Tên Bài, Tên Mục, Tên Dạng]"
                    },
                   
                    # --- NỘI DUNG SONG NGỮ ---
                    "noi_dung": {"type": "STRING", "description": "Câu hỏi tự luận Tiếng Việt"},
                    "noi_dung_en": {"type": "STRING", "description": "Câu hỏi tự luận Tiếng Anh"},
                   
                    "hinh_anh": {
                        "type": "OBJECT",
                        "properties": {
                            "co_hinh": {"type": "BOOLEAN"},
                            "loai": {"type": "STRING"},
                            "mo_ta": {"type": "STRING"}
                        }
                    },
                   
                    # --- HƯỚNG DẪN CHẤM CHI TIẾT SONG NGỮ ---
                    "giai_thich": {"type": "STRING", "description": "Hướng dẫn chấm/Lời giải chi tiết Tiếng Việt. Phải đầy đủ các bước lập luận, công thức, thay số."},
                    "giai_thich_en": {"type": "STRING", "description": "Model Answer/Marking Guide in English."}
                },
                "required": ["stt", "muc_do", "ma_dang", "phan", "noi_dung", "noi_dung_en", "hinh_anh", "giai_thich", "giai_thich_en"]
            }
        }
    },
    "required": ["loai_de", "ma_bai", "tong_so_cau", "cau_hoi"]
}
 