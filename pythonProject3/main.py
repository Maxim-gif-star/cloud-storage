# Комбинаторика
import math
import scipy.special as sc
import itertools
# Сочетания: С(k, n) = (n!)/(k!(n-k)!)

print(sc.comb(3, 2))

# Размещения: A(k, n) = (n!)/(n-k)!

print(sc.perm(3, 2))

# Число сочетаний с повторениями:  