def vowel_count(text: str) -> int:
    vs = set("aeiou")
    n = 0
    for c in text.lower():
        if c in vs:
            n += 1
    return n

