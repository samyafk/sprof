# -*- coding: utf-8 -*
# python3
# Utils - Innovalie - LJK, sept 2019

import numpy as np
import unicodedata as ud
import os

# ------ Strings --------------------

def str_simplify(str):
    # normalize string : replace accents
    # lowercas
    # keep only alfanumeric caracters - except space. " "
    simp_str = ud.normalize('NFKD', str.lower()).encode('ascii', 'ignore').decode('utf-8')
    simp_str = "".join([ c if c.isalnum() else " " for c in simp_str ])
    return simp_str

def str_isin(pattern,str):
    # search if the simplified pattern is in the simplified str
    same=False
    if str_simplify(pattern) in str_simplify(str):
        same=True
    return same

def str_eq(pattern,str):
    # search if the simplified pattern is in the simplified str
    same=False
    if str_simplify(pattern) == str_simplify(str):
        same=True
    return same

# ------ utilitaire pour les classes --------------------

def print_obj_attr(instance):
        dict = vars(instance)
        # enlève les attributs de type tableaux numpy ("ndarray")
        #dict = {k:v for (k,v) in dict.items() if not isinstance(v,np.ndarray)}
        
        for (key,value) in dict.items():
            if not isinstance(value,np.ndarray):
                print(f"{key} : {value}")
            else:
                if value.size:
                    print(f"Premiere et dernière valeur de {key} : {value[0]} - {value[-1]}")
                else:
                    print(f"{key} : empty")

# ------ Calculs --------------------

def _lissage(V):
    """Effectue une opération de lissage. 
    En entrée, le tableau à lisser, en sortie le tabeau après un lissage
    La fonction de lissage utilisée :
        pour chaque indice i, (valeur à i-1 + 2*valeur à i + valeur à i+1)/4
    """
    n = len(V)

    # Cas limite : la permière et la dernière valeur du tableau
    #V_start = [(V[0]*2+V[1])/3,] 
    V_start = [V[0],] # pour le début, il ne faut pas atténuer
    V_end = [(V[n-1]*2+V[n-2])/3,] # en revanche pour la fin, si
    #V_end = [V[n-1],]
    V_middle = np.array([(V[i-1]+V[i]*2+V[i+1])/4 for i in range(1,n-1)])
    args = (V_start, V_middle, V_end)
    return np.concatenate( args )   
    
    '''
    # remarque perso : eq 
    box = np.array([1,2,1])/4
    self.V_smooth = np.convolve(self.V_smooth, box, mode='same')
    # sauf valeurs limite, début et fin (ça "décroche" bcp plus)
    '''
    
def lissage(V, n_iter=200):
    # cette fonction retourne une copie lissée du vecteur donné en parametre
    # valeur par défaut à 200 après tests
    i=0

    # on copie le vecteur, car il va être modifié
    V_smooth = np.copy(V)

    # une petite limite au cas où
    if (n_iter > 1000):
        n_iter=1000

    while (i < n_iter):
        V_smooth = _lissage(V_smooth)
        i = i+1
    
    return V_smooth

def sum_distances(V_mesure, V_model):
    """
    somme des carrés des écarts à la valeur du modèle (= fonction F) 
    """
    sum = 0
    n = len(V_mesure)
    if ( n != len(V_model) ):
        print("Somme des carrés à la distance : attention, les vecteurs ne sont pas de la même taille")
    else:
        # puis on calcule la somme des carrés des différence au modèle
        for i in range (0, n): 
            sum=sum+(V_mesure[i]-V_model[i])**2

    return sum

# from https://github.com/python/cpython/blob/3.7/Lib/bisect.py
def bisect_right(a, x, lo=0, hi=None):
    """Return the index where to insert item x in list a, assuming a is sorted.
    The return value i is such that all e in a[:i] have e <= x, and all e in
    a[i:] have e > x.  So if x already appears in the list, a.insert(x) will
    insert just after the rightmost x already there.
    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)//2
        if x < a[mid]: hi = mid
        else: lo = mid+1
    return lo-1

def bisect_left(a, x, lo=0, hi=None):
    """Return the index where to insert item x in list a, assuming a is sorted.
    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(x) will
    insert just before the leftmost x already there.
    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)//2
        if a[mid] < x: lo = mid+1
        else: hi = mid
    return lo-1
    
def get_inext(array,i_start,ratio): # ratio : accepted gap or end of the array
    """ Returns the first index found for array value > value, after the i_start point
        suppose array is a king of time series
    """
    value = array[i_start]
    diff = value*ratio
    i=i_start
    imax=len(array) - 1
    
    while ( abs(array[i]-value) < diff and i < imax):
        i+=1
    return i
   
def get_iprevious(array,i_start,ratio): # ratio : accepted gap
    """ Returns the first index found for array value > value, after the i_start point
        suppose array is a kinf of  time series
    """
    value = array[i_start]
    diff = value*ratio
    i=i_start
    
    #for i in range(i_start-1,0,-1):
    #    if abs(array[i]-initial_value) > diff:
    #        return i
    while ( abs(array[i]-value) < diff and i > 0):
        i-=1         
    return i  