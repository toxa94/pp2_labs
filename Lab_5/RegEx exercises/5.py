import re

# a    -> must start with 'a'
# .*   -> any characters (zero or more)
# b    -> must end with 'b'
pattern = r"^a.*b$"

text = input("Enter string: ")

if re.match(pattern, text):
    print("Match found")
else:
    print("No match")