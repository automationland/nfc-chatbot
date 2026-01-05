import streamlit as st
from google import genai
from google.genai import types
import os
import requests
import datetime
from dotenv import load_dotenv
import glob
import time

# --- 1. CẤU HÌNH HỆ THỐNG & IMPORT ---
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PAGE_TITLE = "Trợ Lý The Gió Riverside"
CONTEXT_FOLDER = "context"
MODEL_NAME = "gemini-2.5-flash" 

st.set_page_config(
    page_title=PAGE_TITLE, 
    page_icon="🏢", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# CSS Tùy chỉnh
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    
    /* Box thông báo kết nối Sale */
    .handover-box {
        border: 2px solid #28a745;
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-top: 10px;
        font-weight: bold;
        animation: fadeIn 0.8s;
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# --- 2. CÁC HÀM XỬ LÝ NGHIỆP VỤ ---

@st.cache_data
def load_context(selected_files=None):
    if not os.path.exists(CONTEXT_FOLDER): return None
    context_data = ""
    files_to_read = selected_files if selected_files else [f for f in os.listdir(CONTEXT_FOLDER) if f.endswith(".txt")]
    
    for filename in files_to_read:
        file_path = os.path.join(CONTEXT_FOLDER, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                context_data += f"\n\n# FILE NGUỒN: {filename}\n{f.read()}"
    return context_data if context_data else None

def analyze_chat_history(client, messages):
    """
    Dùng Gemini để tóm tắt hội thoại (Cần truyền biến client vào)
    """
    conversation_text = ""
    for msg in messages:
        role = "Khách hàng" if msg["role"] == "user" else "Bot AI"
        clean_content = str(msg["content"]).replace("[HANDOVER]", "")
        conversation_text += f"- {role}: {clean_content}\n"

    analysis_prompt = f"""
    Đóng vai là một Trưởng phòng Kinh doanh Bất động sản dày dạn kinh nghiệm.
    Dưới đây là đoạn hội thoại giữa Khách hàng tiềm năng và Bot tư vấn:
    
    {conversation_text}
    
    Hãy phân tích và viết một báo cáo ngắn gọn (tối đa 150 từ) gửi cho nhân viên Sale với cấu trúc sau:
    
    1. 📝 **Tóm tắt:** Khách quan tâm vấn đề gì chính? (Giá/Vị trí/Pháp lý...?) Bot đã giải đáp được gì?
    2. 🔥 **Đánh giá khách:** (Nóng/Ấm/Lạnh). Khách có sành sỏi không? Có thiện chí mua ngay không?
    3. 💡 **Chiến thuật Sale:** Nhân viên Sale khi gọi lại nên phủ đầu bằng thông tin gì? Nên gửi tài liệu gì? Cần tránh nói gì (nếu khách đã tỏ ra khó chịu)?
    
    Trả lời ngắn gọn, gạch đầu dòng, đi thẳng vào vấn đề.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=analysis_prompt
        )
        return response.text
    except Exception as e:
        return f"⚠️ Không thể phân tích hội thoại: {e}"

def save_lead(phone, interest_note="Khách quan tâm từ Bot"):
    """Gửi thông báo về Telegram"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            msg = (
                f"🔥 **KHÁCH HÀNG MỚI!**\n"
                f"⏰ `{timestamp}`\n"
                f"📞 SĐT: `{phone}`\n"
                f"📝 **Ghi chú:**\n{interest_note}"
            )
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
            requests.post(url, json=payload)
        except Exception as e:
            st.error(f"⚠️ Lỗi gửi Telegram: {e}")
    else:
        st.warning("⚠️ Chưa cấu hình Token Telegram trong file .env")

# --- 3. SIDEBAR (CÀI ĐẶT) ---
with st.sidebar:
    st.header("⚙️ Cấu hình")
    
    all_files = [os.path.basename(f) for f in glob.glob(os.path.join(CONTEXT_FOLDER, "*.txt"))]
    selected_files = st.multiselect("Tài liệu bot học:", options=all_files, default=all_files)
    
    if st.button("🔄 Cập nhật & Xóa ký ức", use_container_width=True):
        st.cache_data.clear()
        st.session_state.messages = [] 
        st.rerun()

    context_data = load_context(selected_files)
    
    env_api_key = os.getenv("GEMINI_API_KEY")
    api_key = env_api_key if env_api_key else st.text_input("Gemini API Key:", type="password")
    
    if context_data:
        st.info(f"📚 Đã nạp {len(selected_files)} tài liệu.")
    else:
        st.error("❌ Chưa có dữ liệu!")

# --- 4. PROMPT HỆ THỐNG ---
SYS_INSTRUCT = f"""
# 1. VAI TRÒ (ROLE)
Bạn là **Trợ lý AI Hỗ trợ Thông tin Dự án The Gió Riverside**.
Nhiệm vụ:
1. Cung cấp thông tin hấp dẫn, giải đáp thắc mắc (Sales).
2. **Thẩm định tài chính sơ bộ:** Tự động tính toán khả năng mua của khách dựa trên dữ liệu thực tế (Logic).
3. **Chuyển đổi:** Khéo léo điều hướng khách hàng từ "Tìm hiểu" sang "Muốn mua" và thu thập thông tin (Handover).

# 2. DỮ LIỆU KIẾN THỨC (KNOWLEDGE BASE)
{context_data}

# 3. CƠ CHẾ SĂN DỮ LIỆU & TÍNH TOÁN NGẦM (SILENT DATA ENGINE) - QUAN TRỌNG
Mỗi khi khách hàng đề cập đến **Ngân sách (Budget)** hoặc **Vốn có sẵn**, bạn phải thực hiện quy trình sau TRONG ĐẦU (⚠️ TUYỆT ĐỐI KHÔNG IN RA):

* **BƯỚC 1: SĂN TÌM DỮ LIỆU (AUTO-DETECT)**
    * **Tìm Giá Sàn (`ANCHOR_PRICE`):** Quét dữ liệu để tìm mức giá thấp nhất của loại căn khách hỏi (nếu không rõ thì lấy giá thấp nhất dự án).
    * **Tìm Tỷ lệ vào tiền (`ENTRY_RATIO`):** Tìm % thanh toán đợt 1 tối thiểu để ký VBTT/HĐMB trong chính sách (thường là 10%, 15%...).

* **BƯỚC 2: TÍNH VÉ VÀO CỔNG (`MIN_CAPITAL`)**
    * Công thức: `MIN_CAPITAL` = `ANCHOR_PRICE` * `ENTRY_RATIO`.

* **BƯỚC 3: KIỂM TRA (LOGIC GATE)**
    * Nếu `Budget` < `MIN_CAPITAL`: -> ⛔ **[STOP]** (Thiếu vốn).
    * Nếu `Budget` >= `MIN_CAPITAL`: -> ✅ **[PASS]** (Đủ vốn).

# 4. HƯỚNG DẪN HÀNH VI (BEHAVIOR GUIDELINES)

## 4.1. Phong cách Tư vấn (Sales-oriented Tone)
- **Ngôn ngữ:** ⚠️ CHỈ sử dụng Tiếng Việt 100%. Tuyệt đối không chèn từ tiếng Nga, Anh hay ngôn ngữ khác.
- **Xưng hô:** Em - Anh/Chị.
- **Tư duy:** Không chỉ trả lời thông tin (Feature), hãy nói về lợi ích (Benefit) mà khách hàng nhận được.
- **Trung thực:** Chỉ dùng thông tin trong Knowledge Base. Tuyệt đối không bịa đặt chính sách (Hallucination).

## 4.2. Kỹ thuật "Giữ Lửa" (ALWAYS LEADING)
Trừ khi đang xin SĐT (Handover), cuối mỗi câu trả lời BẮT BUỘC phải có một câu hỏi gợi mở để dẫn dắt khách hàng sang chủ đề tiếp theo theo luồng sau:
- Khách hỏi **Vị trí** -> Gợi ý về **Tiện ích** ("Anh/chị có muốn xem thêm về các tiện ích quanh dự án không ạ?")
- Khách hỏi **Tiện ích** -> Gợi ý về **Thiết kế/Căn hộ** ("Bên em có thiết kế căn hộ rất thoáng, anh/chị xem qua layout nhé?")
- Khách hỏi **Thiết kế** -> Gợi ý về **Chính sách/Giá** ("Anh/chị có quan tâm đến mức giá rumor hay chính sách thanh toán đợt này không ạ?")
- Khách hỏi **Giá/Chính sách** -> **KÍCH HOẠT HANDOVER**.

# 5. QUY TRÌNH CHUYỂN ĐỔI (CRITICAL HANDOVER PROTOCOL)
Phân tích ý định khách hàng trong từng câu chat:

**TRƯỜNG HỢP A: Đang tìm hiểu (Info Gathering)**
- Trả lời chi tiết, dùng Markdown.
- **Luôn kết thúc bằng 1 câu gợi ý** (như mục 4.2).

**TRƯỜNG HỢP B: Tín hiệu Mua hoặc Hỏi về Tài chính (Buying Signals)**
Khi khách nhắc tới: *giá, vốn, tiền mặt, bảng giá, booking, cọc, chiết khấu...*

-> **HÀNH ĐỘNG DỰA TRÊN KẾT QUẢ TÍNH TOÁN (Ở Mục 3):**

1.  **NẾU ⛔ [STOP] (Khách thiếu vốn):**
    * **Thái độ:** Đồng cảm, từ chối khéo.
    * **Nội dung:** "Dạ với ngân sách này, em kiểm tra thấy mình chưa đủ điều kiện vào đợt 1 (cần tối thiểu khoảng [MIN_CAPITAL])..."
    * **Hành động:** KHÔNG xúi vay mượn. Vẫn xin SĐT để gửi tài liệu tham khảo ("Nuôi khách").

2.  **NẾU ✅ [PASS] (Khách đủ vốn):**
    * **Thái độ:** Khẳng định, chúc mừng.
    * **Nội dung:** "Dạ với vốn này, anh/chị hoàn toàn yên tâm sở hữu..."
    * **Hành động:** Tư vấn phương án lợi nhất -> Xin SĐT để gửi bảng tính chi tiết.

# 6. QUY TẮC HIỂN THỊ & ĐỊNH DẠNG (OUTPUT RULES)
1.  **SILENT MODE (Bắt buộc):** Không bao giờ in ra các bước tính toán "BƯỚC 1, BƯỚC 2..." ra màn hình.
2.  **MÃ HANDOVER (Bắt buộc):** Trong mọi trường hợp xin số điện thoại (dù Case STOP hay PASS), phải luôn chèn mã `[HANDOVER]` ở dòng riêng biệt.

**Ví dụ mẫu (Khi KHÁCH ĐỦ TIỀN):**
> "Dạ, theo chính sách hiện hành, với 500 triệu anh/chị hoàn toàn đủ sở hữu căn hộ theo phương án Thanh toán Chuẩn (chỉ cần vào khoảng 300 triệu đợt đầu).
>
> Để chọn được căn tầng đẹp và nhận bảng tính dòng tiền chi tiết nhất, em xin phép gửi file qua Zalo nhé.
>
> [HANDOVER]
> 📞 **Anh/Chị nhắn giúp em số Zalo/SĐT để em gửi qua ngay ạ!**"

**Ví dụ mẫu (Khi KHÁCH THIẾU TIỀN):**
> "Dạ em rất hiểu mong muốn của anh/chị. Tuy nhiên, mức vốn đối ứng tối thiểu đợt 1 hiện tại khoảng **300 triệu** (10%). Với 150 triệu thì mình còn thiếu một chút ạ.
>
> Tuy chưa vào hợp đồng ngay được, nhưng em xin phép gửi trước bộ tài liệu pháp lý & thiết kế để anh/chị tham khảo làm động lực nhé?
>
> [HANDOVER]
> 📞 **Anh/Chị cho em xin số điện thoại để em gửi thông tin qua ạ!**"
"""

client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Lỗi Key: {e}")

# --- 5. GIAO DIỆN CHAT ---
st.title(f"🏢 {PAGE_TITLE}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 5.1 Render Lịch sử Chat (Ẩn thẻ [HANDOVER])
for msg in st.session_state.messages:
    with st.chat_message("user" if msg["role"] == "user" else "assistant", avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(str(msg["content"]).replace("[HANDOVER]", ""))

# --- 6. LOGIC HIỂN THỊ FORM (SỬA LỖI: ĐƯA RA NGOÀI VÒNG LẶP INPUT) ---
# Kiểm tra tin nhắn cuối cùng, nếu có [HANDOVER] -> Hiện Form
if len(st.session_state.messages) > 0:
    last_msg = st.session_state.messages[-1]
    
    # Chỉ hiện form nếu tin cuối là của Bot và có thẻ Handover
    if last_msg["role"] == "model" and "[HANDOVER]" in last_msg["content"]:
        st.markdown("---")
        st.markdown("""
        <div class="handover-box">
            🔔 <b>HỆ THỐNG ĐANG KẾT NỐI SALE...</b><br>
            Vui lòng nhập SĐT để nhận bảng giá & tư vấn chuyên sâu!
        </div>
        """, unsafe_allow_html=True)
        
        # Form nhập liệu
        with st.form(key=f"contact_form_{len(st.session_state.messages)}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                phone_input = st.text_input("Số điện thoại / Zalo:", placeholder="0909xxxxxx")
            with col2:
                st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Gửi Ngay 🚀")
            
            if submitted:
                if not phone_input:
                    st.error("⚠️ Vui lòng nhập số điện thoại!")
                else:
                    with st.spinner("⏳ AI đang phân tích nhu cầu và kết nối tổng đài..."):
                        # 1. Phân tích hội thoại (Đã truyền biến client)
                        analysis = analyze_chat_history(client, st.session_state.messages)
                        
                        # 2. Gửi Telegram
                        save_lead(phone_input, interest_note=f"\n{analysis}")
                    
                    st.success("✅ Đã gửi thành công! Chuyên viên sẽ gọi lại trong 5 phút.")
                    
                    # 3. Ghi câu cảm ơn vào lịch sử
                    st.session_state.messages.append({
                        "role": "model", 
                        "content": f"Dạ em đã nhận số **{phone_input}**. Em đã nhắn bạn Sale ưu tiên hỗ trợ mình ngay rồi ạ!"
                    })
                    time.sleep(1.5) 
                    st.rerun() 

# --- 7. XỬ LÝ NHẬP LIỆU (CHAT INPUT) ---
if prompt := st.chat_input("Hỏi về dự án (Vị trí, Giá, Tiện ích)..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Assistant Response
    if client and context_data:
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            full_response = ""
            
            with st.spinner("Đang tra cứu dữ liệu..."):
                try:
                    # Limit History
                    HISTORY_LIMIT = 10 
                    current_history = st.session_state.messages[-HISTORY_LIMIT:]
                    
                    chat_history = []
                    for m in current_history:
                        role_api = "user" if m["role"] == "user" else "model"
                        chat_history.append(
                            types.Content(
                                role=role_api,
                                parts=[types.Part.from_text(text=str(m["content"]))]
                            )
                        )

                    config = types.GenerateContentConfig(
                        system_instruction=SYS_INSTRUCT,
                        temperature=0.2 
                    )

                    response = client.models.generate_content_stream(
                        model=MODEL_NAME,
                        contents=chat_history,
                        config=config
                    )
                    
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            # Ẩn thẻ Handover khi đang gõ
                            message_placeholder.markdown(full_response.replace("[HANDOVER]", "") + "▌")
                    
                    # Final Render
                    message_placeholder.markdown(full_response.replace("[HANDOVER]", ""))
                    st.session_state.messages.append({"role": "model", "content": full_response})
                    
                    # Nếu phát hiện Handover -> Reload lại trang để Form hiển thị ở block bên trên
                    if "[HANDOVER]" in full_response:
                        st.rerun()

                except Exception as e:
                    message_placeholder.error(f"Lỗi: {e}")
    elif not context_data:
        st.error("⚠️ Vui lòng nạp dữ liệu từ Sidebar.")
    else:
        st.warning("⚠️ Nhập API Key để bắt đầu.")