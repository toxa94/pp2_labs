import math

# 1. Convert degree to radian
degree = float(input("Input degree: "))
radian = math.radians(degree)
print("Output radian:", round(radian, 6))
print()


# 2. Area of a trapezoid
height = float(input("Height: "))
base1 = float(input("Base, first value: "))
base2 = float(input("Base, second value: "))

area_trapezoid = (base1 + base2) / 2 * height
print("Expected Output:", area_trapezoid)
print()


# 3. Area of regular polygon
n = int(input("Input number of sides: "))
length = float(input("Input the length of a side: "))

area_polygon = (n * length ** 2) / (4 * math.tan(math.pi / n))
print("The area of the polygon is:", int(area_polygon))
print()


# 4. Area of parallelogram
base = float(input("Length of base: "))
height_par = float(input("Height of parallelogram: "))

area_parallelogram = base * height_par
print("Expected Output:", area_parallelogram)