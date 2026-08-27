import os
import json


def split_into_blocks(text):
    """Χωρίζει το κείμενο σε blocks, όπου κάθε συνεχόμενη ομάδα
    γραμμών-πίνακα (που ξεκινούν με |) μένει μαζί σε ένα block,
    αγνοώντας κενές γραμμές ανάμεσά τους."""
    lines = text.split("\n")
    blocks = []
    current_block = []
    current_is_table = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            current_block.append(line)
            continue

        line_is_table = stripped.startswith("|")

        if current_block and line_is_table != current_is_table:
            blocks.append("\n".join(current_block))
            current_block = []

        current_block.append(line)
        current_is_table = line_is_table

    if current_block:
        blocks.append("\n".join(current_block))

    return blocks


def is_marker_line(line):
    """Ελέγχει αν μια γραμμή είναι markdown heading ή ετικέτα σελίδας -
    δηλαδή κάτι που πρέπει να 'κολλήσει' με το block που ακολουθεί,
    αντί να μείνει μόνο του σαν ορφανό mini-chunk."""
    stripped = line.strip().lstrip("\\")
    if stripped.startswith("#"):
        return True
    if stripped.startswith("--- Σελίδα") and stripped.endswith("---"):
        return True
    return False


def extract_trailing_heading(text_block):
    """Αν η τελευταία (μη-κενή) γραμμή ενός text block είναι heading
    ή ετικέτα σελίδας, το χωρίζει: επιστρέφει (υπόλοιπο κείμενο, marker).
    Αλλιώς επιστρέφει (block, None)."""
    lines = text_block.split("\n")

    last_non_empty_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            last_non_empty_idx = i
            break

    if last_non_empty_idx is None:
        return text_block, None

    last_line = lines[last_non_empty_idx]
    if is_marker_line(last_line):
        remaining = "\n".join(lines[:last_non_empty_idx]).strip()
        return remaining, last_line.strip()

    return text_block, None


def chunk_text_blocks(text_blocks, target_words=400, overlap_words=50):
    """Παίρνει μια λίστα από text blocks (καθαρό κείμενο, όχι πίνακες)
    και τα ενώνει σε chunks περίπου target_words λέξεων, με overlap."""
    full_text = "\n\n".join(text_blocks)
    words = full_text.split()

    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + target_words
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start = end - overlap_words

    return chunks


def build_chunks(blocks):
    """Παίρνει τη λίστα από blocks (πίνακες + κείμενο) και φτιάχνει τα τελικά chunks,
    κολλώντας τυχόν headings/ετικέτες σελίδας μαζί με το block που ακολουθεί."""
    final_chunks = []
    pending_text_blocks = []
    pending_heading = None

    def flush_pending_text():
        if pending_text_blocks:
            text_chunks = chunk_text_blocks(pending_text_blocks)
            final_chunks.extend(text_chunks)
            pending_text_blocks.clear()

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        is_table = block.startswith("|")

        if is_table:
            flush_pending_text()
            if pending_heading:
                final_chunks.append(pending_heading + "\n\n" + block)
                pending_heading = None
            else:
                final_chunks.append(block)
        else:
            remaining_text, trailing_heading = extract_trailing_heading(block)

            if remaining_text:
                if pending_heading:
                    pending_text_blocks.append(pending_heading)
                    pending_heading = None
                pending_text_blocks.append(remaining_text)

            if trailing_heading:
                flush_pending_text()
                pending_heading = trailing_heading

    if pending_heading:
        pending_text_blocks.append(pending_heading)
    flush_pending_text()

    return final_chunks


def chunk_document(text):
    """Το πλήρες pipeline: κείμενο PDF -> λίστα τελικών chunks."""
    blocks = split_into_blocks(text)
    return build_chunks(blocks)


# --- Επεξεργαζόμαστε ΟΛΑ τα εξαγμένα .txt αρχεία ---
extracted_folder = "extracted"
all_chunks = []  # θα κρατήσει dictionaries με metadata + κείμενο

for filename in os.listdir(extracted_folder):
    if not filename.endswith(".txt"):
        continue

    filepath = os.path.join(extracted_folder, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_document(text)

    print(f"{filename}: {len(chunks)} chunks")

    for i, chunk_text in enumerate(chunks):
        all_chunks.append({
            "source_document": filename,
            "chunk_index": i,
            "text": chunk_text,
            "word_count": len(chunk_text.split())
        })

print(f"\nΣυνολικά chunks από όλα τα documents: {len(all_chunks)}")

# Αποθηκεύουμε όλα τα chunks σε ένα αρχείο JSON, για επόμενο βήμα (embeddings)
with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, ensure_ascii=False, indent=2)

print("Τα chunks αποθηκεύτηκαν στο chunks.json")