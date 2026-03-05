import re

def camel_to_snake(text):
    # ([A-Z]) -> find uppercase letter
    # _\1     -> add underscore before it
    # .lower() -> convert entire string to lowercase
    return re.sub(r"([A-Z])", r"_\1", text).lower()

text = input("Enter camelCase string: ")

print(camel_to_snake(text))