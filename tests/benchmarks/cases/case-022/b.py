def normalize_text(s: str) -> str:
    # order changed slightly
    s = s.strip()
    s = s.replace("\t", " ")
    return s.lower()

