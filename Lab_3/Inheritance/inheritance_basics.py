# Parent class and child class

class Person:
    def speak(self):
        print("I am human")

class Student(Person):
    pass

s = Student()
s.speak()