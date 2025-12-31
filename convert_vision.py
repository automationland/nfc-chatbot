import os
import glob
import time
import argparse
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter

# Ensure UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

# --- CẤU HÌNH ---
load_dotenv()
DATA_FOLDER = os.path.join('data', 'pdf') 
OUTPUT_FILE = 'context/context2.txt'
TEMP_FOLDER = 'temp_chunks' # Thư mục tạm

MODEL_NAME = "gemini-2.5-flash" 
CHUNK_SIZE = 4 # Số trang mỗi lần xử lý

class Colors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print(f"{Colors.FAIL}❌ Lỗi: Thiếu API Key{Colors.ENDC}")
    exit()

client = genai.Client(api_key=api_key)

def process_chunk(pdf_path, start_page, end_page, total_pages):
    """Xử lý một cụm trang (Chunk)"""
    try:
        file_size = os.path.getsize(pdf_path)
        print(f"      📄 Pages {start_page}-{end_page}/{total_pages} | ☁️  Upload ({round(file_size/1024)} KB)...", end='\r')
        
        # Upload Binary
        with open(pdf_path, "rb") as f:
            uploaded_file = client.files.upload(
                file=f, 
                config=types.UploadFileConfig(mime_type="application/pdf", display_name=f"chunk_{start_page}_{end_page}")
            )
        
        # Chờ Active
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(0.5)
            uploaded_file = client.files.get(name=uploaded_file.name)
            
        if uploaded_file.state.name != "ACTIVE":
            return ""

        print(f"      📄 Pages {start_page}-{end_page}/{total_pages} | 👀 Gemini đang đọc & trích xuất...", end='\r')

        # --- PROMPT ĐƯỢC CẤU HÌNH CHO CHUNKING ---
        prompt = f"""
        VAI TRÒ: Bạn là Chuyên gia Biên tập Dữ liệu Bất động sản (Data Editor).
        NHIỆM VỤ: Trích xuất nội dung từ trang {start_page} đến {end_page} của tài liệu đính kèm.

        QUY TẮC CẤM (BẮT BUỘC):
        1. 🚫 TUYỆT ĐỐI KHÔNG DÙNG BẢNG (No Markdown Tables).
        2. 🚫 KHÔNG TÓM TẮT (No Summarization): Phải lấy chi tiết từng dòng, từng con số, không bỏ sót điều khoản nào.

        YÊU CẦU ĐỊNH DẠNG:
        1. **Cấu trúc:** Sử dụng `###` cho tiêu đề lớn.
        2. **Xử lý bảng:** Phá vỡ bảng thành danh sách `* **Key**: Value`.
           - Ví dụ: `* **Đợt 1**: Thanh toán 10% ngay khi ký HĐMB.`
        3. **Context:** Chỉ trả về nội dung dữ liệu, không cần lời chào. Bỏ qua header/footer (số trang, tên file).
        
        HÃY XỬ LÝ THEO QUY TẮC TRÊN:
        """

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                temperature=0.1, 
                max_output_tokens=8192
            )
        )
        
        extracted_text = response.text if response.text else ""
        
        # Dọn dẹp file trên cloud
        try:
            client.files.delete(name=uploaded_file.name)
        except: pass
            
        print(f"      📄 Pages {start_page}-{end_page}/{total_pages} | ✅ Xong ({len(extracted_text)} chars)      ")
        return extracted_text

    except Exception as e:
        print(f"\n      ❌ Lỗi chunk {start_page}-{end_page}: {e}")
        return ""

def split_and_process_pdf(file_path):
    """Cắt file gốc thành các chunk nhỏ và xử lý lần lượt"""
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)

    try:
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        full_text = ""

        print(f"   ✂️  Phát hiện {total_pages} trang. Gom nhóm {CHUNK_SIZE} trang/lần gửi...")

        # Vòng lặp cắt file: 0, 4, 8, 12...
        for i in range(0, total_pages, CHUNK_SIZE):
            start_idx = i
            end_idx = min(i + CHUNK_SIZE, total_pages)
            
            # Tạo file PDF con
            writer = PdfWriter()
            for page_num in range(start_idx, end_idx):
                writer.add_page(reader.pages[page_num])
            
            temp_filename = os.path.join(TEMP_FOLDER, f"temp_{start_idx}_{end_idx}.pdf")
            with open(temp_filename, "wb") as f:
                writer.write(f)
            
            # Gửi file con đi xử lý
            chunk_content = process_chunk(temp_filename, start_idx+1, end_idx, total_pages)
            
            if chunk_content:
                full_text += f"\n\n--- Dữ liệu trang {start_idx+1}-{end_idx} ---\n" + chunk_content
            
            # Xóa file con local
            try:
                os.remove(temp_filename)
            except: pass
            
            time.sleep(1) # Nghỉ nhẹ tránh spam API

        return full_text
        
    except Exception as e:
        print(f"   ❌ Lỗi đọc PDF: {e}")
        return ""
    finally:
        # Dọn dẹp folder tạm
        try:
            if os.path.exists(TEMP_FOLDER):
                for f in os.listdir(TEMP_FOLDER):
                    os.remove(os.path.join(TEMP_FOLDER, f))
                os.rmdir(TEMP_FOLDER)
        except: pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str)
    args = parser.parse_args()

    if args.file:
        mode = "SINGLE_FILE"
        target_path = os.path.join(DATA_FOLDER, args.file)
        files_to_process = [target_path] if os.path.exists(target_path) else []
    else:
        mode = "FULL_FOLDER"
        files_to_process = sorted(glob.glob(os.path.join(DATA_FOLDER, "*.pdf")))

    if not files_to_process:
        print(f"⚠️ Không có file PDF trong {DATA_FOLDER}.")
        return

    # Nếu chạy Full Folder -> Reset file output
    if mode == "FULL_FOLDER":
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("") 

    print(f"{Colors.HEADER}🚀 BẮT ĐẦU VISION CONVERTER (CHUNKING MODE: {CHUNK_SIZE} pages){Colors.ENDC}")
    
    for i, file_path in enumerate(files_to_process):
        filename = os.path.basename(file_path)
        print(f"\n[{i+1}/{len(files_to_process)}] 🔄 File: {Colors.BOLD}{filename}{Colors.ENDC}")
        
        clean_content = split_and_process_pdf(file_path)
        
        if clean_content:
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n## Nguồn: {filename}\n") 
                f.write("Dưới đây là dữ liệu chi tiết đã được trích xuất:\n\n")
                f.write(clean_content + "\n")
                f.write(f"\n{'='*50}\n")
            
            print(f"   ✅ Xong. Dữ liệu đã được gộp và ghi vào {OUTPUT_FILE}.")
        else:
            print(f"   ⚠️ Lỗi/Rỗng.")

    print(f"\n{Colors.OKGREEN}🎉 HOÀN TẤT! File '{OUTPUT_FILE}' đã xuất thành công.{Colors.ENDC}")

if __name__ == "__main__":
    main()