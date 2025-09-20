def is_palindrome(s: str) -> bool:
    t = s.lower()
    return t == t[::-1]
