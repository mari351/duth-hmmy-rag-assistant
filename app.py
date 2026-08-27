import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
import chromadb

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="university_docs")


def ask_question(question, top_k=4):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=question
    )
    question_embedding = result.embeddings[0].values

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )

    retrieved_chunks = results["documents"][0]
    sources = results["metadatas"][0]
    context = "\n\n---\n\n".join(retrieved_chunks)

    prompt = f"""Είσαι ένας βοηθητικός assistant για φοιτητές του Τμήματος ΗΜ&ΜΥ.
Απάντησε στην ερώτηση με φυσικό, συνομιλητικό ύφος, σαν να εξηγείς σε συμφοιτητή.
Χρησιμοποίησε το παρακάτω context ως πηγή πληροφοριών, αλλά διατύπωσε την απάντηση με τα δικά σου λόγια.
Αν η απάντηση δεν υπάρχει στο context, πες καθαρά ότι δεν έχεις αυτή την πληροφορία - μην μαντεύεις.

Context:
{context}

Ερώτηση: {question}

Απάντηση:"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    unique_sources = set(s["source_document"] for s in sources)
    return response.text, unique_sources


# --- Streamlit UI ---
st.markdown("""
<h1 style='text-align: center; font-size: 48px; font-weight: 900;
           color: #4FD1C5; font-family: "Trebuchet MS", sans-serif;
           text-shadow: 4px 4px 8px rgba(0,0,0,0.3);'>
    ΔΠΘ ΗΜΜΥ Assistant
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@keyframes typing {
    from { width: 0; }
    to { width: 100%; }
}
@keyframes blink {
    50% { border-color: transparent; }
}
.typewriter {
    display: inline-block;
    overflow: hidden;
    white-space: nowrap;
    border-right: 3px solid #4FD1C5;
    font-size: 18px;
    color: #A0AEC0;
    font-style: italic;
    animation: typing 3.5s steps(60, end), blink 0.75s step-end infinite;
}
</style>
<div style='text-align: center;'>
    <span class="typewriter">Ρώτα με για κανονισμούς, πρόγραμμα σπουδών, Erasmus, πρακτική άσκηση</span>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
st.markdown("""
<style>
[data-testid="stChatInput"] {
    background-color: #4FD1C5;
    border-radius: 4px;
    border: 2px solid #4FD1C5;
}
[data-testid="stChatInput"] textarea {
    background-color: #4FD1C5;
    color: white;
    border-radius: 4px;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #E6FFFA;
}
[data-testid="stChatInputSubmitButton"] {
    background-color: #38B2AC;
    border-radius: 4px;
}
[data-testid="stChatInputSubmitButton"] svg {
    fill: white;
}
</style>
""", unsafe_allow_html=True)
question = st.chat_input("Γράψε την ερώτησή σου εδώ...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Ψάχνω..."):
            answer, sources = ask_question(question)
            st.markdown(answer)
            st.caption(f"Πηγές: {', '.join(sources)}")

    st.session_state.messages.append({"role": "assistant", "content": answer})