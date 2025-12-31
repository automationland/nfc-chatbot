# NFC Chatbot - Trợ Lý Dự Án The Gió Riverside

## 📋 Mô tả dự án

Đây là một chatbot AI thông minh được thiết kế để tư vấn về dự án bất động sản **The Gió Riverside** tại Bình Dương. Chatbot sử dụng công nghệ AI của Google Gemini để trả lời các câu hỏi về giá cả, vị trí, tiện ích, chính sách thanh toán và các thông tin liên quan đến dự án.

## ✨ Tính năng chính

- **Trả lời tự động**: Sử dụng AI Gemini để phân tích và trả lời câu hỏi dựa trên dữ liệu thực tế
- **Giao diện thân thiện**: Giao diện chat mobile-friendly được xây dựng bằng Streamlit
- **Nguồn dữ liệu đa dạng**: Hỗ trợ dữ liệu từ Excel và PDF
- **Tùy chỉnh nguồn kiến thức**: Cho phép chọn các tài liệu cụ thể để chatbot tham khảo
- **Trích dẫn nguồn**: Mỗi câu trả lời đều có nguồn tham khảo để đảm bảo tính chính xác
- **Tự động handover**: Phát hiện tín hiệu mua hàng và chuyển tiếp khách hàng cho đội ngũ sale
- **Gửi thông báo Telegram**: Tự động gửi thông tin lead (khách hàng tiềm năng) qua Telegram
- **Phân tích hội thoại**: AI tự động tóm tắt và phân tích nhu cầu khách hàng để hỗ trợ sale

## 🛠️ Công nghệ sử dụng

- **Frontend**: Streamlit
- **AI Engine**: Google Gemini 2.5 Flash
- **Ngôn ngữ**: Python 3.8+
- **Thư viện chính**:
  - `streamlit` - Giao diện web
  - `google-genai` - Tích hợp Google AI
  - `pandas` - Xử lý dữ liệu Excel
  - `pypdf` - Đọc file PDF
  - `python-dotenv` - Quản lý biến môi trường
  - `requests` - Gửi thông báo Telegram

## 📦 Cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd nfc-chatbot
```

### 2. Tạo môi trường ảo
```bash
python -m venv venv
source venv/bin/activate  # Trên macOS/Linux
# hoặc
venv\Scripts\activate     # Trên Windows
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình API Key và Telegram
Tạo file `.env` trong thư mục gốc và thêm:
```
GEMINI_API_KEY=your_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

**Hướng dẫn lấy Telegram Token và Chat ID:**
1. Tạo bot Telegram qua [@BotFather](https://t.me/botfather)
2. Lấy `TELEGRAM_BOT_TOKEN` từ BotFather
3. Tạo group chat hoặc chat riêng với bot
4. Gửi tin nhắn bất kỳ cho bot
5. Truy cập `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` để lấy `chat_id`

## 📊 Chuẩn bị dữ liệu

### Chuyển đổi dữ liệu từ Excel
```bash
python convert_data_excel.py
```
- Chuyển đổi file Excel trong `data/xlsx/` thành text sạch trong `context/context1.txt`

### Chuyển đổi dữ liệu từ PDF
```bash
python convert_vision.py
```
- Sử dụng Google Gemini Vision để trích xuất nội dung từ PDF trong `data/pdf/` thành `context/context2.txt`

## 🚀 Chạy ứng dụng

```bash
streamlit run main.py
```

Ứng dụng sẽ chạy tại `http://localhost:8501`

## 📁 Cấu trúc thư mục

```
nfc-chatbot/
├── main.py                 # Ứng dụng chính Streamlit
├── convert_data_excel.py   # Script chuyển đổi dữ liệu Excel
├── convert_vision.py       # Script chuyển đổi dữ liệu PDF
├── requirements.txt        # Dependencies
├── context/                # Dữ liệu đã xử lý
│   ├── context.txt         # Dữ liệu tổng hợp
│   ├── context1.txt        # Dữ liệu từ Excel
│   ├── context2.txt        # Dữ liệu từ PDF
│   └── TheGio.txt          # Dữ liệu bổ sung
└── data/                   # Dữ liệu thô
    ├── pdf/                # File PDF gốc
    └── xlsx/               # File Excel gốc
```

## 💡 Cách sử dụng

