# Example: Move / copy files between directories

import shutil

# Copy sample file to folder1
shutil.copy("sample.txt", "folder1/sample.txt")

print("File moved to folder1")