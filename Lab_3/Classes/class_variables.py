# Class variable vs Instance variable

class Student:
    school = "KBTU"  # class variable

    def __init__(self, name):
        self.name = name  # instance variable

s1 = Student("Toktar")
s2 = Student("Rinat")

print(s1.school)
print(s2.school)