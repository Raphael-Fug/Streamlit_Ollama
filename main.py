import streamlit as st
# from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import os
import json
from get_model import get_ollama_models

st.set_page_config("Trợ lý ảo C500")
st.title("Trợ lý ảo C500")
st.sidebar.image("./asset/favicon.png")
# st.sidebar.text("C500AI")

# Khởi tạo prompt system
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
    try: 
        with open("chat_history.json", "r", encoding="utf-8") as file: 
            return json.load(file) 
    except FileNotFoundError:
        return []  
        
def save_chat_history():
    with open("chat_history.json", "w", encoding="utf-8") as file: 
        json.dump(st.session_state.chat_history, file, ensure_ascii=False, indent=2) 


if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history_chat() 

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
    
    save_chat_history() 

if st.sidebar.button("Xoá lịch sử chat"):
    st.session_state.chat_history = [] 
    if os.path.exists("chat_history.json"):
        os.remove("chat_history.json") 
    st.rerun()
