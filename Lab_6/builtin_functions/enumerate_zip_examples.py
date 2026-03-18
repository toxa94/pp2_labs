# Example: enumerate and zip

names = ["Ali", "Dana", "Aruzhan"]
scores = [85, 90, 88]

# enumerate
print("Enumerate example:")
for i, name in enumerate(names):
    print(i, name)

# zip
print("Zip example:")
for name, score in zip(names, scores):
    print(name, score)