# Instance method and self

class Student:
    def __init__(self, name):
        self.name = name

    def greet(self):
        print(f"Hello, my name is {self.name}")

student = Student("Toktar")
student.greet()