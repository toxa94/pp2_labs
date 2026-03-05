import re

def snake_to_camel(text):
    # _([a-z])  -> underscore followed by lowercase letter
    # group(1)  -> letter after underscore
    # lambda    -> convert that letter to uppercase
    return re.sub(r"_([a-z])", lambda x: x.group(1).upper(), text)

text = input("Enter snake_case string: ")

print(snake_to_camel(text))