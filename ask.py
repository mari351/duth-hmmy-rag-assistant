import os
from google import genai
from dotenv import load_dotenv
import chromadb

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Συνδεόμαστε στην ΙΔΙΑ ChromaDB που φτιάξαμε πριν
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="university_docs")


def ask_question(question, top_k=4):
    # Βήμα 1: Μετατρέπουμε την ερώτηση σε embedding
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=question
    )
    question_embedding = result.embeddings[0].values

    # Βήμα 2: Similarity search στη ChromaDB - βρίσκουμε τα top_k πιο σχετικά chunks
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )

    retrieved_chunks = results["documents"][0]
    sources = results["metadatas"][0]

    # Βήμα 3: Φτιάχνουμε το context, ενώνοντας τα chunks
    context = "\n\n---\n\n".join(retrieved_chunks)

    # Βήμα 4: Φτιάχνουμε το πλήρες prompt
    prompt = f"""Απάντησε στην ερώτηση του χρήστη βασισμένος ΜΟΝΟ στο παρακάτω context.
Αν η απάντηση δεν υπάρχει στο context, πες καθαρά ότι δεν έχεις αυτή την πληροφορία - μην μαντεύεις.

Context:
{context}

Ερώτηση: {question}

Απάντηση:"""

    # Βήμα 5: Καλούμε το Gemini με το πλήρες prompt
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text, sources


# --- Interactive loop: ρωτάμε συνέχεια μέχρι να γράψει "exit" ---
print("Ρώτα οτιδήποτε για τους κανονισμούς/πρόγραμμα σπουδών (γράψε 'exit' για έξοδο)\n")

while True:
    question = input("Ερώτηση: ")
    if question.lower() == "exit":
        break

    answer, sources = ask_question(question)

    print(f"\nΑπάντηση: {answer}\n")
    print("Πηγές:", set(s["source_document"] for s in sources))
    print("-" * 50 + "\n")