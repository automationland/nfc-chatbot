import os
import requests
from dotenv import load_dotenv

# 1. Nạp biến môi trường từ file .env
load_dotenv()

# 2. Lấy Token và Chat ID
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_test_message():
    # Kiểm tra xem đã cấu hình trong .env chưa
    if not TOKEN or not CHAT_ID:
        print("❌ LỖI: Chưa tìm thấy TOKEN hoặc CHAT_ID trong file .env")
        print("👉 Vui lòng mở file .env và thêm dòng: TELEGRAM_BOT_TOKEN=... và TELEGRAM_CHAT_ID=...")
        return

    print(f"⚙️ Đang thử kết nối tới Bot ID: ...{TOKEN[-5:]}")
    print(f"📨 Đang gửi tin nhắn tới Chat ID: {CHAT_ID}")

    # Nội dung tin nhắn test
    message = (
        "🚀 **TEST KẾT NỐI THÀNH CÔNG!**\n"
        "--------------------------------\n"
        "✅ Hệ thống Bot The Gió Riverside đã sẵn sàng.\n"
        "⏰ Thời gian: Ngay bây giờ\n"
        "📢 Đây là tin nhắn tự động từ Python."
    )

    # Gửi request
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown" # Để chữ đậm/nghiêng đẹp hơn
    }

    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("\n✅ THÀNH CÔNG! Hãy kiểm tra điện thoại của bạn ngay.")
        else:
            print(f"\n❌ THẤT BẠI. Mã lỗi: {response.status_code}")
            print("Chi tiết lỗi:", response.text)
            
    except Exception as e:
        print(f"\n❌ LỖI KẾT NỐI: {e}")

if __name__ == "__main__":
    send_test_message()