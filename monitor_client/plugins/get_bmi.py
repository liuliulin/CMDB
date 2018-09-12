

def get_bmi(weight, waist):
    a = waist * 0.74
    b = weight * 0.082 + 44.74
    return (a - b) / weight * 100


print(get_bmi(62, 80))
