import numpy as np

def apply_damage_fun(indiv_element_dic,dmfunkey,dmfrackey,impvalkey):
    #Compute tha damage fraction on the exposed value of a given element of the exposed system and add it to the dic
    dam_fun=globals().get(indiv_element_dic[dmfunkey])
    indiv_element_dic[dmfrackey]=round(dam_fun(indiv_element_dic[impvalkey]), 3)

def apply_dam_fun_raster(raster_scen_data,mask_scen,damfun):
    dam_fun = globals().get(damfun)
    dam_fun_vec=np.vectorize(dam_fun)
    raster_scen_data[mask_scen] = dam_fun_vec(raster_scen_data[mask_scen])

    return raster_scen_data

def pop_A(imp_val):
    #print(imp_val)
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