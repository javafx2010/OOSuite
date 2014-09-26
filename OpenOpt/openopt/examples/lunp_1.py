from __future__ import print_function
from future.builtins import range
__docformat__ = "restructuredtext en"

from numpy import *
from openopt import LUNP

M, N = 1500, 150
C = empty((M,N))
d =  empty(M)

for j in range(M):
    d[j] = 1.5*N+80*sin(j)
    C[j] = 8*sin(4.0+arange(N)) + 15*cos(j)

lb = sin(arange(N))
ub = lb + 1
p = LUNP(C, d, lb=lb, ub=ub)

r = p.solve('lp:glpk', iprint = -1)

print('f_opt:', r.ff)
#print 'x_opt:', r.xf

