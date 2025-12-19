import os
import glob
import shutil # Import shutil để copy file
from concurrent.futures import ProcessPoolExecutor, as_completed # Thay ThreadPoolExecutor bằng ProcessPoolExecutor
import multiprocessing # Import multiprocessing để lấy process ID
from modules.chuyendang.md2docx import process_batch_multi_docx_to_single_docx
import multiprocessing
from multiprocessing import Process, Queue
from queue import Empty
import sys


# Giả định chuyendangTL.py chứa hàm process_word_file
# Đảm bảo rằng process_word_file và mọi thứ nó sử dụng đều có thể được pickle
# và không có trạng thái toàn cục gây xung đột giữa các tiến trình.
from modules.chuyendang.chuyendangTL import process_word_file
def delete_files_except_docx_parts_docx(folder_path):
    """
    Xóa tất cả các tệp trong một thư mục, ngoại trừ tệp .docx 
    có tên chứa chuỗi '_parts_docx_files'.

    Args:
        folder_path (str): Đường dẫn đến thư mục cần xử lý.

    Returns:
        str: Đường dẫn đầy đủ của tệp .docx được giữ lại. 
             Trả về None nếu không tìm thấy tệp nào phù hợp hoặc thư mục không tồn tại.
    """
    if not os.path.isdir(folder_path):
        print(f"Lỗi: Thư mục '{folder_path}' không tồn tại.")
        return None

    retained_file_path = None
    
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Kiểm tra xem đây có phải là file không
            if os.path.isfile(file_path):
                # Kiểm tra nếu tên file chứa chuỗi '_parts_docx_files' và có đuôi .docx
                if "_parts_docx_files" in filename and filename.endswith('.docx'):
                    retained_file_path = file_path
                    print(f"Đã giữ lại tệp: {filename}")
                    continue  # Bỏ qua tệp này, không xóa
                
                # Nếu không phải tệp cần giữ, thì xóa
                print(f"Đang xóa: {filename}")
                os.remove(file_path)
        
        print(f"Đã hoàn tất việc dọn dẹp thư mục '{folder_path}'.")
        return retained_file_path
    
    except Exception as e:
        print(f"Lỗi khi xóa tệp: {e}")
        return None
    
def process_single_file(input_file, subject, level, json_structure_folder, log_queue, results_queue):
    """
    Xử lý một file DOCX đơn lẻ trong một tiến trình con.
    Log sẽ được gửi vào log_queue và kết quả sẽ được gửi vào results_queue.
    """
    
    # Lưu stdout gốc của tiến trình con
    original_stdout = sys.stdout
    # Chuyển hướng stdout để mọi lệnh print() đều đi vào log_queue
    sys.stdout = QueueWriter(log_queue)

    try:
        pid = multiprocessing.current_process().pid
        # Lấy tên file không có extension
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Tạo temp directory riêng cho mỗi file
        temp_dir = f"temp_{file_name}_pid_{pid}"
        
        # Tìm file cấu trúc JSON
        json_pattern = os.path.join(json_structure_folder, "*.json")
        json_files = glob.glob(json_pattern)
        json_struct_file = None
        for json_file in json_files:
            if file_name in os.path.basename(json_file):
                json_struct_file = json_file
                break
        
        print(f"[PID:{pid}] Bắt đầu xử lý: {file_name} với file cấu trúc JSON: {json_struct_file}")
        
        # Gọi hàm process_word_file có sẵn
        output_file = process_word_file(input_file, subject, level, json_struct_file, temp_dir=temp_dir)
        
        if output_file and os.path.exists(output_file):
            print(f"[PID:{pid}] Hoàn thành: {os.path.basename(output_file)}")
            
            # Xóa thư mục temp sau khi xử lý xong
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"[PID:{pid}] Đã xóa thư mục tạm: {temp_dir}")
            
            # Gửi kết quả thành công vào hàng đợi
            results_queue.put({"status": "success", "input": input_file, "output": output_file})
            return
        else:
            print(f"[PID:{pid}] Lỗi xử lý hoặc không tìm thấy file output: {file_name}")
            results_queue.put({"status": "failed", "input": input_file})
            return
            
    except Exception as e:
        print(f"[PID:{pid}] Lỗi xử lý {input_file}: {str(e)}")
        results_queue.put({"status": "failed", "input": input_file})
    finally:
        # Quan trọng: Khôi phục lại stdout gốc trước khi kết thúc
        sys.stdout = original_stdout
        # Gửi tín hiệu kết thúc log để tiến trình cha biết
        log_queue.put(f"[PID:{pid}]_FINISHED_LOGGING")
