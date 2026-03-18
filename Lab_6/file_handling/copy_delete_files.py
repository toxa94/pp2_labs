# Example: Copy and delete file

import shutil
import os

# Copy file
shutil.copy("sample.txt", "backup.txt")
print("File copied")

# Delete file
if os.path.exists("backup.txt"):
    os.remove("backup.txt")
    print("Backup file deleted")