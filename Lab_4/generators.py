# 1. Generator that generates squares up to N
def square_generator(n):
    for i in range(n + 1):
        yield i * i


print("1. Squares up to N:")
for num in square_generator(5):
    print(num)
print()


# 2. Even numbers between 0 and n (comma separated)
def even_numbers(n):
    for i in range(n + 1):
        if i % 2 == 0:
            yield i


n = int(input("Enter n for even numbers: "))
print("2. Even numbers:")
print(", ".join(str(num) for num in even_numbers(n)))
print()


# 3. Numbers divisible by 3 and 4 in range 0 to n
def divisible_by_3_and_4(n):
    for i in range(n + 1):
        if i % 3 == 0 and i % 4 == 0:
            yield i


print("3. Divisible by 3 and 4:")
for num in divisible_by_3_and_4(50):
    print(num)
print()


# 4. Generator squares from a to b
def squares(a, b):
    for i in range(a, b + 1):
        yield i * i


print("4. Squares from a to b:")
for num in squares(3, 7):
    print(num)
print()


# 5. Numbers from n down to 0
def countdown(n):
    while n >= 0:
        yield n
        n -= 1


print("5. Countdown:")
for num in countdown(5):
    print(num)