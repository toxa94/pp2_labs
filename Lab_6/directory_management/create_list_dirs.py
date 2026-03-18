# Example: Create directories and list files

import os

# Create nested directories
os.makedirs("folder1/folder2", exist_ok=True)

# List files and folders
files = os.listdir(".")
print("Files in current directory:")
print(files)