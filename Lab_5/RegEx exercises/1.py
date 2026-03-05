import re

# ^  -> start of string
# a  -> letter 'a'
# b* -> zero or more 'b'
# $  -> end of string
pattern = r"^ab*$"

text = input("Enter string: ")

if re.match(pattern, text):
    print("Match found")
else:
    print("No match")