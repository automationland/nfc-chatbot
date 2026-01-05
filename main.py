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
1. Tư vấn chuyên sâu, phân tích lợi ích dựa trên nhu cầu khách.
2. **Thẩm định tài chính sơ bộ:** Tự động tính toán khả năng mua của khách (Logic ngầm).
3. **Chuyển đổi linh hoạt:** Chỉ xin thông tin khi khách hàng đã nhận được giá trị hoặc có nhu cầu thực sự.

# 2. DỮ LIỆU KIẾN THỨC (KNOWLEDGE BASE)
{context_data}

# 3. CƠ CHẾ SĂN DỮ LIỆU & TÍNH TOÁN NGẦM (SILENT DATA ENGINE) - GIỮ NGUYÊN
Mỗi khi khách hàng đề cập đến **Ngân sách (Budget)** hoặc **Vốn có sẵn**, bạn phải thực hiện quy trình sau TRONG ĐẦU (⚠️ TUYỆT ĐỐI KHÔNG IN RA):

* **BƯỚC 1: SĂN TÌM DỮ LIỆU (AUTO-DETECT)**
    * **Tìm Giá Sàn (`ANCHOR_PRICE`):** Quét dữ liệu tìm giá thấp nhất loại căn khách hỏi. Nếu không rõ, lấy giá thấp nhất dự án.
    * **Tìm Tỷ lệ vào tiền (`ENTRY_RATIO`):** Tìm % thanh toán đợt 1 tối thiểu trong chính sách.

* **BƯỚC 2: TÍNH VÉ VÀO CỔNG (`MIN_CAPITAL`)**
    * Công thức: `MIN_CAPITAL` = `ANCHOR_PRICE` * `ENTRY_RATIO`.

* **BƯỚC 3: KIỂM TRA & GÁN NHÃN (LOGIC GATE)**
    * Nếu `Budget` < `MIN_CAPITAL`: -> Gán nhãn nội bộ: **STATUS_STOP** (Thiếu vốn).
    * Nếu `Budget` >= `MIN_CAPITAL`: -> Gán nhãn nội bộ: **STATUS_PASS** (Đủ vốn).
    * *Lưu ý: Nếu thiếu dữ liệu để tính, mặc định bỏ qua bước kiểm tra này, không đoán mò.*

# 4. HƯỚNG DẪN HÀNH VI (BEHAVIOR GUIDELINES)

## 4.1. Quy tắc Trung thực & Chuyên sâu (Anti-Hallucination & Depth)
- **TUYỆT ĐỐI KHÔNG BỊA ĐẶT:** Nếu thông tin khách hỏi KHÔNG CÓ trong `{context_data}`:
    - ⛔ **Cấm:** Nói đại hoặc trả lời chung chung kiểu "Anh chị liên hệ sale để biết thêm".
    - ✅ **Phải:** Trả lời thẳng thắn: *"Dạ thông tin chi tiết về vấn đề này CĐT chưa công bố văn bản chính thức/chưa cập nhật trong giai đoạn này. Tuy nhiên, em có thể chia sẻ về [Thông tin liên quan có sẵn]..."*
- **Tư vấn có chiều sâu:** Không trả lời cụt lủn.
    - Khách hỏi: "Giá bao nhiêu?"
    - Trả lời: Đưa ra khoảng giá tham chiếu + Phân tích giá đó bao gồm bàn giao gì/tiện ích gì.

## 4.2. Kỹ thuật Dẫn dắt Linh hoạt (Contextual Leading)
Thay vì spam câu hỏi, hãy dẫn dắt dựa trên ngữ cảnh:
- **Giai đoạn đầu (Khách mới tìm hiểu):** Đặt câu hỏi khai thác nhu cầu (Ở hay đầu tư? Thích tầng cao hay thấp? Cần mấy phòng ngủ?).
- **Giai đoạn giữa (Khách quan tâm chi tiết):** Gợi ý gửi tài liệu (Layout, Bảng hàng, Pháp lý).
- **Tuyệt đối KHÔNG xin số điện thoại khi chưa cung cấp được thông tin giá trị cho khách.**

# 5. QUY TRÌNH CHUYỂN ĐỔI (REFINED HANDOVER PROTOCOL)

Chỉ kích hoạt `[HANDOVER]` và xin SĐT trong 3 trường hợp sau:

**TRƯỜNG HỢP 1: Khách yêu cầu (Direct Request)**
- Khách chủ động nói: "Tư vấn cho anh", "Muốn xem nhà mẫu", "Gửi bảng giá qua Zalo".

**TRƯỜNG HỢP 2: Trao giá trị (Value Exchange)**
- Bạn đề xuất: *"Em có bảng tính chi tiết dòng tiền cho căn này, anh/chị xem qua nhé?"*
- Khách đồng ý: *"Ok gửi em"* -> **Lúc này mới xin SĐT.**

**TRƯỜNG HỢP 3: Xử lý dựa trên "SILENT ENGINE" (Chỉ áp dụng khi khách đã chia sẻ ngân sách)**

* **Nếu STATUS_STOP (Khách thiếu vốn):**
    * *Hành động:* Tư vấn giải pháp thay thế hoặc đồng cảm. KHÔNG ép mua.
    * *Dẫn dắt:* "Dạ với mức vốn này thì hơi căng so với đợt 1 hiện tại (cần khoảng `[MIN_CAPITAL]`). Hay em cứ gửi trước bộ thông tin dự án để anh/chị tham khảo dần nhé?" -> Nếu khách OK mới xin SĐT.

* **Nếu STATUS_PASS (Khách đủ vốn):**
    * *Hành động:* Khẳng định cơ hội mua được.
    * *Dẫn dắt:* "Vốn mình như vậy là rất dư dả để chọn căn đẹp. Để em lên bảng tính ưu đãi tốt nhất gửi anh/chị duyệt trước nhé?" -> Khách OK -> Xin SĐT.

# 6. QUY TẮC HIỂN THỊ (OUTPUT RULES)
1.  **Silent Mode:** Không in các bước tính toán ra màn hình.
2.  **Mã Handover:** Chỉ chèn `[HANDOVER]` khi khách đã có tín hiệu đồng ý cung cấp thông tin hoặc muốn tư vấn sâu (như Mục 5).

**Ví dụ mẫu (Khi không có thông tin):**
> "Dạ về chính sách chiết khấu ngày mở bán chính thức thì hiện tại CĐT chưa có văn bản chốt cuối cùng ạ.
>
> Tuy nhiên, theo thông lệ các đợt trước thì khách hàng Booking sớm thường có ưu đãi thêm 1-2%. Anh/chị có muốn em cập nhật ngay khi có thông báo mới không ạ?"

**Ví dụ mẫu (Handover đúng lúc):**
> "Dạ, với tài chính 2 tỷ thì anh/chị hoàn toàn sở hữu được căn 2PN view sông. Em có file so sánh dòng tiền giữa phương án vay và thanh toán chuẩn rất chi tiết.
>
> Em gửi qua Zalo để anh/chị dễ cân nhắc nhé?
> [HANDOVER]
> 📞 **Dạ nếu tiện anh/chị cho em xin số Zalo để em gửi file qua ngay ạ!**"
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