import pdfplumber
import os


def table_to_markdown(table):
    """Μετατρέπει έναν πίνακα (λίστα από λίστες) σε markdown table string."""
    if not table or len(table) < 2:
        return ""

    headers = table[0]
    rows = table[1:]

    def clean(cell):
        if cell is None:
            return ""
        return str(cell).replace("\n", " ").strip()

    headers = [clean(h) for h in headers]

    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for row in rows:
        cleaned_row = [clean(cell) for cell in row]
        if any(cleaned_row):
            md += "| " + " | ".join(cleaned_row) + " |\n"

    return md


def extract_pdf_content(pdf_path, page_overrides=None, excluded_pages=None):
    """Διατρέχει όλο το PDF και επιστρέφει το πλήρες κείμενο.

    page_overrides: dict {αριθμός_σελίδας: path_αρχείου_fix}
    excluded_pages: λίστα με αριθμούς σελίδων που πρέπει να παραλειφθούν εντελώς
    """
    if page_overrides is None:
        page_overrides = {}
    if excluded_pages is None:
        excluded_pages = []

    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_number = i + 1

            # Αν η σελίδα είναι στη λίστα εξαίρεσης, την προσπερνάμε τελείως
            if page_number in excluded_pages:
                continue

            page_content = f"\n--- Σελίδα {page_number} ---\n"

            if page_number in page_overrides:
                # Χρησιμοποιούμε το χειροκίνητο fix αντί για αυτόματο extraction
                fix_path = page_overrides[page_number]
                with open(fix_path, "r", encoding="utf-8") as f:
                    page_content += f.read()
            else:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        page_content += table_to_markdown(table)
                else:
                    text = page.extract_text()
                    if text:
                        page_content += text

            full_text += page_content

    return full_text


# --- Κεντρικό μητρώο: overrides ανά PDF (για δύσκολους πίνακες) ---
ALL_OVERRIDES = {
    "Π3.1_ΤHMMY_Κανονισμός-Κινητικότητας-Erasmus.pdf": {
        4: "documents/erasmus_moriodotisi_fix.md"
    }
}

# --- Κεντρικό μητρώο: εξαιρούμενες σελίδες ανά PDF ---
EXCLUDED_PAGES = {
    "Εσωτερικός-Κανονισμός-Λειτουργίας-ΤΗΜ_ΜΥ.pdf":
        [35, 36, 37, 38, 39] + list(range(52, 70)) + list(range(76, 83))
}


# --- Διατρέχουμε ΟΛΑ τα PDF στον φάκελο documents/ ---
documents_folder = "documents"
all_documents = {}  # {όνομα_αρχείου: εξαγμένο_κείμενο}

for filename in os.listdir(documents_folder):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(documents_folder, filename)
        overrides = ALL_OVERRIDES.get(filename, {})
        excluded = EXCLUDED_PAGES.get(filename, [])

        print(f"Επεξεργασία: {filename}...")
        text = extract_pdf_content(pdf_path, page_overrides=overrides, excluded_pages=excluded)
        all_documents[filename] = text
        print(f"  → {len(text)} χαρακτήρες εξήχθησαν\n")

print(f"\nΣυνολικά επεξεργάστηκαν {len(all_documents)} PDF")

# Αποθηκεύουμε το καθένα σε ξεχωριστό .txt αρχείο, για έλεγχο
os.makedirs("extracted", exist_ok=True)
for filename, text in all_documents.items():
    output_name = filename.replace(".pdf", ".txt")
    output_path = os.path.join("extracted", output_name)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

print("Όλα τα αρχεία αποθηκεύτηκαν στον φάκελο 'extracted/'")