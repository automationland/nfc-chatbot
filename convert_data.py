import pandas as pd
import os

# --- CẤU HÌNH ---
# 1. Đường dẫn file (Thư mục data/tên file)
EXCEL_FILE_PATH = os.path.join('data', 'source.xlsx')

# 2. Tên Sheet cần lấy dữ liệu
SHEET_NAME_PROJECT = 'The Gió' 

# 3. Cấu hình Cột (Index bắt đầu từ 0: A=0, B=1, C=2, D=3, E=4...)
COL_INDEX_KEY = 1    # Cột B: Câu hỏi/Tiêu chí
COL_INDEX_VALUE = 2  # Cột C: Dữ liệu của "The Gió" (Lưu ý: Eco Retreat trước đó là cột E=4)

OUTPUT_FILE = 'context.txt'

def clean_text(text):
    if pd.isna(text) or text == '-' or str(text).strip() == '':
        return None
    return str(text).strip()

def convert_excel_to_context():
    # Kiểm tra file có tồn tại không
    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"❌ Lỗi: Không tìm thấy file tại đường dẫn: {EXCEL_FILE_PATH}")
        print("👉 Vui lòng tạo folder 'data' và bỏ file 'source.xlsx' vào đó.")
        return

    full_context = ""
    print(f"📂 Đang đọc file: {EXCEL_FILE_PATH}...")
    
    try:
        xls = pd.ExcelFile(EXCEL_FILE_PATH)
        
        # --- XỬ LÝ SHEET "The Gió" ---
        if SHEET_NAME_PROJECT in xls.sheet_names:
            print(f"   -> Đang xử lý Sheet '{SHEET_NAME_PROJECT}'...")
            
            # Đọc sheet, không lấy header mặc định để dễ truy cập theo index
            df = pd.read_excel(xls, sheet_name=SHEET_NAME_PROJECT, header=None)
            
            full_context += f"# THÔNG TIN DỰ ÁN {SHEET_NAME_PROJECT.upper()}\n"
            
            for index, row in df.iterrows():
                # Lấy dữ liệu theo cột đã cấu hình
                col_0 = clean_text(row.get(0)) # Cột A (Mục lục)
                col_key = clean_text(row.get(COL_INDEX_KEY)) # Cột B
                col_val = clean_text(row.get(COL_INDEX_VALUE)) # Cột C (The Gió)
                
                # 1. Nhận diện tiêu đề mục lớn (I., II., III...)
                if col_0 and any(x in str(col_0) for x in ["I.", "II.", "III.", "IV.", "V."]):
                    title = f"{col_0} {col_key if col_key else ''}"
                    full_context += f"\n## {title}\n"
                
                # 2. Nhận diện câu hỏi - câu trả lời
                elif col_key and col_val:
                    full_context += f"- **{col_key}**: {col_val}\n"
        else:
            print(f"⚠️ Không tìm thấy Sheet '{SHEET_NAME_PROJECT}' trong file Excel.")

        # --- GHI FILE KẾT QUẢ ---
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_context)
        
        print(f"\n✅ Thành công! Dữ liệu đã được lưu vào '{OUTPUT_FILE}'")
        print(f"📊 Dung lượng: {len(full_context)} ký tự.")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    convert_excel_to_context()