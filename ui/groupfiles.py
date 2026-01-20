import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class PDFGrouper:
    def _clean_filename_no_regex(self, filename):
        """
        Làm sạch tên file không dùng Regex. 
        Chuyển về chữ thường, thay ký tự đặc biệt bằng dấu cách và cắt bỏ tiền tố.
        """
        # 1. Bỏ đuôi file và chuyển về chữ thường
        name = os.path.splitext(filename)[0].lower()
        
        # 2. Thay thế các ký tự phân tách phổ biến bằng khoảng trắng
        special_chars = "_-.,()[]+"
        for char in special_chars:
            name = name.replace(char, " ")
        
        # 3. Tìm từ "bài" - Đây là điểm bắt đầu của nội dung chính
        # Nếu thấy từ "bài", ta lấy từ vị trí đó trở đi để loại bỏ "rác" phía trước
        pos = name.find("bài")
        if pos != -1:
            name = name[pos:]
            
        # 4. Chuẩn hóa khoảng trắng (loại bỏ dấu cách thừa)
        return " ".join(name.split())

    def smart_group_files(self, all_file_paths):
        file_data = []
        for fp in all_file_paths:
            fname = os.path.basename(fp)
            file_data.append({
                'path': fp,
                'name': fname,
                'clean_text': self._clean_filename_no_regex(fname)
            })

        # TF-IDF xử lý text
        corpus = [f['clean_text'] for f in file_data]
        # analyzer='word' sẽ tự động tách từ dựa trên khoảng trắng và ký tự đặc biệt
        vectorizer = TfidfVectorizer(ngram_range=(1, 3))
        tfidf_matrix = vectorizer.fit_transform(corpus)
        sim_matrix = cosine_similarity(tfidf_matrix)

        groups = {}
        visited = [False] * len(file_data)

        for i in range(len(file_data)):
            if visited[i]: continue
            
            current_group = [file_data[i]['path']]
            visited[i] = True
            
            # Lấy tên nhóm từ tên file sạch đầu tiên (Viết hoa chữ cái đầu)
            group_name = file_data[i]['clean_text'].title()

            for j in range(i + 1, len(file_data)):
                if not visited[j] and sim_matrix[i][j] > 0.6:
                    current_group.append(file_data[j]['path'])
                    visited[j] = True
            
            groups[group_name] = current_group

        return groups

def main(list_path: str=""):
    # print(list_path)
    grouper = PDFGrouper()
    grouped_results = grouper.smart_group_files(list_path)

    print(f"\n=== KẾT QUẢ GỘP NHÓM ({len(grouped_results)} nhóm) ===\n")
    

    return grouped_results