import os

KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")

def list_companies() -> list:
    """Return company names derived from .txt filenames in knowledge_base/."""
    if not os.path.exists(KB_DIR):
        return []
    companies = []
    for f in sorted(os.listdir(KB_DIR)):
        if f.endswith(".txt"):
            companies.append(os.path.splitext(f)[0])  # e.g. "Accenture"
    return companies


def get_company_kb(company_name: str) -> str:
    """Return the full text content for the given company name."""
    filepath = os.path.join(KB_DIR, f"{company_name}.txt")
    if not os.path.exists(filepath):
        return f"No knowledge base found for {company_name}."
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
