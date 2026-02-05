fruits = ["apple", "banana", "cherry"]
for x in fruits:
  print(x)
  if x == "banana":
    break
  
fruits = ["apple", "banana", "cherry"]
for x in fruits:
  if x == "banana":
    break
  print(x)

for i in range(1, 10):
    if i == 5:
        break
    print(i)

text = input()


password = "1234"

for _ in range(3):
    p = input()
    if p == password:
        break

print("Done")

nums = [1, 3, 5, 7, 9]

for n in nums:
    if n == 5:
        break
    print(n)