class QueueWriter:
    def __init__(self, queue):
        self.queue = queue
    
    def write(self, message):
        # Đảm bảo message không rỗng và không chỉ là dòng mới
        if message.strip():
            self.queue.put(message)
    
    def flush(self):
        # flush là bắt buộc nhưng không cần làm gì ở đây
        pass
def process_docx_folder(input_folder, subject, level, max_workers=3, json_structure_folder="json_structure"):
    """
    Xử lý tất cả file DOCX trong thư mục đầu vào sử dụng đa tiến trình.
    """
    docx_files = []
    for file in os.listdir(input_folder):
        if file.endswith(".docx"):
            docx_files.append(os.path.join(input_folder, file))

    json_files = []
    for file in os.listdir(json_structure_folder):
        if file.endswith(".json"):
            json_files.append(os.path.join(json_structure_folder, file))
    
    if not docx_files or not json_files:
        print(f"Không tìm thấy file DOCX trong {input_folder} hoặc JSON trong {json_structure_folder}")
        return
    
    print(f"Tìm thấy {len(docx_files)} file DOCX.")
    print(f"\nBắt đầu xử lý với {max_workers} processes...")
    
    # Tạo hàng đợi để thu thập log và kết quả từ các tiến trình con
    log_queue = multiprocessing.Queue()
    results_queue = multiprocessing.Queue()
    
    processes = []
    
    # Khởi tạo các tiến trình con
    for file in docx_files:
        p = Process(
            target=process_single_file,
            args=(file, subject, level, json_structure_folder, log_queue, results_queue)
        )
        processes.append(p)
        p.start()
        
    successful_files = []
    failed_files = []
    finished_processes_count = 0
    total_processes = len(processes)

    # Vòng lặp lắng nghe log và kết quả
    while finished_processes_count < total_processes:
        try:
            # Lấy log từ log_queue
            log_entry = log_queue.get(timeout=0.1)
            # Kiểm tra tín hiệu kết thúc
            if log_entry.endswith("_FINISHED_LOGGING"):
                finished_processes_count += 1
            else:
                # In log ra terminal
                print(log_entry, end='')
        except Empty:
            pass # Không có log, tiếp tục vòng lặp

        try:
            # Lấy kết quả từ results_queue
            result = results_queue.get(timeout=0.1)
            if result["status"] == "success":
                successful_files.append((result["input"], result["output"]))
            else:
                failed_files.append(result["input"])
        except Empty:
            pass # Không có kết quả, tiếp tục vòng lặp
    
    # Chờ tất cả các tiến trình kết thúc hoàn toàn
    for p in processes:
        p.join()
    
    # --- In kết quả cuối cùng ---
    print(f"\n{'='*50}")
    print("KẾT QUẢ XỬ LÝ:")
    print(f"{'='*50}")
    print(f"Thành công: {len(successful_files)}/{total_processes} files")
    
    if successful_files:
        print("\nFiles thành công:")
        for input_file, output_file in successful_files:
            print(f"   ✓ {os.path.basename(input_file)} -> {os.path.basename(output_file)}")
    
    if failed_files:
        print("\nFiles thất bại:")
        for failed_file in failed_files:
            print(f"   ✗ {os.path.basename(failed_file)}")

def process_batch_files(input_folder, subject, grade,json_structure_folder ):
    """
    Hàm xử lý các file docx, chuyển đổi và dọn dẹp.
    
    Args:
        input_folder (str): Đường dẫn đến thư mục chứa các file đầu vào.
    """
   

    # Nhập thông tin
    print("=== XỬ LÝ BATCH FILE DOCX ===")
    print(f"Thư mục đầu vào: {input_folder}")
    print(f"Thư mục đầu ra: {input_folder}")
    print()

    subject =subject
    level =grade

    # Tùy chọn số processes
    num_cores = multiprocessing.cpu_count()
    # Sử dụng tối đa số lõi, nhưng không vượt quá một ngưỡng an toàn, ví dụ 8
    # và luôn để lại ít nhất 1 lõi cho hệ thống
    max_workers = max(1, min(num_cores - 2, 8))

    print(f"\nSử dụng {max_workers} processes để xử lý...")

    try:
        # Gọi hàm xử lý folder
        # Các hàm này cần được định nghĩa ở đâu đó trong code của bạn
        process_docx_folder(
            input_folder=input_folder,
            subject=subject,
            level=level,
            max_workers=max_workers,
            json_structure_folder=json_structure_folder
        )
        print("Bắt gom các file md thành docx ")
        process_batch_multi_docx_to_single_docx(input_folder=input_folder)
        print("Bắt đầu dọn dẹp các file không cần thiết")
        out_put_docx= delete_files_except_docx_parts_docx(input_folder)
        return out_put_docx
    except Exception as e:
        print(f"Lỗi trong quá trình xử lý: {str(e)}")
