i = 0
while i < 6:
  i += 1
  if i == 3:
    continue
  print(i)

i = 0
while i < 10:
    i += 1
    if i % 2 != 0:
        continue
    print(i)

s = input()

for ch in s:
    if ch == " ":
        continue
    print(ch)

while True:
    n = int(input())
    if n < 0:
        continue
    if n == 0:
        break
    print(n)

text = input()

for c in text:
    if c == "a":
        continue
    print(c, end="")