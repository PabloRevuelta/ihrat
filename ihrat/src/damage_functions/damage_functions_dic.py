def pop_A(imp_val):
    if imp_val<0.3:
        return 0
    else:
        return 1
def pop_B(imp_val):
    if imp_val < 0.5:
        return 0
    else:
        return 1
def build_A(imp_val):
    if imp_val > 3:
        return 1
    else:
        return 0.33*imp_val
def build_B(imp_val):
    if imp_val > 6:
        return 1
    else:
        return 0.17*imp_val
def build_C(imp_val):
    if imp_val > 9:
        return 1
    else:
        return 0.11*imp_val
