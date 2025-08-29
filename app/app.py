import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json
import os
from get_model import get_ollama_models

st.set_page_config("Trợ lý ảo C500")
st.title("Trợ lý ảo C500")
favicon_path = os.path.join(os.path.dirname(__file__), 'favicon.png')
st.sidebar.image(favicon_path)


if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = """
    Bạn là một trợ lý ảo thông minh và hữu ích tên là C500AI. Hãy trả lời các câu hỏi của người dùng một cách chính xác, rõ ràng và thân thiện.

    Khi trả lời:
    - Luôn giữ giọng điệu lịch sự và chuyên nghiệp
    - Cung cấp thông tin chính xác và đáng tin cậy
    - Nếu không biết câu trả lời, hãy thừa nhận điều đó thay vì đoán mò
    - Hỗ trợ người dùng giải quyết vấn đề một cách hiệu quả
    - Trả lời ngắn gọn và dễ hiểu

    Nếu người dùng hỏi về thông tin cá nhân hoặc yêu cầu thực hiện hành động không phù hợp, hãy từ chối một cách lịch sự và giải thích lý do.
    """

if "show_prompt_editor" not in st.session_state:
    st.session_state.show_prompt_editor = False

# JavaScript functions để tương tác với Local Storage
def inject_local_storage_js():
    st.markdown("""
    <script>
    // Hàm lưu dữ liệu vào Local Storage
    function saveToLocalStorage(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (e) {
            console.error('Error saving to localStorage:', e);
            return false;
        }
    }
    
    // Hàm lấy dữ liệu từ Local Storage
    function getFromLocalStorage(key) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error('Error getting from localStorage:', e);
            return null;
        }
    }
    
    // Hàm xóa dữ liệu từ Local Storage
    function removeFromLocalStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Error removing from localStorage:', e);
            return false;
        }
    }
    
    // Expose functions to Streamlit
    window.localStorageManager = {
        save: saveToLocalStorage,
        get: getFromLocalStorage,
        remove: removeFromLocalStorage
    };
    </script>
    """, unsafe_allow_html=True)

# Inject JavaScript
inject_local_storage_js()

with st.sidebar:
    st.header("Cài đặt")
    models = get_ollama_models()
    
    if models:
        model_names = [model["name"] for model in models]
        selected_model = st.selectbox(
            "Chọn mô hình:", 
            model_names,
            index=model_names.index("hf.co/uonlp/Vistral-7B-Chat-gguf:Q4_0") if "hf.co/uonlp/Vistral-7B-Chat-gguf:Q4_0" in model_names else 0
        )
    else:
        st.warning("Không tìm thấy mô hình nào.")
        selected_model = "hf.co/uonlp/Vistral-7B-Chat-gguf:Q4_0" 

    if st.button("Chỉnh prompt system"):
        st.session_state.show_prompt_editor = not st.session_state.show_prompt_editor

    if st.session_state.show_prompt_editor:
        default_prompt = """
        Bạn là một trợ lý ảo thông minh và hữu ích tên là C500AI. Hãy trả lời các câu hỏi của người dùng một cách chính xác, rõ ràng và thân thiện.

        Khi trả lời:
        - Luôn giữ giọng điệu lịch sự và chuyên nghiệp
        - Cung cấp thông tin chính xác và đáng tin cậy
        - Nếu không biết câu trả lời, hãy thừa nhận điều đó thay vì đoán mò
        - Hỗ trợ người dùng giải quyết vấn đề một cách hiệu quả
        - Trả lời ngắn gọn và dễ hiểu

        Nếu người dùng hỏi về thông tin cá nhân hoặc yêu cầu thực hiện hành động không phù hợp, hãy từ chối một cách lịch sự và giải thích lý do.
        """
        
        prompt_input = st.text_area(
            label="Prompt System", 
            value=st.session_state.system_prompt,
            height=200,
            help="Cập nhật Prompt System cho AI"
        )
        
        if st.button("Cập nhật Prompt"):
            if prompt_input.strip():  
                st.session_state.system_prompt = prompt_input
                st.success("Đã cập nhật prompt hệ thống!")
            else:
                st.warning("Prompt không được để trống!")    
                
        if st.button("Khôi phục mặc định"):
            st.session_state.system_prompt = default_prompt
            st.success("Đã khôi phục prompt mặc định!")
            st.rerun() 

