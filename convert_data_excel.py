import pandas as pd
import os
import glob
import argparse
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- CẤU HÌNH ---
load_dotenv()
DATA_FOLDER = os.path.join('data', 'xlsx') 
OUTPUT_FILE = 'context/context1.txt' 
# Cập nhật model khả dụng (2.0)
MODEL_NAME = "gemini-2.5-flash"
CHUNK_SIZE = 15000 

# Màu sắc hiển thị Terminal
class Colors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Khởi tạo API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print(f"{Colors.FAIL}❌ Lỗi: Chưa cấu hình GEMINI_API_KEY trong file .env{Colors.ENDC}")
    exit()

client = genai.Client(api_key=api_key)

def clean_chunk_with_ai(text_chunk, index, total):
    """Gửi đoạn text lên AI để làm sạch và xóa trùng lặp"""
    print(f"      ... AI đang xử lý đoạn {index}/{total} ({len(text_chunk)} ký tự)...", end='\r')
    
    # Prompt được tinh chỉnh để trả về data thuần khiết
    prompt = f"""
    VAI TRÒ: Bạn là Chuyên gia Biên tập Dữ liệu (Data Editor) cho hệ thống RAG (Retrieval Augmented Generation).
    
    NHIỆM VỤ:
    1. **SỬA LỖI CHÍNH TẢ:** Kiểm tra và sửa lỗi chính tả tiếng Việt, lỗi gõ máy (typo) trong văn bản.
    2. **CHUẨN HÓA:** Viết hoa chữ cái đầu câu, tên riêng, địa danh (VD: "hcm" -> "TP.HCM", "thủ đức" -> "Thủ Đức").
    3. **FORMAT MARKDOWN:** Trình bày lại dữ liệu dưới dạng danh sách thông tin (Bullet points) hoặc Bảng (Table) sao cho dễ đọc nhất.
       - Với các thông số kỹ thuật (diện tích, giá, tầng...), hãy dùng định dạng: `- **Tên trường**: Giá trị`
    4. **BẢO TOÀN DỮ LIỆU:**
       - TUYỆT ĐỐI KHÔNG tự ý xóa thông tin chi tiết (như mô tả dài).
       - TUYỆT ĐỐI KHÔNG sửa đổi con số (giá tiền, diện tích, số điện thoại, mã căn).
       - Chỉ xóa dòng nếu nó hoàn toàn vô nghĩa (VD: "null", "NaN", "---").

    INPUT (Dữ liệu thô từ Excel):
    {text_chunk}

    OUTPUT (Chỉ trả về Markdown sạch, không thêm lời dẫn):
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0)
        )
        # Làm sạch các ký tự thừa nếu AI lỡ thêm vào
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```"): # Xóa markdown block nếu có
            cleaned_text = cleaned_text.replace("```markdown", "").replace("```", "")
        return cleaned_text
    except Exception as e:
        print(f"\n      ❌ Lỗi API: {e}")
        return text_chunk

def process_large_text(full_text):
    """
    LOGIC MỚI: Cắt theo dòng (New Line) an toàn.
    Không bao giờ cắt giữa chừng một dòng dữ liệu.
    """
    if not full_text.strip():
        return ""
        
    lines = full_text.split('\n')
    chunks = []
    current_chunk = []
    current_length = 0
    
    for line in lines:
        line_len = len(line) + 1 # +1 cho ký tự xuống dòng
        
        # Nếu cộng thêm dòng này mà vượt quá giới hạn -> Đẩy chunk cũ đi, tạo chunk mới
        if current_length + line_len > CHUNK_SIZE:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = line_len
        else:
            current_chunk.append(line)
            current_length += line_len
            
    # Đẩy chunk cuối cùng nếu còn
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    
    # Xử lý từng chunk
    cleaned_parts = []
    for i, chunk in enumerate(chunks):
        cleaned = clean_chunk_with_ai(chunk, i+1, len(chunks))
        cleaned_parts.append(cleaned)
        
    return "\n".join(cleaned_parts)

def read_and_parse_excel(file_path):
    """Giữ nguyên logic đọc Excel của bạn"""
    try:
        xls = pd.ExcelFile(file_path)
        sheet_name = 'The Gió' if 'The Gió' in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        df.dropna(how='all', inplace=True) 
        df.dropna(axis=1, how='all', inplace=True)
        
        raw_text = ""
        for index, row in df.iterrows():
            row_items = []
            for col_name, val in row.items():
                if pd.notna(val) and str(val).strip() != "":
                    if "Unnamed" in str(col_name):
                        row_items.append(str(val).strip())
                    else:
                        row_items.append(f"{col_name}: {str(val).strip()}")
            
            if row_items:
                raw_text += " | ".join(row_items) + "\n"
        return raw_text
    except Exception as e:
        print(f"❌ Lỗi đọc file {os.path.basename(file_path)}: {e}")
        return ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str)
    args = parser.parse_args()

    if args.file:
        target_path = os.path.join(DATA_FOLDER, args.file)
        files_to_process = [target_path] if os.path.exists(target_path) else []
        mode = "SINGLE_FILE"
    else:
        files_to_process = glob.glob(os.path.join(DATA_FOLDER, "*.xlsx"))
        mode = "FULL_FOLDER"

    if not files_to_process:
        print(f"⚠️ Không tìm thấy file .xlsx nào.")
        return

    # Nếu chạy Full Folder -> Reset file output sạch trơn
    if mode == "FULL_FOLDER":
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("") # Xóa trắng file, không viết Header ngày tháng

    print(f"{Colors.HEADER}🚀 BẮT ĐẦU XỬ LÝ...{Colors.ENDC}")

    for i, file_path in enumerate(files_to_process):
        filename = os.path.basename(file_path)
        print(f"\n[{i+1}/{len(files_to_process)}] 🔄 File: {Colors.BOLD}{filename}{Colors.ENDC}")
        
        raw_text = read_and_parse_excel(file_path)
        
        if raw_text:
            clean_text = process_large_text(raw_text)
            
            # Ghi file theo format Markdown đơn giản: ## Nguồn -> Data
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n## Nguồn: {filename}\n") # Tiêu đề file dạng Markdown H2
                f.write(clean_text + "\n") # Data sạch
            
            print(f"   ✅ Xong. (Gốc: {len(raw_text)} -> Sạch: {len(clean_text)})")
        else:
            print(f"   ⚠️ File rỗng.")

    print(f"\n{Colors.OKGREEN}🎉 HOÀN TẤT! Kiểm tra file: '{OUTPUT_FILE}'{Colors.ENDC}")

if __name__ == "__main__":
    main()