1. **Khởi động chatbot**: Chạy `streamlit run main.py`
2. **Cấu hình dữ liệu**: Trong sidebar, chọn các tài liệu muốn chatbot tham khảo
3. **Đặt câu hỏi**: Nhập câu hỏi về dự án The Gió Riverside
4. **Nhận câu trả lời**: Chatbot sẽ trả lời dựa trên dữ liệu và trích dẫn nguồn

### Ví dụ câu hỏi:
- "Giá căn hộ studio là bao nhiêu?"
- "Dự án có tiện ích gì?"
- "Chính sách thanh toán như thế nào?"
- "Vị trí dự án ở đâu?"

## 🎯 Demo Chat

Dưới đây là ví dụ hội thoại thực tế với chatbot:

**Trợ Lý The Gió Riverside**

👤  
Dự án này nằm ở đâu vậy em?

🤖  
Dạ, dự án The Gió Riverside tọa lạc ngay mặt tiền đường ĐT16, tỉnh Bình Dương, và thừa hưởng view sông Đồng Nai tươi mát ạ.  

Vị trí này kết nối mọi tiện ích chỉ trong vài phút, như Big C, Coopmart, ga Metro, Bến xe Miền Đông, Suối Tiên, Thủy Châu, Làng Đại học.  

👉 Anh/chị có muốn xem thêm về các tiện ích quanh dự án không ạ?

👤  
Tiện ích có gì đặc biệt không? Anh thích bơi.

🤖  
Dạ, tiện ích nội khu The Gió Riverside có hồ bơi, công viên, khu BBQ, sân thể thao, phòng gym, khu vui chơi trẻ em ạ.  

Đặc biệt, khu phức hợp dưới nước trên tầng thượng (tầng 40) có hồ bơi vô cực tại 02 tháp Gió Đông & tháp Gió Nam, Jacuzzi, công viên nước trẻ em và tổng chiều dài khu chơi nước liên hoàn cho trẻ em trên sân thượng là 80m.  

👉 Bên em có thiết kế căn hộ rất thoáng, anh/chị xem qua layout nhé?

👤  
Giá rổ thế nào? Nghe nói 45 triệu hả?

🤖  
Dạ, đơn giá căn hộ The Gió Riverside từ 50 triệu/m² ạ. Giá rumor căn studio từ 1,8 - 2,3 tỷ đã bao gồm VAT ạ.  

Để chọn được căn tầng đẹp và nhận bảng tính dòng tiền chi tiết nhất cho từng đợt đóng, em xin phép kết nối anh/chị với chuyên viên hỗ trợ riêng nhé.  

📞 Anh/Chị nhắn giúp em số Zalo/SĐT để bạn ấy gửi file qua ngay ạ!

*(Sau khi khách hàng nhập số điện thoại)*

🤖  
Dạ em đã nhận số 123123123. Em đã nhắn bạn Sale ưu tiên hỗ trợ mình ngay rồi ạ!

## 🔧 Tùy chỉnh

### Thay đổi model AI
Trong `main.py`, sửa biến `MODEL_NAME`:
```python
MODEL_NAME = "gemini-2.5-flash-lite"  # hoặc "gemini-2.5-flash"
```

### Thay đổi prompt hệ thống
Sửa biến `SYS_INSTRUCT` trong `main.py` để tùy chỉnh cách chatbot trả lời.

### Thêm dữ liệu mới
1. Đặt file Excel/PDF vào thư mục tương ứng
2. Chạy script chuyển đổi
3. Khởi động lại ứng dụng

## 📋 Yêu cầu hệ thống

- Python 3.8+
- API Key của Google Gemini (từ Google AI Studio)
- Bot Token và Chat ID của Telegram (để gửi thông báo lead)
- Kết nối internet để gọi API Gemini và gửi Telegram

## 🙏 Lưu ý

- Chatbot chỉ trả lời dựa trên dữ liệu được cung cấp trong thư mục `context/`
- Đảm bảo có đủ dữ liệu trước khi chạy ứng dụng
- API Key Gemini cần có đủ quota để sử dụng
- Cấu hình Telegram để nhận thông báo lead tự động
- Khi phát hiện tín hiệu mua hàng, bot sẽ yêu cầu số điện thoại và chuyển tiếp cho sale

---

*Được phát triển với ❤️ cho dự án The Gió Riverside*</content>
<parameter name="filePath">/Users/taitran/nfc-chatbot/README.md