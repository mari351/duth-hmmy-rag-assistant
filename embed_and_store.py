import json
import os
import time
from google import genai
from dotenv import load_dotenv
import chromadb

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Φορτώθηκαν {len(chunks)} chunks προς επεξεργασία\n")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="university_docs")

# Παίρνουμε τα ids που ήδη υπάρχουν στη βάση, ώστε να μην τα ξανακάνουμε
existing_ids = set(collection.get()["ids"])
print(f"Ήδη υπάρχουν {len(existing_ids)} chunks στη ChromaDB, θα τα προσπεράσουμε\n")

for i, chunk in enumerate(chunks):
    chunk_id = f"chunk_{i}"

    if chunk_id in existing_ids:
        continue  # το έχουμε ήδη επεξεργαστεί, προσπερνάμε

    text = chunk["text"]

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    embedding = result.embeddings[0].values

    collection.add(
        ids=[chunk_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{
            "source_document": chunk["source_document"],
            "chunk_index": chunk["chunk_index"]
        }]
    )

    time.sleep(1)  # μικρή παύση, ώστε να μη χτυπάμε rate limit

    if (i + 1) % 10 == 0:
        print(f"Επεξεργάστηκαν {i + 1}/{len(chunks)} chunks...")

print(f"\nΌλα τα chunks αποθηκεύτηκαν στη ChromaDB!")