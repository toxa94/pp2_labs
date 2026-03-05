import re

# (?<!^)    -> negative lookbehind (not start of string)
# ([A-Z])   -> uppercase letter
pattern = r"(?<!^)([A-Z])"

text = input("Enter text: ")

# add space before each capital letter
result = re.sub(pattern, r" \1", text)

print(result)