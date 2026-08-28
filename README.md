# DUTH ECE Assistant

A **RAG-based (Retrieval-Augmented Generation) AI assistant** that answers questions over real documents from the Department of Electrical \& Computer Engineering (ECE) at the Democritus University of Thrace (DUTH) such as academic regulations, curriculum, Erasmus mobility, internships, and thesis guidelines.

This project was built to understand, hands-on and step by step, how a full RAG pipeline actually works: from extracting text out of heterogeneous PDFs, to retrieval and answer generation.

**Live demo:** available on request



## HOW IT WORKS ?

Ask something like *"How many ECTS do I need to graduate?"* or *"What are the scoring criteria for Erasmus?"*, and the assistant will:

1. Convert the question into an embedding
2. Search semantically across the stored documents
3. Retrieve the most relevant passages
4. Answer in natural language, grounded strictly in those passages — and explicitly say when the information isn't available, instead of guessing

## Architecture

```
PDF documents
     │
     ▼
Text extraction (pdfplumber)
  ├─ Auto-detects tables → converts to Markdown tables
  ├─ Manual overrides for pages with merged cells
  └─ Excludes pages with broken font encoding
     │
     ▼
Chunking
  ├─ Table protection (tables are never split mid-row)
  ├─ Headings get attached to the table/text block that follows
  └─ Text chunks \~400 words, with 50-word overlap
     │
     ▼
Embeddings (Gemini gemini-embedding-001)
     │
     ▼
Vector storage (ChromaDB, persistent local)
     │
     ▼
Query pipeline: question → embedding → similarity search →
                top-k context → prompt to Gemini → answer
     │
     ▼
Streamlit chat UI


\---

## Tech stack

|Layer|Tool|
|-|-|
|LLM \& Embeddings|Google Gemini API (`gemini-3.6-flash`, `gemini-embedding-001`)|
|PDF parsing|`pdfplumber`|
|Vector database|`ChromaDB`|
|Frontend|`Streamlit`|
|Language|Python|



## Running locally

```bash
git clone https://github.com/mari351/duth-hmmy-rag-assistant.git
cd duth-hmmy-rag-assistant
pip install -r requirements.txt
```

Create a `.env` file with:

```
GEMINI\_API\_KEY=your-key-here
```

```bash
python explore\_pdf.py       # PDF -> clean text
python chunking.py          # text -> chunks
python embed\_and\_store.py   # chunks -> embeddings -> ChromaDB
streamlit run app.py        # launch the chat UI
```

\---

## Screenshots of the Demo:


!\[](screenshots/one.png)

!\[](screenshots/two.png)

!\[](screenshots/three.png)

