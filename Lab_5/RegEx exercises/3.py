import re

# \b        -> word boundary
# [a-z]+    -> one or more lowercase letters
# _         -> underscore
# [a-z]+    -> one or more lowercase letters
# \b        -> word boundary
pattern = r"\b[a-z]+_[a-z]+\b"

text = input("Enter text: ")

matches = re.findall(pattern, text)
print(matches)