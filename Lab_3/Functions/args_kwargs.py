# Using *args and **kwargs

def show_scores(*scores):
    """Accepts any number of points"""
    print("Points:", scores)

def student_info(**info):
    """Accepts information such as name, age"""
    for key, value in info.items():
        print(f"{key}: {value}")

show_scores(90, 85, 88)
student_info(name="Toktar", age=18, city="Baikonur")