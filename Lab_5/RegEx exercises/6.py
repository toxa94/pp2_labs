import re

# [ ,.]  -> matches space OR comma OR dot
pattern = r"[ ,.]"

text = input("Enter text: ")

# re.sub replaces all matches with ":"
result = re.sub(pattern, ":", text)

print(result)