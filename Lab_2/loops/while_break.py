i = 1
while i < 6:
  print(i)
  if i == 3:
    break
  i += 1

while True:
    x = int(input())
    if x > 0:
        break

print("Positive number entered")

s = input()
i = 0

while i < len(s):
    if s[i] == "a":
        break
    print(s[i])
    i += 1

password = "1234"

while True:
    p = input()
    if p == password:
        break

print("Access granted")

while True:
    n = int(input())
    if n == 0:
        break
    print(n)