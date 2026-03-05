import re

# [A-Z]   -> exactly one uppercase letter
# [a-z]+  -> one or more lowercase letters
pattern = r"\b[A-Z][a-z]+\b"

text = input("Enter text: ")

matches = re.findall(pattern, text)
print(matches)