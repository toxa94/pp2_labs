import re

# [A-Z]     -> uppercase letter
# [^A-Z]*   -> zero or more characters that are NOT uppercase
pattern = r"[A-Z][^A-Z]*"

text = input("Enter camelCase string: ")

result = re.findall(pattern, text)

print(result)