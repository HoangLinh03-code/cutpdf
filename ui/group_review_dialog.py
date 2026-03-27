import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class GroupReviewDialog(QDialog):
    """
    Hộp thoại cho phép người dùng kiểm tra và kéo thả gom nhóm PDF trước khi gửi AI.
    """
    def __init__(self, initial_groups, parent=None):
        super().__init__(parent)
        self.initial_groups = initial_groups # dict {"Tên Nhóm": ["path1", "path2"]}
        self.final_groups = {}
        self.init_ui()
        self.populate_tree()

    def init_ui(self):
        self.setWindowTitle("Kiểm tra & Chỉnh sửa Gộp File")
        self.resize(700, 500)
        layout = QVBoxLayout(self)

        lbl_info = QLabel("Vui lòng kiểm tra các nhóm bên dưới. Bạn có thể <b>kéo thả</b> file giữa các nhóm, tạo nhóm mới hoặc xóa file bị thừa.")
        lbl_info.setStyleSheet("color: #1565C0; font-size: 14px; margin-bottom: 10px;")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        # Thanh công cụ
        toolbar_layout = QHBoxLayout()
        self.btn_add_group = QPushButton("➕ Tạo Nhóm Mới")
        self.btn_remove = QPushButton("❌ Xóa Mục Chọn")
        
        self.btn_add_group.clicked.connect(self.create_new_group)
        self.btn_remove.clicked.connect(self.remove_selected_item)

        toolbar_layout.addWidget(self.btn_add_group)
        toolbar_layout.addWidget(self.btn_remove)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Tree Widget có hỗ trợ kéo thả
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Tên Nhóm / File PDF", "Đường dẫn gốc"])
        self.tree_widget.setColumnWidth(0, 400)
        self.tree_widget.setAlternatingRowColors(True)
        
        # Cấu hình kéo thả an toàn
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)
        self.tree_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.tree_widget)

        # Nút xác nhận
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Hủy Bỏ")
        self.btn_confirm = QPushButton("✅ XÁC NHẬN & CHẠY AI")
        self.btn_confirm.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_confirm.clicked.connect(self.accept_and_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

    def populate_tree(self):
        """Đưa dữ liệu từ dict lên cây"""
        for group_name, file_paths in self.initial_groups.items():
            # Nhóm (Không được kéo đi, chỉ nhận thả vào)
            group_item = QTreeWidgetItem(self.tree_widget)
            group_item.setText(0, f"📁 {group_name}")
            group_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDropEnabled)
            
            # File con (Được kéo đi, không nhận thả vào)
            for path in file_paths:
                file_item = QTreeWidgetItem(group_item)
                file_item.setText(0, f"📄 {os.path.basename(path)}")
                file_item.setText(1, path)
                file_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
        
        self.tree_widget.expandAll()

    def create_new_group(self):
        name, ok = QInputDialog.getText(self, "Tạo Nhóm Mới", "Nhập tên nhóm (Tên bài viết ra file Word):")
        if ok and name.strip():
            group_item = QTreeWidgetItem(self.tree_widget)
            group_item.setText(0, f"📁 {name.strip()}")
            group_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDropEnabled)
            self.tree_widget.scrollToItem(group_item)

    def remove_selected_item(self):
        root = self.tree_widget.invisibleRootItem()
        for item in self.tree_widget.selectedItems():
            (item.parent() or root).removeChild(item)

    def accept_and_save(self):
        """Quét lại cây để lấy cấu trúc dữ liệu người dùng đã chốt"""
        self.final_groups = {}
        root = self.tree_widget.invisibleRootItem()
        
        for i in range(root.childCount()):
            group_item = root.child(i)
            # Nếu lỡ kéo file ra ngoài thành cấp 1, bỏ qua hoặc xử lý
            if "📁" not in group_item.text(0):
                continue
                
            group_name = group_item.text(0).replace("📁 ", "").strip()
            file_paths = []
            
            for j in range(group_item.childCount()):
                file_item = group_item.child(j)
                path = file_item.text(1)
                if path:
                    file_paths.append(path)
            
            if file_paths: # Bỏ qua nhóm rỗng
                self.final_groups[group_name] = file_paths
                
        if not self.final_groups:
            QMessageBox.warning(self, "Lỗi", "Không có nhóm nào hợp lệ chứa file để xử lý!")
            return
            
        self.accept() # Đóng dialog và trả về code Accepted

    def get_final_data(self):
        return self.final_groups