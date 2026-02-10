# 🚀 CutPdfByDrive - Nền Tảng Giáo Dục Thông Minh

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green?style=for-the-badge&logo=qt&logoColor=white)
![VertexAI](https://img.shields.io/badge/AI-Google%20Vertex-orange?style=for-the-badge&logo=googlecloud&logoColor=white)
![Status](https://img.shields.io/badge/Trạng_thái-Hoạt_động-success?style=for-the-badge)

**CutPdfByDrive** là giải pháp phần mềm desktop "All-in-One" (Tất cả trong một) hàng đầu, được thiết kế chuyên biệt cho nhà giáo dục và người sáng tạo nội dung. Tận dụng sức mạnh của **Google Gemini 2.5 Pro**, **PyQt5** và **Google Gemini 3 Pro**, hệ thống tối ưu hóa quy trình (workflow) số hóa, xử lý và tạo tài liệu giáo dục chất lượng cao.

---

## 🌟 Tính Năng Chính

Nền tảng được chia thành bốn phân hệ (module) chuyên biệt, mỗi module đóng vai trò quan trọng trong đường ống xử lý tài liệu (document processing pipeline):

### 1. ✂️ **Cut PDF (Phân Đoạn Thông Minh)**
*Tách tài liệu chính xác được tăng cường bởi AI.*
- **🤖 Phân Tích Thông Minh**: Sử dụng Google Vertex AI để hiểu cấu trúc tài liệu và Mục lục (Table of Contents).
- **📄 Tách Tự Động**: Tự động phân đoạn các tệp PDF lớn thành các bài học hoặc chương riêng lẻ với cách đặt tên chính xác.
- **📊 Báo Cáo Cấu Trúc**: Tạo báo cáo Excel chi tiết về cách tổ chức tài liệu.
- **☁️ Tích Hợp Đám Mây**: Nhập và xử lý trực tiếp từ **Google Drive**.

### 2. 🔄 **Convert PDF (Chuyển Đổi Nâng Cao)**
*Chuyển đổi tài liệu với độ trung thực cao.*
- **📝 PDF sang Markdown**: Chuyển đổi các tệp PDF phức tạp sang Markdown, bảo toàn các công thức **MathJax**.
- **📄 PDF sang DOCX**: Xuất sang Microsoft Word với định dạng chuyên nghiệp.
- **🧠 Tích Hợp Mathpix & OCR**: Nhận dạng ký tự quang học (OCR) hàng đầu trong ngành cho ghi chú viết tay và các phương trình toán học phức tạp.
- **⚡ Xử Lý Hàng Loạt**: Xử lý hàng trăm tệp đồng thời với tốc độ cao.

### 3. & 4. 📝 **GenQues (Tạo Câu Hỏi AI)**
*Các module chuyên biệt cho Khoa học Tự nhiên (KHTN) & Khoa học Xã hội (KHXH).*
Tuân thủ **Chuẩn Giáo dục 2025**, hỗ trợ 4 dạng câu hỏi chính:
- **✅ Trắc Nghiệm (Multiple Choice)**: Tự động tạo các phương án nhiễu (distractors).
- **⚖️ Đúng/Sai**: Đánh giá mệnh đề phức hợp.
- **✍️ Trả Lời Ngắn**: Điền vào chỗ trống và tạo câu trả lời súc tích.
- **📝 Tự Luận (Essay)**: Câu hỏi tự luận chuyên sâu kèm hướng dẫn chấm điểm chi tiết.

#### **Khả Năng Nâng Cao:**
| Tính Năng | Mô Tả |
| :--- | :--- |
| **🚀 Đa Luồng (Multi-threading)** | Xử lý đồng thời nhiều tệp (số lượng luồng tùy chỉnh). |
| **📂 Gom Nhóm Thông Minh** | Tự động gom nhóm các file đã cắt thành các đơn vị bài học để tạo câu hỏi toàn diện. |
| **🎨 Xem Trước Trực Tiếp** | Xem trước trực quan các tệp DOCX được tạo ngay trong ứng dụng. |
| **🔧 Tùy Chỉnh Prompt** | Kiểm soát hoàn toàn các câu lệnh (prompts) cho AI để điều chỉnh phong cách và độ khó đầu ra. |

---

## 🏗️ Kiến Trúc Hệ Thống

Kiến trúc mô-đun (modular architecture) đảm bảo tính ổn định và khả năng mở rộng.

```
d:\CheckTool\OneInAll\cutpdf\
├── ui/                         # Tầng Giao Diện Người Dùng (PyQt5)
│   ├── main_window.py          # Cửa Sổ Ứng Dụng Chính
│   ├── cut_pdf_widget.py       # Giao Diện Cắt PDF
│   ├── convert_pdf_widget.py   # Giao Diện Chuyển Đổi PDF
│   ├── gen_ques.py             # Lớp Cơ Sở (Base Class) cho các Module GenQues
│   ├── genques_khtn_widget.py  # Module Khoa Học Tự Nhiên
│   └── genques_khxh_widget.py  # Module Khoa Học Xã Hội
├── modules/                    # Tầng Nghiệp Vụ (Business Logic Layer)
│   ├── common/                 # Tiện Ích Dùng Chung (API AI, OCR, Xử Lý Ảnh)
│   ├── khtn/                   # Triển Khai Logic KHTN
│   └── khxh/                   # Triển Khai Logic KHXH
├── output/                     # Các Tài Liệu Đầu Ra (Artifacts)
├── main.py                     # Điểm Khởi Chạy Ứng Dụng (Entry Point)
└── prompt                     # Prompt cho AI
```

---

## 📋 Yêu Cầu Hệ Thống

| Thành Phần | Khuyến Nghị |
| :--- | :--- |
| **Hệ Điều Hành** | Windows 10 / 11 |
| **Python** | Phiên bản 3.8 hoặc cao hơn |
| **RAM** | 8GB+ khuyến nghị cho xử lý hàng loạt |
| **Cloud APIs** | **Google Cloud** (Vertex AI, Drive), **Mathpix** (Tùy chọn) |

---

## 🚀 Cài Đặt & Thiết Lập

### **1. Cài Đặt Các Gói Phụ Thuộc (Dependencies)**
```bash
pip install -r requirements.txt
```

### **2. Cấu Hình Thông Tin Xác Thực (Credentials)**
Để kích hoạt các tính năng AI và Cloud, hãy cấu hình các khóa API của bạn:
1.  **Google Cloud**: Đặt tệp `service_account.json` hoặc `client_secret.json` vào thư mục gốc.
2.  **Biến Môi Trường (Environment Variables)**: Đổi tên `.env.example` thành `.env` và điền các khóa cần thiết (ví dụ: Mathpix).

### **3. Khởi Chạy Ứng Dụng**
```bash
python main.py
```

---

## 📖 Hướng Dẫn Nhanh

### **Tạo Câu Hỏi (GenQues)**
1.  **Chọn Nguồn**: Kéo & thả các tệp PDF bài học (hoặc thư mục). Hệ thống tự động gom nhóm theo bài học.
2.  **Cấu Hình**:
    -   Chọn các dạng câu hỏi mong muốn (Trắc nghiệm, Đ/S, Trả lời ngắn, Tự luận).
    -   (Tùy chọn) Tùy chỉnh prompt cho các yêu cầu cụ thể.
3.  **Xử Lý**:
    -   Thiết lập **Số Luồng Xử Lý (Worker Threads)** (Mặc định: 3).
    -   Nhấn **"Start Processing"**.
4.  **Kiểm Tra**:
    -   Truy cập các tệp đã tạo trong tab **Results** (Kết quả).
    -   Xem trước nội dung ngay lập tức hoặc mở trong Microsoft Word.

---

## 📄 Giấy Phép
**Lưu Hành Nội Bộ**. Bảo lưu mọi quyền.
Được phát triển cho quy trình sản xuất nội dung giáo dục nội bộ.

---

<p align="center">
  <i>Được xây dựng với ❤️ cho Giáo Dục</i>
</p>
