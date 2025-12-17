# 🔧 CutPdfByDrive - AI-Powered PDF Processing Tool

**CutPdfByDrive** là một ứng dụng desktop mạnh mẽ được xây dựng bằng PyQt5, chuyên dụng để xử lý PDF với sự hỗ trợ của AI và các dịch vụ cloud.

## 🎯 Tính năng chính

### 📚 **Cut PDF (Cắt PDF thông minh)**

- **🤖 AI Analysis**: Sử dụng Google Vertex AI (Gemini 2.5 Pro) để phân tích mục lục và cấu trúc sách
- **📄 Auto Cut**: Tự động cắt PDF thành các bài học/chương riêng biệt
- **📊 Excel Summary**: Tạo bảng tóm tắt Excel với thông tin chi tiết
- **📥 Google Drive Integration**: Tải PDF trực tiếp từ Google Drive
- **📁 Local Processing**: Xử lý batch PDF từ folder local
- **🗜️ PDF Compression**: Nén PDF với nhiều mức chất lượng

### 🔄 **Convert PDF (Chuyển đổi PDF)**

- **📝 PDF to Markdown**: Chuyển đổi PDF sang Markdown với OCR
- **📄 PDF to DOCX**: Chuyển đổi PDF sang Microsoft Word
- **📃 PDF OCR Enhancement**: Cải thiện PDF với OCR
- **🧠 Mathpix Integration**: Sử dụng Mathpix API để nhận dạng text và công thức toán học
- **📥 Google Drive Support**: Hỗ trợ tải và xử lý từ Google Drive
- **⚡ Smart Processing**: Tự động kiểm tra trạng thái conversion

## 🏗️ Cấu trúc dự án

```
d:\CutPdfByDrive\
├── ui/                          # Giao diện người dùng
│   ├── main_window.py          # Cửa sổ chính
│   ├── cut_pdf_widget.py       # Widget cắt PDF
│   ├── convert_pdf_widget.py   # Widget chuyển đổi PDF
│   └── sidebar.py              # Thanh sidebar
├── CUTPDF/                     # Core modules
│   └── config/
│       └── credentials.py      # Quản lý credentials
├── process.py                  # Xử lý PDF đơn lẻ
├── auto_processor.py           # Xử lý tự động từ Drive
├── local_processor.py          # Xử lý batch local
├── client_driver.py            # Google Drive API
├── cutPDF.py                   # Core PDF cutting logic
├── callAPI.py                  # Vertex AI integration
├── convert_odf_md.py           # PDF to Markdown standalone
├── compress_manager.py         # PDF compression
├── prompt.txt                  # AI analysis prompt
└── main.py                     # Entry point
```

## 📋 Yêu cầu hệ thống

- **Python 3.7+**
- **Windows 10/11** (khuyến nghị)
- **RAM**: Tối thiểu 4GB
- **Dung lượng**: 2GB trống
- **Internet**: Kết nối ổn định (cho AI và API calls)

## 🚀 Cài đặt

### **Bước 1: Clone repository**

```bash
git clone <repository-url>
cd CutPdfByDrive
```

### **Bước 2: Cài đặt dependencies**

```bash
pip install -r requirements.txt
```

**Hoặc cài đặt thủ công:**

```bash
pip install PyQt5 PyQt5-tools
pip install google-cloud-aiplatform
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install requests python-dotenv
pip install PyPDF2 reportlab
pip install xlsxwriter
pip install Pillow
```

### **Bước 3: Thiết lập API Credentials**

#### **3.1 Google Cloud Credentials (cho AI Analysis)**

**Cách 1: Sử dụng Service Account file**

1. Tạo file `service_account.json` trong thư mục `CUTPDF/config/`
2. Copy nội dung service account key từ Google Cloud Console

**Cách 2: Sử dụng embedded credentials (mặc định)**

- Tool đã có sẵn credentials hardcoded trong `credentials.py`
- Không cần setup gì thêm

#### **3.2 Google Drive API**

