# Read and print file contents

with open("sample.txt", "r") as f:
    content = f.read()
    print("File content:")
    print(content)