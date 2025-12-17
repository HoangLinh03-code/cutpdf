import os
import pickle
import re
import io
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class GoogleDriveAPI:
    def __init__(self, client_secrets_file):
        """
        Khởi tạo Google Drive API client với OAuth2
        Args:
            client_secrets_file: Đường dẫn đến file JSON OAuth2 client
        """
        self.SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        self.CLIENT_SECRETS_FILE = client_secrets_file
        self.TOKEN_FILE = 'token.pickle'
        
        # Xác thực và tạo service
        self.creds = self._authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def _authenticate(self):
        """Xác thực OAuth2"""
        creds = None
        
        # Kiểm tra token đã lưu
        if os.path.exists(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # Nếu không có credentials hợp lệ
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Đang refresh token...")
                creds.refresh(Request())
            else:
                print("Bắt đầu xác thực OAuth2...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CLIENT_SECRETS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Lưu token
            with open(self.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def extract_folder_id(self, input_text):
        """Trích xuất folder ID từ URL hoặc ID trực tiếp"""
        input_text = input_text.strip()
        
        # Kiểm tra nếu input là ID trực tiếp
        if re.match(r'^[a-zA-Z0-9_-]+$', input_text) and len(input_text) > 20:
            print(f"Đây là folder ID trực tiếp: {input_text}")
            return input_text
        
        print(f"Đang xử lý URL: {input_text}")
        clean_url = input_text.split('?')[0]
        
        # Pattern: /folders/FOLDER_ID
        folder_pattern = r'/folders/([a-zA-Z0-9_-]+)'
        match = re.search(folder_pattern, clean_url)
        if match:
            folder_id = match.group(1)
            print(f"Tìm thấy folder ID: {folder_id}")
            return folder_id
        
        raise ValueError(f"Không thể trích xuất folder ID từ: {input_text}")
    
    def get_folder_name(self, folder_id):
        """Lấy tên của folder"""
        try:
            folder = self.service.files().get(fileId=folder_id, fields='name').execute()
            return folder.get('name', 'Unknown')
        except Exception as e:
            print(f"Lỗi khi lấy tên folder: {e}")
            return 'Unknown'
    
    def list_all_folders(self, parent_folder_id, current_path=""):
        """
        Liệt kê tất cả các folder con đệ quy
        Returns: dict {folder_id: relative_path}
        """
        folders_map = {}
        
        try:
            # Lấy tất cả folder con
            query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=100
            ).execute()
            
            folders = results.get('files', [])
            
            for folder in folders:
                folder_path = os.path.join(current_path, folder['name']) if current_path else folder['name']
                folders_map[folder['id']] = folder_path
                print(f"Tìm thấy folder: {folder_path}")
                
                # Đệ quy vào folder con
                sub_folders = self.list_all_folders(folder['id'], folder_path)
                folders_map.update(sub_folders)
            
            return folders_map
            
        except Exception as e:
            print(f"Lỗi khi liệt kê folders: {e}")
            return {}
    
    def list_pdf_files_in_folder(self, folder_id):
        """Liệt kê tất cả file PDF trong một folder cụ thể"""
        try:
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, size)",
                pageSize=100
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            print(f"Lỗi khi liệt kê PDF trong folder {folder_id}: {e}")
            return []
    
    def download_file(self, file_id, file_name, download_path):
        """Tải xuống file"""
        try:
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(download_path, exist_ok=True)
            
            request = self.service.files().get_media(fileId=file_id)
            file_path = os.path.join(download_path, file_name)
            
            with io.FileIO(file_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print(f"  Download progress: {int(status.progress() * 100)}%")
            
            print(f"  ✓ Đã tải xuống: {file_path}")
            return file_path
        
        except Exception as e:
            print(f"  ✗ Lỗi khi tải file {file_name}: {e}")
            return None
    
    def download_all_pdfs_with_structure(self, root_folder_id, base_download_path):
        """
        Tải xuống tất cả PDF từ folder gốc và các folder con
        với cấu trúc thư mục được giữ nguyên
        """
        try:
            # Lấy tên folder gốc
            root_folder_name = self.get_folder_name(root_folder_id)
            print(f"Bắt đầu tải từ folder: {root_folder_name}")
            
            # Tạo thư mục gốc
            root_download_path = os.path.join(base_download_path, root_folder_name)
            
            # Lấy danh sách tất cả folders
            print("\n=== Đang quét cấu trúc thư mục ===")
            all_folders = self.list_all_folders(root_folder_id)
            all_folders[root_folder_id] = ""  # Thêm folder gốc
            
            total_files = 0
            downloaded_files = 0
            
            print(f"\n=== Bắt đầu tải PDF ===")
            
            # Duyệt qua từng folder
            for folder_id, relative_path in all_folders.items():
                folder_download_path = os.path.join(root_download_path, relative_path) if relative_path else root_download_path
                
                # Lấy danh sách PDF trong folder này
                pdf_files = self.list_pdf_files_in_folder(folder_id)
                
                if pdf_files:
                    folder_display_path = relative_path if relative_path else root_folder_name
                    print(f"\nFolder: {folder_display_path} ({len(pdf_files)} PDFs)")
                    
                    total_files += len(pdf_files)
                    
                    # Tải từng file PDF
                    for pdf_file in pdf_files:
                        print(f"  Đang tải: {pdf_file['name']}")
                        result = self.download_file(
                            pdf_file['id'], 
                            pdf_file['name'], 
                            folder_download_path
                        )
                        if result:
                            downloaded_files += 1
            
            print(f"\n=== Hoàn thành ===")
            print(f"Tổng số file PDF: {total_files}")
            print(f"Đã tải thành công: {downloaded_files}")
            print(f"Thư mục lưu: {root_download_path}")
            
        except Exception as e:
            print(f"Lỗi trong quá trình tải: {e}")

    # Giữ nguyên các method cũ cho compatibility
    def list_pdf_files(self, folder_input):
        """
        Liệt kê files PDF trong folder (method cũ)
        """
        try:
            folder_id = self.extract_folder_id(folder_input)
            return self.list_pdf_files_in_folder(folder_id)
        except Exception as e:
            print(f'Lỗi khi liệt kê files: {e}')
            return []