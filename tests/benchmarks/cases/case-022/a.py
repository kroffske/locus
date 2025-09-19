def normalize_text(s: str) -> str:
    s = s.replace("\t", " ")
    s = s.strip()
    return s.lower()
