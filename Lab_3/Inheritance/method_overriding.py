# Method override

class Person:
    def speak(self):
        print("I am talking")

class Student(Person):
    def speak(self):
        print("I am a student and I am speaking.")

s = Student()
s.speak()