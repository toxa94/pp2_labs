import re

# b{2,3} -> 'b' must appear at least 2 times and at most 3 times
pattern = r"^ab{2,3}$"

text = input("Enter string: ")

if re.match(pattern, text):
    print("Match found")
else:
    print("No match")