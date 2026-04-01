import os
import sys
import io
import time
import random
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QComboBox, QPushButton, QMessageBox, 
    QFileDialog, QScrollArea, QGroupBox, QFrame
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Đảm bảo import đúng project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google import genai
from google.genai import types
from PIL import Image

# Chỉ lấy hàm get_vertex_ai_credentials từ callAPI
from modules.common.callAPI import get_vertex_ai_credentials

# =====================================================================
# HÀM NÉN ẢNH (COMPRESS)
# =====================================================================
def compress_image_to_min(image_bytes, max_size=(1024,1024), quality=75):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="JPEG", quality=quality, optimize=True)
        return output_buffer.getvalue()
    except Exception as e:
        print(f"Lỗi nén ảnh: {e}")
        return image_bytes

# =====================================================================
# LUỒNG XỬ LÝ GEN NHIỀU ẢNH (CÓ TÙY CHỌN MODEL & FALLBACK)
# =====================================================================
class BatchImageGenThread(QThread):
    progress = pyqtSignal(str)
    image_done = pyqtSignal(str, str, bytes) 
    finished_all = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, vi_prompts, en_prompts, aspect_ratio, model_vi, model_en):
        super().__init__()
        self.vi_prompts = vi_prompts
        self.en_prompts = en_prompts
        self.aspect_ratio = aspect_ratio
        self.model_vi = model_vi
        self.model_en = model_en
        self.is_running = True

    def generate_single_image(self, client, prompt, lang):
        if lang == 'vi':
            final_prompt = f"Vẽ hình ảnh minh họa chính xác cho mô tả sau: {prompt}"
            selected_model = self.model_vi
        else:
            final_prompt = f"Generate a high-quality, accurate illustration based on the following description: {prompt}"
            selected_model = self.model_en

        if selected_model == "gemini-3-pro-image-preview":
            models_to_try = ["gemini-3-pro-image-preview", "gemini-3.1-flash-image-preview"]
        else:
            models_to_try = [selected_model]

        max_retries = 3
        base_delay = 8

        for model_name in models_to_try:
            for attempt in range(max_retries):
                if not self.is_running: return None
                
                try:
                    self.progress.emit(f"🔄 Đang gọi {model_name}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=final_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
                            candidate_count=1,
                            image_config=types.ImageConfig(aspect_ratio=self.aspect_ratio),
                        )
                    )
                    
                    for part in response.parts:
                        if part.inline_data and part.inline_data.data:
                            raw_bytes = part.inline_data.data
                            compressed_bytes = compress_image_to_min(raw_bytes)
                            return compressed_bytes
                            
                    return None
                    
                except Exception as api_err:
                    error_str = str(api_err).lower()
                    if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                        if attempt < max_retries - 1:
                            sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0.1, 1.5)
                            self.progress.emit(f"⚠️ Quá tải API ({model_name}). Thử lại sau {sleep_time:.1f}s...")
                            time.sleep(sleep_time)
                            continue
                        else:
                            break 
                    else:
                        break 
                        
        return None

    def run(self):
        try:
            creds = get_vertex_ai_credentials()
            project_id = os.getenv("PROJECT_ID")
            
            if not creds or not project_id:
                self.error.emit("❌ Thiếu Credentials hoặc Project ID trong file .env.gen")
                return

            client = genai.Client(vertexai=True, project=project_id, location="global", credentials=creds)

            # Xử lý Tiếng Việt
            for i, prompt in enumerate(self.vi_prompts):
                if not self.is_running: break
                self.progress.emit(f"🇻🇳 Đang xử lý VI ({i+1}/{len(self.vi_prompts)}): {prompt[:30]}...")
                
                img_bytes = self.generate_single_image(client, prompt, 'vi')
                if img_bytes:
                    self.image_done.emit('vi', prompt, img_bytes)
                    self.progress.emit(f"✅ Xong VI ({i+1}/{len(self.vi_prompts)}). Đang làm nguội API...")
                    time.sleep(3)
                else:
                    self.error.emit(f"❌ Thất bại khi sinh ảnh VI: {prompt[:30]}")

            # Xử lý Tiếng Anh
            for i, prompt in enumerate(self.en_prompts):
                if not self.is_running: break
                self.progress.emit(f"🇬🇧 Đang xử lý EN ({i+1}/{len(self.en_prompts)}): {prompt[:30]}...")
                
                img_bytes = self.generate_single_image(client, prompt, 'en')
                if img_bytes:
                    self.image_done.emit('en', prompt, img_bytes)
                    self.progress.emit(f"✅ Xong EN ({i+1}/{len(self.en_prompts)}). Đang làm nguội API...")
                    time.sleep(3)
                else:
                    self.error.emit(f"❌ Thất bại khi sinh ảnh EN: {prompt[:30]}")

            self.progress.emit("🎉 ĐÃ HOÀN TẤT TOÀN BỘ DANH SÁCH!")
            self.finished_all.emit()

        except Exception as e:
            self.error.emit(f"❌ Lỗi Exception: {str(e)}")
            self.finished_all.emit()

    def stop(self):
        self.is_running = False

