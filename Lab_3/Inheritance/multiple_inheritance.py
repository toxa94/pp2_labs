# Multiple inheritance

class Athlete:
    def train(self):
        print("Exercising")

class Student:
    def study(self):
        print("Studying")

class SportsStudent(Athlete, Student):
    pass

ss = SportsStudent()
ss.train()
ss.study()