def generate_response(question):
    try:
        chat_model = ChatOllama(model=selected_model)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", st.session_state.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        chat_history = []
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_history.append(AIMessage(content=msg["content"]))
        
        chain = prompt | chat_model
        
        response = chain.invoke({
            "chat_history": chat_history,
            "question": question
        })
        
        return response.content
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return f"Đã xảy ra lỗi: {str(e)}"

def load_history_chat():
    """Load chat history từ Local Storage thông qua JavaScript"""
    load_script = """
    <script>
    function loadChatHistory() {
        const history = localStorage.getItem('c500_chat_history');
        if (history) {
            try {
                const parsed = JSON.parse(history);
                // Gửi dữ liệu về Streamlit
                window.parent.postMessage({
                    type: 'chat_history',
                    data: parsed
                }, '*');
                return parsed;
            } catch (e) {
                console.error('Error parsing chat history:', e);
                return [];
            }
        }
        return [];
    }
    
    // Load ngay khi script chạy
    loadChatHistory();
    </script>
    """
    
    st.components.v1.html(load_script, height=0)
    
    return []

def save_chat_history():
    """Lưu chat history vào Local Storage"""
    if st.session_state.chat_history:
        # Tạo JavaScript để lưu dữ liệu
        save_script = f"""
        <script>
        try {{
            const chatHistory = {json.dumps(st.session_state.chat_history, ensure_ascii=False)};
            localStorage.setItem('c500_chat_history', JSON.stringify(chatHistory));
            console.log('Chat history saved to localStorage');
        }} catch (e) {{
            console.error('Error saving chat history:', e);
        }}
        </script>
        """
        
        st.components.v1.html(save_script, height=0)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
    # Thử load từ Local Storage khi khởi tạo
    load_script = """
    <script>
    function initChatHistory() {
        const history = localStorage.getItem('c500_chat_history');
        if (history) {
            try {
                const parsed = JSON.parse(history);
                // Hiển thị trong console để debug
                console.log('Loaded chat history:', parsed);
                
                // Có thể sử dụng Streamlit's session state thông qua callback
                if (window.streamlitCallbacks && window.streamlitCallbacks.setChatHistory) {
                    window.streamlitCallbacks.setChatHistory(parsed);
                }
            } catch (e) {
                console.error('Error loading chat history:', e);
            }
        }
    }
    
    // Chạy khi DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChatHistory);
    } else {
        initChatHistory();
    }
    </script>
    """
    st.components.v1.html(load_script, height=0)

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Nhập câu hỏi")

if question:
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    
    response = generate_response(question)
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    # Lưu vào Local Storage
    save_chat_history()

if st.sidebar.button("Xoá lịch sử chat"):
    st.session_state.chat_history = []
    
    # Xóa từ Local Storage
    clear_script = """
    <script>
    try {
        localStorage.removeItem('c500_chat_history');
        console.log('Chat history cleared from localStorage');
    } catch (e) {
        console.error('Error clearing chat history:', e);
    }
    </script>
    """
    st.components.v1.html(clear_script, height=0)
    
    st.success("Đã xóa lịch sử chat!")
    st.rerun()

if st.sidebar.button("Tải lại lịch sử"):
    load_script = """
    <script>
    const history = localStorage.getItem('c500_chat_history');
    if (history) {
        try {
            const parsed = JSON.parse(history);
            console.log('Reloaded chat history:', parsed);
            alert('Đã tải lại lịch sử chat từ Local Storage. Vui lòng refresh trang để xem.');
        } catch (e) {
            console.error('Error reloading chat history:', e);
            alert('Lỗi khi tải lại lịch sử chat.');
        }
    } else {
        alert('Không có lịch sử chat trong Local Storage.');
    }
    </script>
    """
    st.components.v1.html(load_script, height=0)
