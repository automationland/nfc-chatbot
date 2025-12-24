import streamlit as st
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import time

# --- 1. CẤU HÌNH TRANG & CSS ---
load_dotenv()

PAGE_TITLE = "Trợ Lý The Gió Riverside"
CONTEXT_FILE = "context.txt"
MODEL_NAME = "gemini-2.0-flash-lite"

st.set_page_config(
    page_title=PAGE_TITLE, 
    page_icon="🏢", 
    layout="centered", # Layout centered nhìn giống app chat mobile hơn
    initial_sidebar_state="collapsed" # Thu gọn sidebar để tập trung vào chat
)

# Custom CSS để giao diện đẹp hơn
st.markdown("""
<style>
    /* Xóa padding thừa ở đầu trang */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Ẩn icon menu mặc định của Streamlit (3 dấu gạch) nếu muốn */
    /* #MainMenu {visibility: hidden;} */
    /* footer {visibility: hidden;} */
    
    /* Style cho khung chat */
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. HÀM LOAD DỮ LIỆU ---
@st.cache_data
def load_context():
    if os.path.exists(CONTEXT_FILE):
        with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return None

context_data = load_context()

# --- 3. XỬ LÝ SIDEBAR (SETTINGS) ---
with st.sidebar:
    st.header("⚙️ Cấu hình")
    
    # API Key Handling
    env_api_key = os.getenv("GEMINI_API_KEY")
    if env_api_key:
        st.success("✅ Đã kết nối API")
        api_key = env_api_key
    else:
        api_key = st.text_input("Gemini API Key:", type="password")
        st.info("Nhập key để bắt đầu chat.")
    
    st.markdown("---")
    
    # Nút Reset
    if st.button("Làm mới cuộc trò chuyện", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown(f"**Dữ liệu:** {'✅ Đã nạp' if context_data else '❌ Chưa có'}")

# --- 4. KHỞI TẠO CLIENT & PROMPT ---
if not context_data:
    st.error("⚠️ Chưa có dữ liệu. Vui lòng chạy file `convert_data.py` trước.")
    st.stop()

# --- CẤU HÌNH PROMPT (NHÂN CÁCH BOT) ---
# --- CẤU HÌNH PROMPT (ĐÃ FIX LỖI XIN SĐT) ---
SYS_INSTRUCT = f"""
VAI TRÒ:
Bạn là Chuyên viên Tư vấn BĐS của dự án The Gió Riverside.
Phong cách: Tinh gọn - Súc tích - Thực tế.

DỮ LIỆU NỀN TẢNG:
{context_data}

NGUYÊN TẮC TRẢ LỜI:
1.  **Cấu trúc:** Trả lời trực diện + 3-5 gạch đầu dòng + Insight ngắn gọn.
2.  **Trung thực:** Chỉ dùng thông tin trong dữ liệu.

3.  **QUAN TRỌNG - XỬ LÝ YÊU CẦU TÀI LIỆU:**
    * **Tuyệt đối KHÔNG xin thông tin cá nhân** (SĐT, Email, Zalo) của khách hàng dưới mọi hình thức.
    * Nếu khách hàng yêu cầu gửi "Bảng hàng", "Hình ảnh", "Chính sách chi tiết":
        * Hãy trích xuất ngay các thông tin chi tiết nhất (Giá, Diện tích, Mã căn...) có trong Dữ liệu nền tảng để trả lời ngay tại đây.
        * Nếu trong dữ liệu có đường link (URL) ảnh hoặc tài liệu, hãy gửi link đó.
        * Nếu không có thông tin chi tiết hơn, hãy nói: "Dạ hiện tại em có thể cung cấp ngay các thông tin cốt lõi sau đây..." và liệt kê ra.

4.  **Thái độ:** Nhiệt tình, hỗ trợ giải đáp ngay lập tức, không hẹn khách.
"""

client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Lỗi Key: {e}")

# --- 5. GIAO DIỆN CHAT ---
st.title(f"🏢 {PAGE_TITLE}")

# Khởi tạo history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lời chào nếu chưa có tin nhắn
if len(st.session_state.messages) == 0:
    st.info("👋 Chào sếp! Tôi là trợ lý ảo AI. Sếp cần thông tin gì về dự án The Gió hôm nay?")

# Render lịch sử chat
for msg in st.session_state.messages:
    # Chọn Avatar
    avatar = "👤" if msg["role"] == "user" else "🤖"
    role_ui = "assistant" if msg["role"] == "model" else "user"
    
    with st.chat_message(role_ui, avatar=avatar):
        st.markdown(msg["content"])

# --- 6. XỬ LÝ INPUT & LOADING ---
if prompt := st.chat_input("Hỏi về giá, vị trí, tiện ích..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Assistant Response (Có Loading)
    if client:
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            full_response = ""
            
            # --- HIỆU ỨNG LOADING ---
            # Spinner sẽ chạy cho đến khi data bắt đầu stream về
            with st.spinner("Đang tra cứu dữ liệu..."):
                try:
                    # Convert history cho SDK mới
                    chat_history = []
                    for m in st.session_state.messages:
                        role_api = "user" if m["role"] == "user" else "model"
                        chat_history.append(
                            types.Content(
                                role=role_api,
                                parts=[types.Part.from_text(text=m["content"])]
                            )
                        )

                    # Config
                    config = types.GenerateContentConfig(
                        system_instruction=SYS_INSTRUCT,
                        temperature=0.7
                    )

                    # Gọi API
                    response = client.models.generate_content_stream(
                        model=MODEL_NAME,
                        contents=chat_history,
                        config=config
                    )
                    
                    # Stream dữ liệu
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            # Hiệu ứng gõ máy (tùy chọn, stream trực tiếp thì bỏ sleep)
                            # time.sleep(0.01) 
                            message_placeholder.markdown(full_response + "▌")
                    
                    # Hoàn tất
                    message_placeholder.markdown(full_response)
                    
                    # Lưu vào session
                    st.session_state.messages.append({"role": "model", "content": full_response})

                except Exception as e:
                    message_placeholder.error(f"Lỗi: {e}")
    else:
        st.warning("Vui lòng nhập API Key để tiếp tục.")