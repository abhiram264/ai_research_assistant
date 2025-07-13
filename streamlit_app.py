
import os
import shutil
import tempfile
import pdfplumber
import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
import arxiv
import requests
import base64
import streamlit.components.v1 as components

# Load API Key
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]


if not GOOGLE_API_KEY:
    st.error("❌ GOOGLE_API_KEY not found in .env file")
    st.stop()

# Constants
EMBED_DIR = "embeddings/faiss_index"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200

# Auto-clear FAISS index at each app run
if os.path.exists(EMBED_DIR):
    shutil.rmtree(EMBED_DIR)

# Initialize Models
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
chat_model = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-flash",
    google_api_key=GOOGLE_API_KEY,
    system_message="You are a helpful AI assistant for analyzing academic papers. If the documents don't contain the answer, try to infer based on your own knowledge."
)

# Page Setup
st.set_page_config(page_title="AI Research Assistant", layout="wide")
st.title("🤖 AI-Powered Research Assistant")

with st.expander("📌 Project Overview", expanded=True):
    st.markdown("""
    Welcome to your **AI Research Assistant**!  
    Upload or search academic papers, and get instant Q&A, summaries, and insights powered by **Google Gemini + FAISS + LangChain**.
    """)

# Session State Setup
for key in ["mode", "selected_pdfs", "qa_chain", "chat_history"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "mode" else []

# Action Area
st.markdown("### 🔍 Choose Your Input Method")
col1, col2 = st.columns(2)
with col1:
    if st.button("📄 Upload PDFs", use_container_width=True):
        st.session_state.mode = "upload"
with col2:
    if st.button("🌐 Search ArXiv", use_container_width=True):
        st.session_state.mode = "search"

# PDF Preview Utility
def preview_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return "\n\n".join(page.extract_text() or "" for page in pdf.pages)

# Show PDF in iframe


def display_pdf(file_path):
    file_name = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    # Offer fallback download button
    st.download_button(
        label="📄 View PDF in new tab (recommended for Chrome)",
        data=pdf_bytes,
        file_name=file_name,
        mime="application/pdf",
    )

    # Inline iframe (will work in Firefox & some environments)
    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="700"
            type="application/pdf">
        </iframe>
    """
    components.html(pdf_display, height=700, scrolling=True)





# Chunk PDFs (with abstract prioritization)
def process_pdf(file_path):
    docs = PyPDFLoader(file_path).load()
    first_page_text = docs[0].page_content if docs else ""
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)
    if first_page_text:
        chunks.insert(0, Document(page_content=first_page_text, metadata={"source": "first_page"}))
    return chunks

# ArXiv search and download
def search_arxiv(topic, max_results=5):
    return list(arxiv.Search(query=topic, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance).results())

def download_arxiv_pdf(paper):
    title = paper.title.strip().replace(" ", "_").replace("/", "_")
    file_path = f"data/{title}.pdf"
    response = requests.get(paper.pdf_url)
    if response.status_code == 200 and response.content.startswith(b"%PDF"):
        os.makedirs("data", exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    return None

# --- Upload Mode ---
if st.session_state.mode == "upload":
    st.markdown("### 📥 Upload Your PDFs")
    uploaded_files = st.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True, label_visibility="collapsed")

    if uploaded_files:
        all_chunks = []
        st.session_state.selected_pdfs = []

        with st.spinner("Processing uploaded files..."):
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    pdf_path = tmp_file.name
                    st.session_state.selected_pdfs.append(pdf_path)
                    display_pdf(pdf_path)
                    all_chunks.extend(process_pdf(pdf_path))

            st.success(f"✅ Processed {len(uploaded_files)} file(s)")

        with st.spinner("Creating FAISS vector store..."):
            vectorstore = FAISS.from_documents(all_chunks, embedding_model)
            vectorstore.save_local(EMBED_DIR)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
            st.session_state.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=chat_model,
                retriever=retriever,
                return_source_documents=False
            )

# --- ArXiv Mode ---
elif st.session_state.mode == "search":
    st.markdown("### 🌐 Search Research on ArXiv")
    topic = st.text_input("🔎 Enter a research topic")

    if topic:
        with st.spinner("Fetching papers..."):
            results = search_arxiv(topic)

        if not results:
            st.warning("No results found.")
        else:
            for i, paper in enumerate(results):
                with st.expander(f"{i+1}. {paper.title}"):
                    st.markdown(f"**Authors:** {', '.join(a.name for a in paper.authors)}")
                    st.markdown(f"**Published:** {paper.published.date()}")
                    if st.button(f"📥 Load this Paper", key=f"load_{i}"):
                        pdf_path = download_arxiv_pdf(paper)
                        if pdf_path:
                            st.session_state.selected_pdfs = [pdf_path]
                            st.session_state.qa_chain = None
                            st.session_state.mode = "loaded"
                            st.rerun()

# --- Loaded PDF Mode ---
if st.session_state.mode == "loaded" and st.session_state.selected_pdfs:
    long_form_instruction = (
    "Please provide a long, detailed, and clearly structured explanation. "
    "Use simple language, include context, and break down complex terms. "
    "Imagine you are teaching this to someone new to the topic."
)

    st.markdown("### 📖 PDF Viewer")
    for pdf_path in st.session_state.selected_pdfs:
        file_name = os.path.basename(pdf_path)
        st.subheader(f"📘 Loaded File: `{file_name}`")
        display_pdf(pdf_path)

    if not st.session_state.qa_chain:
        all_chunks = []
        with st.spinner("Creating FAISS index from loaded paper..."):
            for pdf_path in st.session_state.selected_pdfs:
                all_chunks.extend(process_pdf(pdf_path))
            vectorstore = FAISS.from_documents(all_chunks, embedding_model)
            vectorstore.save_local(EMBED_DIR)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
            st.session_state.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=chat_model,
                retriever=retriever,
                return_source_documents=False
            )

    st.markdown("### ❓ Ask a Question")
    user_question = st.text_input("💬 Type your question here")

    if user_question:
        long_form_instruction = (
            "Please provide a long, detailed, and clearly structured explanation. "
            "Use simple language, include context, and break down complex terms. "
            "Imagine you are teaching this to someone new to the topic."
        )

        chat_history = st.session_state.chat_history or []
        file_names = [os.path.basename(p) for p in st.session_state.selected_pdfs]
        file_context = f"Filename(s): {', '.join(file_names)}"

        with st.spinner("Generating answer..."):
            try:
                question_prompt = (
                    f"{long_form_instruction}\n\n"
                    f"Based on this paper: {file_context}\n\n"
                    f"Question: {user_question.strip()}"
                )
                response = st.session_state.qa_chain.invoke({
                    "question": question_prompt,
                    "chat_history": chat_history
                })
                answer = response.get("answer", "").strip()

                if "i don't know" in answer.lower() or not answer:
                    raise ValueError("Fallback triggered")

            except:
                fallback_prompt = (
                    f"{long_form_instruction}\n\n"
                    f"The paper filename is: {file_names[0]}\n\n"
                    f"Question: {user_question.strip()}"
                )
                answer = chat_model.invoke(fallback_prompt).content.strip()

        st.session_state.chat_history.append((user_question, answer))
        st.markdown("#### 🧠 Answer")
        st.write(answer)

    # Summarization
    st.markdown("---")
    st.markdown("### 🧾 Summarize Paper(s)")
    summary_option = st.radio("Choose a summary type", ["Short Summary", "Detailed Summary", "Summary by Sections"], horizontal=True)

    if st.button("📝 Generate Summary"):
        all_text = "\n".join(preview_pdf(pdf) for pdf in st.session_state.selected_pdfs)

        summary_prompt_map = {
        "Short Summary": (
            "Write a short, crisp summary of the following academic paper. "
            "Keep it under 100 words and highlight only the core objective and conclusion."
        ),
        "Detailed Summary": (
            "Write a detailed, structured summary of the following academic paper. "
            "Include background, methodology, findings, and conclusion. Use clear paragraphs."
        ),
        "Summary by Sections": (
            "Break down the following research paper section by section. "
            "Include headings (like Introduction, Methodology, Results, etc.) and give a few sentences per section."
        )
    }

        prompt_intro = summary_prompt_map[summary_option]
        full_prompt = f"{prompt_intro}\n\n{all_text}"

        with st.spinner("Generating summary..."):
            response = chat_model.invoke(full_prompt)
            st.markdown("#### 📚 Summary")
            st.write(response.content if hasattr(response, "content") else response)

# --- Footer ---
st.markdown("---")
st.caption("🧠 Built with LangChain + Google Gemini + FAISS + Streamlit")
