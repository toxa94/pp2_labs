fruits = ["apple", "banana", "cherry"]
for x in fruits:
  if x == "banana":
    continue
  print(x)

for i in range(1, 6):
    if i == 3:
        continue
    print(i)

for i in range(1, 11):
    if i % 2 != 0:
        continue
    print(i)

text = input()

for ch in text:
    if ch == " ":
        continue
    print(ch)

numbers = [3, -1, 5, -7, 8]

for n in numbers:
    if n < 0:
        continue
    print(n)

word = input()

for c in word:
    if c == "a":
        continue
    print(c, end="")