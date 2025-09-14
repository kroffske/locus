def is_palindrome(s: str) -> bool:
    t = s.lower()  # same logic
    return t == t[::-1]

