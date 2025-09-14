import streamlit as st
import wikipedia
from PyPDF2 import PdfReader
import os
import re

# ---------------------------
# Load Abbreviations from PDF
# ---------------------------
def load_abbreviations(pdf_path="abbreviations.pdf"):
    abbr_dict = {}
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        for line in text.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                abbr_dict[key.strip().upper()] = val.strip()
    except FileNotFoundError:
        st.warning(f"Abbreviations PDF not found at '{pdf_path}'. Continuing without abbreviations.")
    except Exception as e:
        st.warning(f"Error loading abbreviations: {e}")
    return abbr_dict

ABBREVIATIONS = load_abbreviations()

# ---------------------------
# Expand abbreviations in question
# ---------------------------
def expand_question(q):
    tokens = q.split()
    expanded_tokens = []
    for t in tokens:
        m = re.match(r"^(\W*)([\w\-]+)(\W*)$", t, flags=re.UNICODE)
        if m:
            pre, core, post = m.groups()
            key = core.upper()
            if key in ABBREVIATIONS:
                core = ABBREVIATIONS[key]
            expanded_tokens.append(pre + core + post)
        else:
            core = re.sub(r'^\W+|\W+$', '', t)
            key = core.upper()
            if key in ABBREVIATIONS:
                expanded_tokens.append(t.replace(core, ABBREVIATIONS[key]))
            else:
                expanded_tokens.append(t)
    return " ".join(expanded_tokens)

# ---------------------------
# Get Wikipedia answer
# ---------------------------
def get_answer(question):
    if not question or str(question).strip() == "":
        return "⚠️ Please enter a question."
    try:
        expanded_q = expand_question(question)
        search_results = wikipedia.search(expanded_q, results=5)
        if not search_results:
            search_results = wikipedia.search(question, results=5)

        if not search_results:
            return f"⚠️ No Wikipedia results found for '{question}'. Try rephrasing."

        candidate_title = search_results[0]
        try:
            summary = wikipedia.summary(candidate_title, sentences=5, auto_suggest=False)
            return summary
        except wikipedia.exceptions.DisambiguationError as de:
            options = de.options
            return f"⚠️ Ambiguous topic. Try one of these: {options[:5]}"
        except Exception:
            return f"⚠️ Could not fetch a Wikipedia page for '{question}'."
    except Exception as e:
        return f"⚠️ Unexpected error: {e}"

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="🤖 Chatbot", layout="wide")

# Sidebar
st.sidebar.title("📌 Menu")
option = st.sidebar.radio("Choose an option:", ["New Chat", "History"])

# Session state
if "history" not in st.session_state:
    st.session_state.history = []

if option == "New Chat":
    st.session_state.history = []
    st.sidebar.success("🆕 Started a new chat!")

# Heading
st.markdown("<h1 style='text-align:center;'>🤖 Chatbot</h1>", unsafe_allow_html=True)

# Search bar
user_input = st.text_input("Ask your question:")

# File upload (optional)
uploaded_file = st.file_uploader("📂 Upload PDF (optional)", type=["pdf"])
if uploaded_file:
    st.success(f"✅ Uploaded: {uploaded_file.name}")

# Save & Download buttons (side by side)
col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Save"):
        st.success("✅ Saved (demo only)")
with col2:
    if st.session_state.history:
        content = ""
        for q, a in st.session_state.history:
            content += f"Q: {q}\nA: {a}\n\n"
        st.download_button("⬇️ Download chat", data=content.encode("utf-8"),
                           file_name="chat_history.txt")
    else:
        st.button("⬇️ Download", disabled=True)

# Answer processing
if user_input:
    answer = get_answer(user_input)
    st.write(f"**You asked:** {user_input}")
    st.write(f"**Bot (detailed):** {answer}")
    st.session_state.history.append((user_input, answer))

# History in sidebar
if option == "History":
    st.sidebar.subheader("📜 Chat History")
    if not st.session_state.history:
        st.sidebar.info("No history yet. Ask something first.")
    for idx, (q, a) in enumerate(st.session_state.history):
        with st.sidebar.expander(f"Q{idx+1}: {q}"):
            st.write(a)
