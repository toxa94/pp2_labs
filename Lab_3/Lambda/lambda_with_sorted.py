# sorted() + lambda

students = [
    ("Toktar", 90),
    ("Rinat", 85),
    ("Magzhan", 95)
]

# Sort by score
sorted_students = sorted(students, key=lambda x: x[1])
print(sorted_students)