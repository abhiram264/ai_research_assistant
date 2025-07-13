
# 🤖 AI-Powered Research Assistant

Welcome to your **AI Research Assistant**, a tool designed to streamline your academic workflow using **Google Gemini**, **LangChain**, **FAISS**, and **Streamlit**.

![Made with Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-blueviolet?style=for-the-badge&logo=streamlit)
![Powered by LangChain](https://img.shields.io/badge/Powered%20by-LangChain-blue?style=for-the-badge)
![Gemini Model](https://img.shields.io/badge/Model-Google%20Gemini-ffce44?style=for-the-badge)

---

## 🚀 Features

- 📄 Upload or search academic PDFs from **ArXiv**
- 🤖 Ask questions and get answers with **context-aware AI**
- 🧠 Choose response style: Concise, Detailed, Layman Explanation
- 📚 Summarize papers (short, detailed, or section-wise)
- 🔍 Auto-clears FAISS index on every session for clean usage
- 🌐 Streamlit-hosted PDF viewer (Firefox inline + Chrome-friendly download)


---

## 🧰 Tech Stack

| Technology | Purpose                     |
|------------|-----------------------------|
| Streamlit  | Web interface               |
| FAISS      | Vector database             |
| LangChain  | LLM orchestration           |
| Google Gemini | LLM backend (chat + embeddings) |
| ArXiv API  | Research paper search       |

---

## 🛠 Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/abhiram264/ai-research-assistant.git
cd ai-research-assistant
```

### 2. Create `.streamlit/secrets.toml`

```toml
GOOGLE_API_KEY = "your_google_gemini_api_key"
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run locally

```bash
streamlit run streamlit_app.py
```

---

## 🌍 Deploy on Streamlit Cloud

1. Push your project to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app and connect your GitHub repo
4. Add your `GOOGLE_API_KEY` under **Secrets**

---

## 📄 License

MIT License

---

## 🙏 Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [Google Gemini](https://deepmind.google)
- [Streamlit](https://streamlit.io/)
- [ArXiv](https://arxiv.org/)

---
