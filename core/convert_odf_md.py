import requests 
import base64 
import os 
import json 
import time
from config.credentials import Config
# Load credentials từ environment


def get_mathpix_credentials():
    return Config.MATHPIX_APP_KEY, Config.MATHPIX_APP_ID

def send_pdf_to_mathpix(file_path):
    """Gửi PDF đến Mathpix API để convert"""
    try:
        app_key, app_id = get_mathpix_credentials()
        
        with open(file_path, "rb") as f:
            print("📤 Đang gửi request đến Mathpix...")

            files = {
                "file": (os.path.basename(file_path), f, "application/pdf")
            }

            response = requests.post(
                "https://api.mathpix.com/v3/pdf",
                headers={
                    "app_id": app_id,
                    "app_key": app_key
                },
                files=files,
                # Specify conversion formats
                data={
                    "conversion_formats[md]": "true",  # Enable Markdown
                }
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ Gửi thành công!")
                print(f"📋 PDF ID: {result.get('pdf_id', 'N/A')}")
                return result
            else:
                print(f"❌ Lỗi API: {response.status_code} - {response.text}")
                return None

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def check_conversion_status(pdf_id):
    """Kiểm tra trạng thái conversion"""
    app_key, app_id = get_mathpix_credentials()
    
    headers = {
        'app_key': app_key,
        'app_id': app_id
    }
    
    try:
        url = f"https://api.mathpix.com/v3/pdf/{pdf_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'unknown')
            print(f"📋 Conversion status: {status}")
            return result
        else:
            print(f"❌ Lỗi check status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Lỗi check status: {e}")
        return None

def download_markdown(pdf_id, output_path):
    """Download file Markdown đã convert"""
    app_key, app_id = get_mathpix_credentials()
    
    headers = {
        'app_key': app_key, 
        'app_id': app_id
    }
    
    print(f"📥 Đang download Markdown cho PDF ID: {pdf_id}")
    
    try:
        # Mathpix API endpoint cho markdown
        url = f"https://api.mathpix.com/v3/pdf/{pdf_id}.md"
        response = requests.get(url, headers=headers, timeout=120)
        
        if response.status_code == 200:
            # Tạo thư mục nếu chưa có
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
            # Lưu content dạng text (UTF-8)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
                print(f"✅ Downloaded Markdown: {output_path}")
            return output_path
        else:
            print(f"❌ Lỗi download: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi download: {str(e)}")
        return None

def wait_for_conversion(pdf_id, max_wait_time=300):
    """Chờ conversion hoàn thành với timeout"""
    print(f"⏳ Chờ conversion hoàn thành (max {max_wait_time}s)...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status_result = check_conversion_status(pdf_id)
        
        if not status_result:
            print("❌ Không thể check status")
            return False
        
        status = status_result.get('status', 'unknown')
        
        if status == 'completed':
            print("✅ Conversion hoàn thành!")
            return True
        elif status == 'error':
            error_msg = status_result.get('error', 'Unknown error')
            print(f"❌ Conversion lỗi: {error_msg}")
            return False
        elif status == 'processing':
            print("🔄 Đang xử lý...")
        
        # Đợi 10 giây trước khi check lại
        time.sleep(10)
    
    print("⏰ Timeout! Conversion mất quá nhiều thời gian")
    return False

def convert_pdf_to_markdown(pdf_path, output_path=None):
    """
    Convert PDF to Markdown
    
    Args:
        pdf_path (str): Đường dẫn file PDF đầu vào
        output_path (str): Đường dẫn file Markdown đầu ra (optional)
    
    Returns:
        str: Đường dẫn file Markdown nếu thành công, None nếu thất bại
    """
    print("🎯 Bắt đầu convert PDF to Markdown")
    
    # Kiểm tra file PDF tồn tại
    if not os.path.exists(pdf_path):
        print(f"❌ File không tồn tại: {pdf_path}")
        return None
    
    # Hiển thị thông tin file
    file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
    print(f"📄 File: {os.path.basename(pdf_path)} ({file_size:.1f} MB)")
    
    # 1. Gửi PDF lên Mathpix
    result = send_pdf_to_mathpix(pdf_path)
    if not result:
        print("❌ Không thể gửi PDF lên Mathpix")
        return None
    
    pdf_id = result.get('pdf_id')
    if not pdf_id:
        print("❌ Không nhận được pdf_id")
        return None
    
    print(f"📋 PDF ID: {pdf_id}")
    
    # 2. Chờ conversion hoàn thành
    if not wait_for_conversion(pdf_id):
        print("❌ Conversion thất bại hoặc timeout")
        return None
    
    # 3. Tạo output path nếu chưa có
    if not output_path:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{pdf_name}_converted.md")
    
    # 4. Download file Markdown
    downloaded_file = download_markdown(pdf_id, output_path)
    
    if downloaded_file:
        # Kiểm tra file đã tạo
        if os.path.exists(downloaded_file):
            file_size = os.path.getsize(downloaded_file)
            print(f"🎉 Hoàn thành! File Markdown: {downloaded_file} ({file_size} bytes)")
            return downloaded_file
        else:
            print("❌ File Markdown không được tạo")
            return None
    else:
        print("❌ Không thể download file Markdown")
        return None

def convert_multiple_pdfs(pdf_folder, output_folder=None):
    """
    Convert nhiều PDF files trong một folder
    
    Args:
        pdf_folder (str): Thư mục chứa PDF files
        output_folder (str): Thư mục output (optional)
    """
    print(f"📂 Scanning folder: {pdf_folder}")
    
    if not os.path.isdir(pdf_folder):
        print(f"❌ Folder không tồn tại: {pdf_folder}")
        return
    
    # Tìm tất cả PDF files
    pdf_files = []
    for file in os.listdir(pdf_folder):
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(pdf_folder, file))
    
    if not pdf_files:
        print("❌ Không tìm thấy PDF files nào")
        return
    
    print(f"📄 Tìm thấy {len(pdf_files)} PDF files")
    
    # Setup output folder
    if not output_folder:
        output_folder = os.path.join(pdf_folder, "converted_markdown")
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Convert từng file
    successful = 0
    failed = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*60}")
        print(f"🔄 Converting {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        print(f"{'='*60}")
        
        # Tạo output path
        pdf_name = os.path.splitext(os.path.basename(pdf_file))[0]
        output_path = os.path.join(output_folder, f"{pdf_name}.md")
        
        # Convert
        result = convert_pdf_to_markdown(pdf_file, output_path)
        
        if result:
            successful += 1
            print(f"✅ Success: {os.path.basename(result)}")
        else:
            failed += 1
            print(f"❌ Failed: {os.path.basename(pdf_file)}")
        
        # Delay giữa các file để tránh rate limit
        if i < len(pdf_files):
            print("⏳ Waiting 5 seconds before next conversion...")
            time.sleep(5)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🎉 CONVERSION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📂 Output folder: {output_folder}")

# MAIN EXECUTION
if __name__ == "__main__": 
    print("🚀 PDF to Markdown Converter")
    print("=" * 50)
    
    # Option 1: Convert single file
    single_pdf = r"D:\CutPdfByDrive\CUTPDF\auto_processed\downloaded_pdfs\KNTT\Lớp 1\KNTT_SGK_ Dao duc 1.pdf"
    
    if os.path.exists(single_pdf):
        print("🎯 Converting single PDF file...")
        result = convert_pdf_to_markdown(single_pdf)
        
        if result:
            print(f"\n✅ SUCCESS! Markdown file: {result}")
            
            # Mở file để xem
            try:
                import webbrowser
                webbrowser.open(result)
                print("📖 File đã được mở trong trình duyệt")
            except:
                print("📖 Bạn có thể mở file Markdown bằng text editor")
        else:
            print(f"\n❌ FAILED! Không thể convert file")
    else:
        print(f"❌ File không tồn tại: {single_pdf}")
    
    # Option 2: Convert multiple files (uncomment để sử dụng)
    # folder_path = r"C:\path\to\your\pdf\folder"
    # convert_multiple_pdfs(folder_path)