# =====================================================================
# GIAO DIỆN CHÍNH
# =====================================================================
class GenImageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.generated_images = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("🎨 SINH ẢNH HÀNG LOẠT TỪ MÔ TẢ")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        input_group = QGroupBox("1. Dán danh sách mô tả (Mỗi mô tả nằm trên 1 dòng)")
        input_layout = QVBoxLayout()

        # --- TEXTBOX ---
        row_text_layout = QHBoxLayout()
        
        col_vi = QVBoxLayout()
        col_vi.addWidget(QLabel("🇻🇳 Danh sách mô tả Tiếng Việt:"))
        self.txt_vi = QTextEdit()
        self.txt_vi.setPlaceholderText("Sơ đồ mạch điện gồm điện trở R nối tiếp tụ C\nĐồ thị hàm số bậc 2 Parabol...")
        self.txt_vi.setFixedHeight(120)
        col_vi.addWidget(self.txt_vi)
        row_text_layout.addLayout(col_vi)

        col_en = QVBoxLayout()
        col_en.addWidget(QLabel("🇬🇧 Danh sách mô tả Tiếng Anh (Bỏ trống nếu không cần):"))
        self.txt_en = QTextEdit()
        self.txt_en.setPlaceholderText("AC circuit diagram with resistor R...\nParabola graph of quadratic function...")
        self.txt_en.setFixedHeight(120)
        col_en.addWidget(self.txt_en)
        row_text_layout.addLayout(col_en)

        input_layout.addLayout(row_text_layout)

        # --- CẤU HÌNH MODEL & TỶ LỆ ---
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("🤖 Model VI:"))
        self.cb_model_vi = QComboBox()
        self.cb_model_vi.addItems(["gemini-3-pro-image-preview", "gemini-3.1-flash-image-preview", "gemini-2.5-flash-image"])
        config_layout.addWidget(self.cb_model_vi)

        config_layout.addWidget(QLabel("🤖 Model EN:"))
        self.cb_model_en = QComboBox()
        self.cb_model_en.addItems(["gemini-2.5-flash-image", "gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview"])
        config_layout.addWidget(self.cb_model_en)

        config_layout.addWidget(QLabel("📐 Tỷ lệ:"))
        self.cb_ratio = QComboBox()
        self.cb_ratio.addItems(["1:1", "16:9", "4:3", "3:4", "9:16"])
        config_layout.addWidget(self.cb_ratio)
        
        config_layout.addStretch()
        input_layout.addLayout(config_layout)

        # --- NÚT BẤM ---
        btn_layout = QHBoxLayout()
        self.btn_generate = QPushButton("🚀 BẮT ĐẦU SINH ẢNH")
        self.btn_generate.setStyleSheet("padding: 8px; font-weight: bold; background-color: #27ae60; color: white;")
        self.btn_generate.clicked.connect(self.start_batch_generation)
        btn_layout.addWidget(self.btn_generate)

        self.btn_stop = QPushButton("⏹️ Dừng lại")
        self.btn_stop.setStyleSheet("padding: 8px; font-weight: bold; background-color: #e74c3c; color: white;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_generation)
        btn_layout.addWidget(self.btn_stop)

        input_layout.addLayout(btn_layout)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # --- THANH TRẠNG THÁI ---
        self.lbl_status = QLabel("Sẵn sàng.")
        self.lbl_status.setStyleSheet("color: #2980b9; font-weight: bold;")
        layout.addWidget(self.lbl_status)

        # --- HIỂN THỊ KẾT QUẢ ---
        result_group = QGroupBox("2. Kết quả ảnh (Tự động lưu vào folder 'Output sinh ảnh')")
        result_layout = QVBoxLayout()
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.results_container = QWidget()
        self.results_vbox = QVBoxLayout(self.results_container)
        self.results_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.results_container)
        
        result_layout.addWidget(self.scroll_area)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

    def sanitize_filename(self, text, max_len=45):
        """Xóa ký tự cấm và cắt ngắn chuỗi để làm tên file"""
        clean = re.sub(r'[\\/*?:"<>|]', "", text)
        clean = clean.replace('\n', ' ').strip()
        if len(clean) > max_len:
            clean = clean[:max_len].strip() + "..."
        return clean

    def start_batch_generation(self):
        raw_vi = self.txt_vi.toPlainText().split('\n')
        raw_en = self.txt_en.toPlainText().split('\n')
        
        vi_prompts = [p.strip() for p in raw_vi if p.strip()]
        en_prompts = [p.strip() for p in raw_en if p.strip()]

        if not vi_prompts and not en_prompts:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập ít nhất 1 dòng mô tả!")
            return

        self.clear_results()
        self.btn_generate.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.generated_images.clear()

        aspect_ratio = self.cb_ratio.currentText()
        model_vi = self.cb_model_vi.currentText()
        model_en = self.cb_model_en.currentText()

        self.thread = BatchImageGenThread(vi_prompts, en_prompts, aspect_ratio, model_vi, model_en)
        self.thread.progress.connect(self.update_status)
        self.thread.error.connect(self.handle_error)
        self.thread.image_done.connect(self.add_result_card)
        self.thread.finished_all.connect(self.handle_finished)
        self.thread.start()

    def update_status(self, msg):
        self.lbl_status.setText(msg)

    def handle_error(self, err_msg):
        self.lbl_status.setText(err_msg)

    def handle_finished(self):
        self.btn_generate.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def stop_generation(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.lbl_status.setText("⚠️ Đã gửi lệnh dừng. Đang chờ tiến trình hiện tại thoát...")
            self.btn_stop.setEnabled(False)

    def clear_results(self):
        for i in reversed(range(self.results_vbox.count())): 
            widget = self.results_vbox.itemAt(i).widget()
            if widget is not None: 
                widget.setParent(None)

    def add_result_card(self, lang, prompt, img_bytes):
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; margin-bottom: 5px; }")
        card_layout = QHBoxLayout(card)
        
        info_layout = QVBoxLayout()
        lang_icon = "🇻🇳 [VI]" if lang == "vi" else "🇬🇧 [EN]"
        lbl_info = QLabel(f"<b>{lang_icon}</b> {prompt}")
        lbl_info.setWordWrap(True)
        info_layout.addWidget(lbl_info)
        
        btn_save = QPushButton("💾 Lưu Ảnh Này")
        btn_save.setStyleSheet("padding: 5px; background-color: #2980b9; color: white; font-weight: bold; border-radius: 3px;")
        
        img_index = len(self.generated_images)
        self.generated_images.append(img_bytes)
        
        # Đưa trực tiếp `prompt` vào nút bấm qua hàm lambda
        btn_save.clicked.connect(lambda checked, idx=img_index, l=lang, p=prompt: self.save_single_image(idx, l, p))
        
        info_layout.addWidget(btn_save)
        info_layout.addStretch()
        card_layout.addLayout(info_layout, stretch=2)

        lbl_img = QLabel()
        lbl_img.setStyleSheet("border: none; background: transparent;")
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        image = QImage()
        image.loadFromData(img_bytes)
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        lbl_img.setPixmap(scaled_pixmap)
        
        card_layout.addWidget(lbl_img, stretch=1)
        self.results_vbox.addWidget(card)

    def save_single_image(self, idx, lang, prompt):
        if idx >= len(self.generated_images): return
        bytes_data = self.generated_images[idx]
        
        # 1. Tạo folder "Output sinh ảnh" tự động nếu chưa có
        output_dir = os.path.join(project_root, "Output sinh ảnh")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 2. Xử lý tên file từ prompt (cắt ngắn + xóa ký tự lỗi)
        safe_prompt = self.sanitize_filename(prompt, max_len=45)
        default_name = f"{safe_prompt} ({lang.upper()}).jpg"
        
        # 3. Ép hộp thoại lưu mở mặc định vào folder Output
        default_path = os.path.join(output_dir, default_name)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Lưu ảnh {lang.upper()}", default_path, "JPEG Images (*.jpg);;PNG Images (*.png)"
        )
        
        if file_path:
            try:
                with open(file_path, "wb") as f:
                    f.write(bytes_data)
                QMessageBox.information(self, "Thành công", f"Đã lưu ảnh tại:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu file:\n{str(e)}")