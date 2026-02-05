i = 1
while i < 6:
  print(i)
  i += 1

i = 10
while i >= 1:
    print(i)
    i -= 1


n = int(input())
total = 0

while n > 0:
    total += n
    n -= 1

print(total)

s = input()
i = len(s) - 1

while i >= 0:
    print(s[i], end="")
    i -= 1


password = "1234"
user_input = ""

while user_input != password:
    user_input = input("Enter password: ")

print("Access granted")
