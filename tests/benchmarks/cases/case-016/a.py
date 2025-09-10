def count_vowels(s: str) -> int:
    vowels = set("aeiou")
    c = 0
    for ch in s.lower():
        if ch in vowels:
            c += 1
    return c

