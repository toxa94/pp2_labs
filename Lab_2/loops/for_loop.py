fruits = ["apple", "banana", "cherry"]
for x in fruits:
  print(x)

for x in "banana":
  print(x)

for i in range(1, 6):
    print(i)


for i in range(10):
    if i % 2 == 0:
        print(i)

n = int(input())
total = 0

for i in range(1, n + 1):
    total += i

print(total)

s = input()

for i in range(len(s) - 1, -1, -1):
    print(s[i], end="")


numbers = [3, 5, 7, 9]

for n in numbers:
    print(n)


#Using the range() function:
for x in range(6):
  print(x)

#Note that range(6) is not the values of 0 to 6, but the values 0 to 5.


#Print all numbers from 0 to 5, and print a message when the loop has ended:

for x in range(6):
  print(x)
else:
  print("Finally finished!")

#Break the loop when x is 3, and see what happens with the else block:
for x in range(6):
  if x == 3: break
  print(x)
else:
  print("Finally finished!")

#Nested Loops
adj = ["red", "big", "tasty"]
fruits = ["apple", "banana", "cherry"]

for x in adj:
  for y in fruits:
    print(x, y)

#The pass Statement
"""""for loops cannot be empty,
 but if you for some reason have a for loop with no content,
 put in the pass statement to avoid getting an error."""

for x in [0, 1, 2]:
  pass