# Create a file and write data

with open("sample.txt", "w") as f:
    f.write("Hello\n")
    f.write("Python file handling practice\n")

# Append new data

with open("sample.txt", "a") as f:
    f.write("New line added\n")