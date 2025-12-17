import os

def rename_ctst_to_kntt(root_folder):
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith('.pdf') and "CTST" in filename:
                new_filename = filename.replace("CTST", "KNTT")
                old_path = os.path.join(dirpath, filename)
                new_path = os.path.join(dirpath, new_filename)
                os.rename(old_path, new_path)
                print(f"Đã đổi tên: {old_path} -> {new_path}")

# Sử dụng:
root_folder = r"D:\CutPdfByDrive\downloaded_pdfs\SBT_KNTT_full"
rename_ctst_to_kntt(root_folder)