1. Tạo project trên [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Drive API
3. Tạo OAuth 2.0 credentials
4. Download file `client_secret_*.json` và đặt trong thư mục gốc

#### **3.3 Mathpix API (cho PDF Conversion)**

**Cách 1: Environment variables**

```bash
# Tạo file .env
MATHPIX_APP_KEY=your_app_key_here
MATHPIX_APP_ID=your_app_id_here
```

**Cách 2: Sử dụng credentials mặc định (đã có sẵn)**

- Tool đã có credentials hardcoded, có thể sử dụng ngay

### **Bước 4: Chạy ứng dụng**

```bash
python main.py
```

## 📖 Hướng dẫn sử dụng

### **🔄 PDF Conversion Mode**

1. **Chọn PDF Files**:

   - **Local**: Click "📄 Chọn PDF Files" hoặc "📂 Chọn Folder"
   - **Google Drive**: Nhập URL folder Drive và click "📥 Tải từ Drive"

2. **Chọn Output Format**:

   - **📝 Markdown (.md)**: Chuyển đổi sang Markdown
   - **📄 DOCX**: Chuyển đổi sang Microsoft Word
   - **📃 PDF (OCR Enhanced)**: PDF với OCR cải thiện

3. **Cấu hình Options**:

   - **Output Folder**: Chọn thư mục đầu ra (để trống = cùng thư mục gốc)
   - **Smart Waiting**: Tự động chờ conversion hoàn thành
   - **Auto Open**: Tự động mở file sau khi convert

4. **Bắt đầu Convert**: Click "🚀 Bắt đầu Convert"

### **✂️ PDF Cutting Mode**

1. **Google Drive Processing**:

   - Nhập URL folder Google Drive
   - Chọn file prompt (hoặc sử dụng mặc định)
   - Click "🚀 Bắt đầu xử lý tự động"

2. **Local Processing**:

   - Chọn folder chứa PDF files
   - Configure prompt file
   - Click "📁 Xử lý folder local"

3. **Manual Processing**:
   - Chọn file PDF đơn lẻ
   - Chọn prompt file
   - Click "⚙️ Xử lý file"

## 📁 Cấu trúc Output

### **Conversion Output**

```
output/
├── {source_folder_name}/
│   ├── document_converted.md
│   ├── document_converted.docx
│   └── document_ocr.pdf
```

### **Cut PDF Output**

```
{book_name}/
├── Book_Name - Chapter_1.pdf
├── Book_Name - Chapter_2.pdf
├── Book_Name_summary.xlsx
└── Book_Name.json
```

## ⚙️ Cấu hình nâng cao

### **AI Prompt Customization**

Edit file `prompt.txt` để tùy chỉnh cách AI phân tích PDF:

```text
Từ tài liệu được cung cấp, hãy phân tích kỹ mục lục và tạo ra một kết quả có định dạng là một mảng JSON.
Mục tiêu chính: Trích xuất các đơn vị nội dung chi tiết, độc lập và có ý nghĩa học tập...
```

### **PDF Compression Settings**

- **screen (72dpi)**: Nén tối đa, file nhỏ nhất
- **ebook (150dpi)**: Cân bằng chất lượng và dung lượng
- **printer (300dpi)**: Chất lượng cao
- **prepress (300dpi)**: Chất lượng tốt nhất

## 🔧 Troubleshooting

### **Lỗi thường gặp**

**1. ImportError: No module named 'PyQt5'**

```bash
pip install PyQt5
```

**2. Google Auth Error**

- Kiểm tra file `client_secret_*.json`
- Đảm bảo Google Drive API đã được enable

**3. Mathpix API Error**

- Kiểm tra internet connection
- Credentials mặc định có thể bị rate limit

**4. AI Processing Error**

- Kiểm tra Google Cloud credentials
- File PDF phải có mục lục rõ ràng

### **Performance Tips**

1. **Batch Processing**: Xử lý nhiều file cùng lúc thay vì từng file
2. **Smart Waiting**: Enable để tối ưu thời gian chờ
3. **Internet**: Đảm bảo kết nối ổn định cho API calls
4. **RAM**: Đóng các ứng dụng khác khi xử lý file lớn

## 🎯 Use Cases

### **Giáo dục**

- Cắt sách giáo khoa thành từng bài học
- Chuyển đổi tài liệu PDF sang Markdown để edit
- Tạo bộ sưu tập tài liệu từ Google Drive

### **Văn phòng**

- Digitize tài liệu giấy với OCR
- Chuyển đổi PDF sang Word để chỉnh sửa
- Nén PDF để tiết kiệm dung lượng

### **Nghiên cứu**

- Xử lý batch paper, thesis
- Trích xuất nội dung có cấu trúc
- Tạo summary tự động

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Hỗ trợ

- **Issues**: [GitHub Issues](repository-url/issues)
- **Documentation**: [Wiki](repository-url/wiki)
- **Email**: your-email@example.com

## 🙏 Acknowledgments

- **Mathpix API** - OCR và conversion
- **Google Vertex AI** - AI analysis
- **PyQt5** - GUI framework
- **Google Drive API** - Cloud storage integration

---

⭐ **Star this repo nếu tool hữu ích cho bạn!** ⭐
