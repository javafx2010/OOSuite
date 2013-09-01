from numpy import ndarray, asscalar, isscalar, inf, nan, searchsorted, logical_not, \
copy as Copy, logical_and, where, asarray, any, all, atleast_1d, vstack, logical_or, isfinite, array

import numpy as np
from FDmisc import FuncDesignerException, update_mul_inf_zero, update_negative_int_pow_inf_zero, \
update_div_zero
from FuncDesigner.multiarray import multiarray
from boundsurf import boundsurf, surf, devided_interval, split, boundsurf_join
from boundsurf2 import surf2, boundsurf2
from operator import truediv as td

try:
    from bottleneck import nanmin, nanmax
except ImportError:
    from numpy import nanmin, nanmax
    
class Interval:
    def __init__(self, l, u, definiteRange):
        if isinstance(l, ndarray) and l.size == 1: l = asscalar(l)
        if isinstance(u, ndarray) and u.size == 1: u = asscalar(u)
        self.lb, self.ub, self.definiteRange = l, u, definiteRange
    def __str__(self):
        return 'FuncDesigner interval with lower bound %s and upper bound %s' % (self.lb, self.ub)
    def __repr__(self):
        return str(self)


def ZeroCriticalPoints(lb_ub):
    arg_infinum, arg_supremum = lb_ub[0], lb_ub[1]
    if isscalar(arg_infinum):
        return [0.0] if arg_infinum < 0.0 < arg_supremum else []
    tmp = Copy(arg_infinum)
    #tmp[where(logical_and(arg_infinum < 0.0, arg_supremum > 0.0))] = 0.0
    tmp[atleast_1d(logical_and(arg_infinum < 0.0, arg_supremum > 0.0))] = 0.0
    return [tmp]

#def IntegerCriticalPoints(arg_infinum, arg_supremum):
#    # TODO: check it for rounding errors
#    return arange(ceil(arg_infinum), ceil(1.0+arg_supremum), dtype=float).tolist()


## TODO: split TrigonometryCriticalPoints into (pi/2) *(2k+1) and (pi/2) *(2k)
#def TrigonometryCriticalPoints(lb_ub):
#    arg_infinum, arg_supremum = lb_ub[0], lb_ub[1]
#    # returns points with coords n * pi/2, arg_infinum <= n * pi/2<= arg_supremum,n -array of integers
#    arrN = asarray(atleast_1d(floor(2 * arg_infinum / pi)), int)
#    Tmp = []
#    for i in range(1, 6):
#        th = (arrN+i)*pi/2
#        #ind = where(logical_and(arg_infinum < th,  th < arg_supremum))[0]
#        ind = logical_and(arg_infinum < th,  th < arg_supremum)
#        #if ind.size == 0: break
#        if not any(ind): break
#        tmp = atleast_1d(Copy(arg_infinum))
#        tmp[atleast_1d(ind)] = asarray((arrN[ind]+i)*pi/2, dtype = tmp.dtype)
#        Tmp.append(tmp)
#    return Tmp
#    # 6 instead of  5 for more safety, e.g. small numerical rounding effects
#    #return [i / 2.0 * pi for i in range(n1, amin((n1+6, n2))) if (arg_infinum < (i / 2.0) * pi <  arg_supremum)]

#def halph_pi_x_2k_plus_one_points(arg_infinum, arg_supremum):
#    n1 = asarray(floor(2 * arg_infinum / pi), int)
#    Tmp = []
#    for i in range(1, 7):
#        if i% 2: continue
#        ind = where(logical_and(arg_infinum < (n1+i)*pi/2,  (n1+i)*pi/2< arg_supremum))[0]
#        if ind.size == 0: break
#        tmp = arg_infinum.copy()
#        #assert (n1+i)*pi/2 < 6.3
#        tmp[ind] = (n1[ind]+i)*pi/2
#        Tmp.append(tmp)
#    #raise 0
#    return Tmp
#    

#cosh_deriv = lambda x: Diag(np.sinh(x))
def ZeroCriticalPointsInterval(inp, func):
    is_abs = func == np.abs
    is_cosh = func == np.cosh    
    assert is_abs or is_cosh
    def interval(domain, dtype): 
        
        # TODO:
        # ia_surf_level = 2
        ################
        
        lb_ub, definiteRange = inp._interval(domain, dtype, ia_surf_level = 2)
        if isinstance(lb_ub, boundsurf):
            if is_abs:
                return lb_ub.abs()
            elif is_cosh:
                return defaultIntervalEngine(lb_ub, func, np.sinh, np.nan, 1, 0.0, 1.0)
        
        lb, ub = lb_ub#[0], lb_ub[1]
        ind1, ind2 = lb < 0.0, ub > 0.0
        ind = logical_and(ind1, ind2)
        TMP = func(lb_ub)
        TMP.sort(axis=0)
        if any(ind):
            F0 = func(0.0)
            TMP[0, atleast_1d(logical_and(ind, TMP[0] > F0))] = F0
#            TMP[atleast_1d(logical_and(ind, t_max < F0))] = F0
        return TMP, definiteRange
    return interval

def nonnegative_interval(inp, func, deriv, domain, dtype, F0, shift = 0.0):
    is_arccosh = func == np.arccosh
    is_sqrt = func == np.sqrt
    is_log = func in (np.log, np.log2, np.log10, np.log1p)
    
    ##############################
    assert is_arccosh or is_sqrt or is_log, 'unimplemented yet'
    # check for monotonity is required, sort or reverse of t_min_max has to be performed for monotonity != +1
    ##############################
    
    lb_ub, definiteRange = inp._interval(domain, dtype, ia_surf_level = 2)
    
    isBoundSurf = isinstance(lb_ub, boundsurf)
    
    if isBoundSurf:
        if is_sqrt or is_log:
            r, definiteRange = defaultIntervalEngine(lb_ub, func, deriv, 
                                                     monotonity = 1, convexity = -1, feasLB = 0.0)
            return r, r.definiteRange
        elif is_arccosh:
            r, definiteRange = defaultIntervalEngine(lb_ub, func, deriv, 
                                                     monotonity = 1, convexity = -1, feasLB = 1.0)
            return r, r.definiteRange
        lb_ub_resolved = lb_ub.resolve()[0]
    else:
        lb_ub_resolved = lb_ub
            
    lb, ub = lb_ub_resolved#[0], lb_ub_resolved[1]
    th = shift # 0.0 + shift = shift
    ind = lb < th

    
    if any(ind):
        lb_ub_resolved = lb_ub_resolved.copy()
        lb_ub_resolved[0, logical_and(ind, ub >= th)] = th
        if definiteRange is not False:
            if type(definiteRange) != np.ndarray:
                definiteRange = np.empty_like(lb, bool)
                definiteRange.fill(True)
            definiteRange[ind] = False
    
    r = func(lb_ub_resolved)
    
    return r, definiteRange

def box_1_interval(inp, r, func, domain, dtype):
    assert func in (np.arcsin, np.arccos, np.arctanh)

    lb_ub, definiteRange = inp._interval(domain, dtype, ia_surf_level = 2)
    isBoundSurf = isinstance(lb_ub, boundsurf)

    if isBoundSurf:
        return devided_interval(inp, r, domain, dtype, feasLB = -1.0, feasUB = 1.0)

    lb_ub_resolved = lb_ub.resolve()[0] if isBoundSurf else lb_ub
    lb_ub_resolved, definiteRange = adjustBounds(lb_ub_resolved, definiteRange, -1.0, 1.0)
    t_min_max = func(lb_ub_resolved)
    if func == np.arccos:
        t_min_max = t_min_max[::-1]
        
    return t_min_max, definiteRange


def adjust_lx_WithDiscreteDomain(Lx, v):
    if v.domain is bool or v.domain is 'bool':
        Lx[Lx != 0] = 1
    else:
        d = v.domain 
        ind = searchsorted(d, Lx, 'left')
        ind2 = searchsorted(d, Lx, 'right')
        ind3 = where(ind!=ind2)[0]
        #Tmp = Lx[:, ind3].copy()
        Tmp = d[ind[ind3]]
        #if any(ind==d.size):print 'asdf'
        ind[ind==d.size] -= 1# Is it ever encountered?
    #    ind[ind==d.size-1] -= 1
        Lx[:] = d[ind]
        Lx[ind3] = asarray(Tmp, dtype=Lx.dtype)

        
def adjust_ux_WithDiscreteDomain(Ux, v):
    if v.domain is bool or v.domain is 'bool':
        Ux[Ux != 1] = 0
    else:
        d = v.domain 
        ind = searchsorted(d, Ux, 'left')
        ind2 = searchsorted(d, Ux, 'right')
        ind3 = where(ind!=ind2)[0]
        #Tmp = Ux[:, ind3].copy()
        Tmp = d[ind[ind3]]
        #ind[ind==d.size] -= 1
        ind[ind==0] = 1
        Ux[:] = d[ind-1]
        Ux[ind3] = asarray(Tmp, dtype=Ux.dtype)

def add_interval(self, other, domain, dtype):
    domain1, definiteRange1 = self._interval(domain, dtype, ia_surf_level = 2)
    #print domain1.resolve()
    domain2, definiteRange2 = other._interval(domain, dtype, ia_surf_level = 2)
    return domain1 + domain2, logical_and(definiteRange1, definiteRange2)

def add_const_interval(self, c, domain, dtype): 
    r, definiteRange = self._interval(domain, dtype, ia_surf_level = 2)
    return r + c, definiteRange

def neg_interval(self, domain, dtype):
    r, definiteRange = self._interval(domain, dtype, ia_surf_level = 2)
    if type(r) == ndarray:
        assert r.shape[0] == 2
        #return (-r[1], -r[0])
        return -np.flipud(r), definiteRange
    else:
        #assert type(r) == boundsurf
        return -r, definiteRange

def mul_interval(self, other, isOtherOOFun, Prod, domain, dtype):
    
    lb1_ub1, definiteRange = self._interval(domain, dtype, ia_surf_level = 2)

    if isOtherOOFun:
        lb2_ub2, definiteRange2 = other._interval(domain, dtype, ia_surf_level = 2)
        definiteRange = logical_and(definiteRange, definiteRange2)
    else:
        lb2_ub2 = other
        
    if type(lb2_ub2) in (boundsurf, boundsurf2) or type(lb1_ub1) in (boundsurf, boundsurf2):
        if type(lb2_ub2) in (boundsurf, boundsurf2) and type(lb1_ub1) in (boundsurf, boundsurf2):
            resolveSchedule = domain.resolveSchedule.get(Prod, ())
            r = lb1_ub1.__mul__(lb2_ub2, resolveSchedule)
        else:
            r = lb1_ub1 * lb2_ub2
        r.definiteRange = definiteRange
        return r, r.definiteRange
    elif isscalar(other) or (type(other) == ndarray and other.size == 1):
        r = lb1_ub1 * other if other >= 0 else lb1_ub1[::-1] * other
        return r, definiteRange
    
    lb1, ub1 = lb1_ub1
    lb2, ub2 = lb2_ub2 if isOtherOOFun else (other, other)
    
    firstPositive = all(lb1 >= 0)
    firstNegative = all(ub1 <= 0)
    secondPositive = all(lb2 >= 0)
    secondNegative = all(ub2 <= 0)
    if firstPositive and secondPositive:
        t= vstack((lb1 * lb2, ub1 * ub2))
    elif firstNegative and secondNegative:
        t = vstack((ub1 * ub2, lb1 * lb2))
    elif firstPositive and secondNegative:
        t = vstack((lb2 * ub1, lb1 * ub2))
    elif firstNegative and secondPositive:
        t = vstack((lb1 * ub2, lb2 * ub1))
        #t = vstack((lb1 * other, ub1 * other) if other >= 0 else (ub1 * other, lb1 * other))
    elif isOtherOOFun:
        t = vstack((lb1 * lb2, ub1 * lb2, lb1 * ub2, ub1 * ub2))# TODO: improve it
        t = vstack((nanmin(t, 0), nanmax(t, 0)))
    else:
        t = vstack((lb1 * other, ub1 * other))# TODO: improve it
        t.sort(axis=0)
        
    #assert isinstance(t_min, ndarray) and isinstance(t_max, ndarray), 'Please update numpy to more recent version'
    if isOtherOOFun:
        update_mul_inf_zero(lb1_ub1, lb2_ub2, t)
    
    return t, definiteRange


def div_interval(self, other, Div, domain, dtype):
    
    lb2_ub2, definiteRange2 = other._interval(domain, dtype, ia_surf_level = 2)

    secondIsBoundsurf = isinstance(lb2_ub2, boundsurf)
    
    lb1_ub1, definiteRange1 = self._interval(domain, dtype, ia_surf_level = 2)# if type(lb2_ub2)==ndarray else 1)
    firstIsBoundsurf = type(lb1_ub1) in (boundsurf, boundsurf2)
#    if type(lb1_ub1) == boundsurf2:
#        lb1_ub1 = lb1_ub1.to_linear()
    
    # TODO: mention in doc definiteRange result for 0 / 0
    definiteRange = logical_and(definiteRange1, definiteRange2)
    
    tmp = None
    if not firstIsBoundsurf and secondIsBoundsurf:
        # TODO: check handling zeros
        if not hasattr(other, '_inv'):
            other._inv = other ** -1 #1.0/other
#            other._inv.engine_convexity = other._inv.engine_monotonity = -1
        Tmp = pow_const_interval(other, other._inv, -1, domain, dtype)[0]
        if isinstance(Tmp, boundsurf):
            tmp = lb1_ub1 * Tmp#lb2_ub2 ** -1
    elif firstIsBoundsurf and not secondIsBoundsurf:# and (t1_positive or t1_negative or t2_positive or t2_negative):
        # TODO: handle zeros
        Tmp2 = 1.0 / lb2_ub2
        Tmp2.sort(axis=0)
        tmp = lb1_ub1 * Tmp2
        #tmp = lb1_ub1 * (1.0 / tmp2[::-1]) 
    elif firstIsBoundsurf and secondIsBoundsurf:
        tmp = lb1_ub1.__div__(lb2_ub2, domain.resolveSchedule.get(Div, ()))
    if tmp is not None:
        if type(tmp) in (boundsurf, boundsurf2):
            tmp.definiteRange = definiteRange
            return tmp, tmp.definiteRange
#        else:
#            return tmp, definiteRange

    tmp1 = lb1_ub1.resolve()[0] if firstIsBoundsurf else lb1_ub1

    tmp2 = lb2_ub2.resolve()[0] if secondIsBoundsurf else lb2_ub2

    lb1, ub1 = tmp1[0], tmp1[1]
    lb2, ub2 = tmp2[0], tmp2[1]

    tmp = vstack((td(lb1, lb2), td(lb1, ub2), td(ub1, lb2), td(ub1, ub2)))
    r = vstack((nanmin(tmp, 0), nanmax(tmp, 0)))
    update_div_zero(lb1, ub1, lb2, ub2, r)
    return r, definiteRange


#def rdiv_interval(self, r, other, domain, dtype):
#
#    Tmp, definiteRange = pow_const_interval(self, r, -1, domain, dtype)
#    print '-----'
#    print type(Tmp)
#    print Tmp if type(Tmp) == ndarray else Tmp.resolve()[0]
#    print other
#    return Tmp, definiteRange
    
#    arg_lb_ub, definiteRange = self._interval(domain, dtype, ia_surf_level = 1)
#    if type(arg_lb_ub) == boundsurf:
#        arg_lb_ub_resolved = arg_lb_ub.resolve()[0]
#        if all(arg_lb_ub_resolved >= 0) or all(arg_lb_ub_resolved <= 0):
#            return other * arg_lb_ub ** (-1), definiteRange
#        else:
#            arg_lb_ub = arg_lb_ub_resolved
#    arg_infinum, arg_supremum = arg_lb_ub[0], arg_lb_ub[1]
#    if other.size != 1: 
#        raise FuncDesignerException('this case for interval calculations is unimplemented yet')
#    r = vstack((other / arg_supremum, other / arg_infinum))
#    r.sort(axis=0)
#    r1, r2 = r
#    update_negative_int_pow_inf_zero(arg_infinum, arg_supremum, r, other)
#
#    return r, definiteRange

def get_inv_b2_coeffs(ll, uu, dll, duu, c_l, c_u):
    ind_z =  uu == ll
    dll, duu, c_l, c_u = duu, dll, c_u, c_l
    #L
    #L2, U2 = dll * ll + c_l, dll * uu + c_l
    #ind = L2<U2
    #l2 = np.where(ind, L2, U2)
#    print ll, uu, dll, duu, c_l, c_u
    ind = dll > 0
    
    argmin = np.where(ind, uu, ll)
    min_val = argmin * dll + c_l
#    print('l:',ll,'u:',uu,'argmin:', argmin, 'dll:',dll,'c_l:',c_l,'min_val:', min_val)

    dl = dll#np.where(ind, dll, duu)

#    a = dl**2 * min_val**-3  
#    b = -(2*dl**2+dl) * min_val**-2
    a = dl**2 * min_val**-3  
    b = - (dl*min_val+2*dl**2*argmin) * min_val**-3
#    a/=2
    a[ind_z] = b[ind_z] = 0.0
    ind_z2 = logical_or(logical_not(isfinite(a)), logical_not(isfinite(b)))
    a[ind_z2] = b[ind_z2] = 0.0
    c = 1.0/min_val + dl * argmin * min_val**-2 + dl**2 * argmin ** 2 * min_val**-3
    c[ind_z2] = 1.0/min_val[ind_z2]# - (a * argmin + b) * argmin
    koeffs_l = (a, b, c)
#    print a, b, c, a*argmin**2+b*argmin+ c, 1.0/(argmin * dll + c_l)
#    a, b, c = 0, 0, 0

#    from numpy.linalg import solve
#    from numpy import array, vstack
#    a, b, c = solve(vstack([[2*u, 1, 0], [l**2, l, 1], [u**2, u, 1]]), array([-dl/u2**2, 1/l2, 1/u2]))

#    #new
##    a = dl**2 * point_val**-3  #
#    a = argmin ** -3.0
#    b = - argmin ** -2.0 - 2 * a *  argmin
#    a[ind_z] = b[ind_z] = 0.0
#    ind_z2 = logical_or(logical_not(isfinite(a)), logical_not(isfinite(b)))
#    a[ind_z2] = b[ind_z2] = 0.0
#    c = 1.0 / argmin #- (a * argmin + b) * argmin
#    #/new
#    koeffs_l = array((a, b, c))
    
    
    #U
##    L2, U2 = duu * ll + c_u, duu * uu + c_u
##    ind = L2<U2
##    l2, u2 = np.where(ind, L2, U2), np.where(ind, U2, L2)
#    ind = duu > 0
#    l, u = np.where(ind, ll, uu), np.where(ind, uu, ll)
#    l2, u2 = l * duu + c_u, u * duu + c_u
#    dl = np.where(ind, dll, duu)
##    dl = np.where(ind, duu, dll)
#    inv_u2, inv_l2 = 1.0/u2, 1.0/l2
#    
##    a = (inv_u2 - inv_l2 + (l-u) * dl * inv_l2) * (u-l) ** -2.0
##    b = dl * inv_l2 - 2 * a * l
#    u2_2 = u2 ** 2
#    a = (1.0/l2  - 1.0/u2 + dl*(l-u)/u2_2) / (u-l)**2
#    b = -dl/u2_2 - 2*a*u
#
#    a[ind_z] = b[ind_z] = 0.0
#    ind_z2 = logical_or(logical_not(isfinite(a)), logical_not(isfinite(b)))
#    a[ind_z2] = b[ind_z2] = 0.0
#    c = inv_u2 - (a * u + b) * u
#    
    
    
    #############new
    ind = duu > 0
    argmax = np.where(ind, ll, uu)
    max_val = argmax * duu + c_u
#    print('l:',ll,'u:',uu,'argmax:', argmax, 'dll:',dll,'c_l:',c_l,'max_val:', max_val)

    dl = duu#np.where(ind, dll, duu)

#    a = dl**2 * max_val**-3  
#    b = -(2*dl**2+dl) * max_val**-2
    a = dl**2 * max_val**-3  
    b = - (dl*max_val+2*dl**2*argmax) * max_val**-3
#    a/=2
    a[ind_z] = b[ind_z] = 0.0
    ind_z2 = logical_or(logical_not(isfinite(a)), logical_not(isfinite(b)))
    a[ind_z2] = b[ind_z2] = 0.0
    c = 1.0/max_val + dl * argmax * max_val**-2 + dl**2 * argmax ** 2 * max_val**-3
    c[ind_z2] = 1.0/max_val[ind_z2]
    ################
    
    
    
#    from numpy.linalg import solve#    from numpy.linalg import solve
#    from numpy import array, vstack

#    from numpy import array, vstack
#    a, b, c = solve(vstack([[2*u, 1, 0], [l**2, l, 1], [u**2, u, 1]]), array([-dl/u2**2, 1/l2, 1/u2]))
    
    koeffs_u = array((a, b, c))
    
    return koeffs_l, koeffs_u

def pow_const_interval(self, r, other, domain, dtype):
    lb_ub, definiteRange = self._interval(domain, dtype, ia_surf_level = 2)
    isBoundSurf = isinstance(lb_ub, boundsurf)
    
    # changes
    if 1 and isBoundSurf and other == 2 and lb_ub.level == 1 and len(lb_ub.l.d) == 1 and len(lb_ub.u.d) == 1:
        L, U = lb_ub.l, lb_ub.u
        d, c = L.d, L.c
        s_l = surf2(dict((k, v**2) for k, v in d.items()), dict((k, 2*v*c) for k, v in d.items()), c**2)
        
        if lb_ub.l is lb_ub.u:
            return boundsurf2(s_l, s_l, definiteRange, domain), definiteRange
        
        d, c = U.d, U.c
        lb_ub_resolved = lb_ub.resolve()[0]
        if all(lb_ub_resolved >= 0):
            s_u = surf2(dict((k, v**2) for k, v in d.items()), dict((k, 2*v*c) for k, v in d.items()), c**2)
            return boundsurf2(s_l, s_u, definiteRange, domain), definiteRange
        elif all(lb_ub_resolved <= 0):
            s_u = s_l
            s_l = surf2(dict((k, v**2) for k, v in d.items()), dict((k, 2*v*c) for k, v in d.items()), c**2)
            return boundsurf2(s_l, s_u, definiteRange, domain), definiteRange
    # changes end
    
    lb_ub_resolved = lb_ub.resolve()[0] if isBoundSurf else lb_ub
    arg_isNonNegative = all(lb_ub_resolved >= 0)
    arg_isNonPositive = all(lb_ub_resolved <= 0)
    
    #changes
    # !!!!!!!TODO: rdiv beyond arg_isNonNegative, arg_isNonPositive
    if 1 and other == -1 and (arg_isNonNegative or arg_isNonPositive) and isBoundSurf and len(lb_ub.dep)==1:
        k = list(lb_ub.dep)[0]
        l, u = domain[k]
        d_l, d_u = lb_ub.l.d[k], lb_ub.u.d[k]
        c_l, c_u = lb_ub.l.c, lb_ub.u.c 
        if arg_isNonPositive:
#            print('arg_isNonPositive')
            lb_ub = -lb_ub
            d_l, d_u = -d_u, -d_l
            c_l, c_u = -c_u, -c_l

#        print lb_ub_resolved
#        print l, u, d_l, d_u, c_l, c_u
        koeffs_l, koeffs_u = get_inv_b2_coeffs(l, u, d_l, d_u, c_l, c_u)
        
#        ###########
#        from boundsurf2 import apply_quad_lin
#        a, b, c = koeffs_l
#        s_l = apply_quad_lin(a, b, c, lb_ub.l)
#        a, b, c = koeffs_u
#        s_u = apply_quad_lin(a, b, c, lb_ub.u)
#        ###########
#        print koeffs_l, koeffs_u
        if arg_isNonPositive:
            c_l, c_u = -c_u, -c_l
            d_l, d_u = -d_u, -d_l
            lb_ub = -lb_ub
            koeffs_l, koeffs_u = -array(koeffs_u), -array(koeffs_l)

        #############
        
        
        
        a, b, c = koeffs_l
        s_l = surf2({k:a}, {k:b}, c)
        a, b, c = koeffs_u
        s_u = surf2({k:a}, {k:b}, c)
        
#        ###############
#        from numpy import linspace
#        x = linspace(l, u, 2000)
#        d_l, d_u = lb_ub.l.d[k], lb_ub.u.d[k]
#        c_l, c_u = lb_ub.l.c, lb_ub.u.c 
#        import pylab
#        if 1:
#            pylab.plot(x, 1.0/(d_l*x+c_l), 'r', linewidth = 2)
#            pylab.plot(x, koeffs_l[0]*x**2+koeffs_l[1]*x+koeffs_l[2], 'b', linewidth = 1)
##        else:
#            pylab.plot(x, 1.0/(d_u*x+c_u), 'b', linewidth = 2)
#            pylab.plot(x, koeffs_u[0]*x**2+koeffs_u[1]*x+koeffs_u[2], 'r', linewidth = 1)
#        pylab.grid()
#        pylab.show()
#        ###############


        return boundsurf2(s_l, s_u, definiteRange, domain), definiteRange
        
    #changes end
    
    
    other_is_int = asarray(other, int) == other
    isOdd = other_is_int and other % 2 == 1
    if isBoundSurf and not any(np.isinf(lb_ub_resolved)):
        
        #new
#        if arg_isNonNegative: 
#            return defaultIntervalEngine(lb_ub, r.fun, r.d,  
#                monotonity = 1,  
#                convexity = 1 if other > 1.0 or other < 0 else -1) 
#        
#        if other_is_int and other > 0 and other % 2 == 0: 
#            return devided_interval(self, r, domain, dtype)
        
        #prev
        if arg_isNonNegative or (other_is_int and other > 0 and other % 2 == 0): 
            return defaultIntervalEngine(lb_ub, r.fun, r.d,  
                monotonity = 1 if other > 0 and arg_isNonNegative else -1 if arg_isNonNegative and other < 0 else np.nan,  
                convexity = 1 if other > 1.0 or other < 0 else -1,  
                criticalPoint = 0.0, criticalPointValue = 0.0)         
        
        feasLB = -inf if other_is_int else 0.0
        if other > 0 or arg_isNonPositive:
            return devided_interval(self, r, domain, dtype, feasLB = feasLB)
        
        if other_is_int and other < 0:# and other % 2 != 0:
            lb, ub = lb_ub_resolved 
            ind_positive, ind_negative, ind_z = split(lb >= 0, ub <= 0)
            B, inds = [], []
            if ind_positive.size:
                inds.append(ind_positive)
                monotonity = -1
                b = defaultIntervalEngine(lb_ub, r.fun, r.d, monotonity = monotonity, convexity = 1, 
                                          domain_ind = ind_positive)[0]
                B.append(b)
            if ind_negative.size:
                inds.append(ind_negative)
                
                # TODO: fix it
                monotonity = -1 if isOdd else 1
                
                convexity = -1 if isOdd else 1
                b = defaultIntervalEngine(lb_ub, r.fun, r.d, monotonity = monotonity, convexity = convexity, 
                                          domain_ind = ind_negative)[0]
                B.append(b)
            if ind_z.size:
                inds.append(ind_z)
                t = 1.0 / lb_ub_resolved[:, ind_z]
                t.sort(axis=0)
                update_negative_int_pow_inf_zero(lb_ub_resolved[0, ind_z], lb_ub_resolved[1, ind_z], t, other)
                b = boundsurf(
                              surf({}, t[0]), 
                              surf({}, t[1]), 
                              definiteRange if type(definiteRange) == bool or definiteRange.size == 1 \
                              else definiteRange[ind_z], 
                              domain)
                B.append(b)

            r = boundsurf_join(inds, B)
            return r, r.definiteRange

    lb_ub = lb_ub_resolved
    Tmp = lb_ub ** other
    Tmp.sort(axis = 0)
    lb, ub = lb_ub
    
    if not other_is_int or not isOdd:
        ind_z = logical_and(lb < 0, ub >= 0)
        if any(ind_z):
            Tmp[0, ind_z] = 0.0
            if not other_is_int:
                definiteRange = logical_and(definiteRange, logical_not(ind_z))

    if other < 0 and other_is_int:
        update_negative_int_pow_inf_zero(lb, ub, Tmp, other)

    return Tmp, definiteRange    

    
def pow_oofun_interval(self, other, domain, dtype): 
    # TODO: handle discrete cases
    lb1_ub1, definiteRange1 = self._interval(domain, dtype, ia_surf_level = 2)
    lb2_ub2, definiteRange2 = other._interval(domain, dtype, ia_surf_level = 2)
    if isinstance(lb1_ub1, boundsurf) or isinstance(lb2_ub2, boundsurf):
        r = (lb2_ub2 * lb1_ub1.log()).exp()
        return r, r.definiteRange
    
    lb1, ub1 = lb1_ub1#[0], lb1_ub1[1]
    lb2, ub2 = lb2_ub2#[0], lb2_ub2[1]
    T = vstack((lb1 ** lb2, lb1** ub2, ub1**lb2, ub1**ub2))
    t_min, t_max = nanmin(T, 0), nanmax(T, 0)
    definiteRange = logical_and(definiteRange1, definiteRange2)
    
    ind1 = lb1 < 0
    if any(ind1):
        definiteRange = logical_and(definiteRange, logical_not(ind1))
        ind2 = ub1 >= 0
        t_min[atleast_1d(logical_and(logical_and(ind1, ind2), logical_and(t_min > 0.0, ub2 > 0.0)))] = 0.0
        t_max[atleast_1d(logical_and(ind1, logical_not(ind2)))] = nan
        t_min[atleast_1d(logical_and(ind1, logical_not(ind2)))] = nan
    return vstack((t_min, t_max)), definiteRange
    
def defaultIntervalEngine(arg_lb_ub, fun, deriv, monotonity, convexity, criticalPoint = np.nan, 
                          criticalPointValue = np.nan, feasLB = -inf, feasUB = inf, domain_ind = slice(None), R0 = None):
    #monotonity = nan
    assert type(monotonity) != bool and type(convexity) != bool, 'bug in defaultIntervalEngine'
    
    Ld2, Ud2 = getattr(arg_lb_ub.l,'d2', {}),  getattr(arg_lb_ub.u,'d2', {})
#    print convexity, type(arg_lb_ub)

    # DEBUG!!!!!!!!!!!!!!!!!
#    if (len(Ld2) != 0 or len(Ud2) != 0): 
#        arg_lb_ub = arg_lb_ub.to_linear()
#        Ld2, Ud2 = {}, {}
    
#    if (len(Ld2) != 0 or len(Ud2) != 0) and convexity not in (-1, 1, -101, 9):
#        arg_lb_ub = arg_lb_ub.to_linear()
#        Ld2, Ud2 = {}, {}

    L, U, domain, definiteRange = arg_lb_ub.l, arg_lb_ub.u, arg_lb_ub.domain, arg_lb_ub.definiteRange
    Ld, Ud = L.d, U.d

    if type(domain_ind) == np.ndarray:
        if domain_ind.dtype == bool:
            domain_ind = where(domain_ind)[0]
        Ld, Ud = dict_reduce(Ld, domain_ind), dict_reduce(Ud, domain_ind)
        Ld2, Ud2 = dict_reduce(Ld2, domain_ind), dict_reduce(Ud2, domain_ind)
        R0 = (arg_lb_ub.resolve()[0] if R0 is None else R0)[:, domain_ind]
        if type(definiteRange) != bool and definiteRange.size > 1:
            definiteRange = definiteRange[domain_ind]
    elif R0 is None:
        R0 = arg_lb_ub.resolve()[0]
        
    #R0 = arg_lb_ub.resolve(ind = domain_ind)[0]
    
    assert R0.shape[0]==2, 'unimplemented yet'
    
    if feasLB != -inf or feasUB != inf:
        R0, definiteRange = adjustBounds(R0, definiteRange, feasLB, feasUB)
        
    r_l, r_u = R0
    R2 = fun(R0)
    
    ind_inf = np.where(np.logical_or(np.isinf(R2[0]), np.isinf(R2[1])))[0]

    koeffs = (R2[1] - R2[0]) / (r_u - r_l)
    koeffs[ind_inf] = 0.0
    
    ind_eq = where(r_u == r_l)[0]

    if monotonity == 1:
        new_l_resolved, new_u_resolved = R2
        U_dict, L_dict = Ud, Ld
        U2_dict, L2_dict = Ud2, Ld2
        _argmin, _argmax = r_l, r_u
    elif monotonity == -1:
        new_u_resolved, new_l_resolved = R2
        U_dict, L_dict = Ld, Ud
        U2_dict, L2_dict = Ld2, Ud2
        _argmin, _argmax = r_u, r_l
    else:
        assert len(Ld2) == len(Ud2) == 0, 'unimplemented'
        ind = R2[1] > R2[0] 
        R2.sort(axis=0)
        new_l_resolved, new_u_resolved = R2
        
        _argmin = where(ind, r_l, r_u)
        _argmax = where(ind, r_u, r_l)
        if criticalPoint is not np.nan:
            ind_c = logical_and(r_l < criticalPoint, r_u > criticalPoint)
            if convexity == 1:
                new_l_resolved[ind_c] = criticalPointValue
                _argmin[ind_c] = criticalPoint
            elif convexity == -1:
                new_u_resolved[ind_c] = criticalPointValue
                _argmax[ind_c] = criticalPoint
        Keys = set().union(set(Ld.keys()), set(Ud.keys()))

        L_dict = dict((k, where(ind, Ld.get(k, 0), Ud.get(k, 0))) for k in Keys)
        U_dict = dict((k, where(ind, Ud.get(k, 0), Ld.get(k, 0))) for k in Keys)
        if len(Ld2) != 0 or len(Ud2) != 0:
            L2_dict = dict((k, where(ind, Ld2.get(k, 0), Ud2.get(k, 0))) for k in Keys)
            U2_dict = dict((k, where(ind, Ud2.get(k, 0), Ld2.get(k, 0))) for k in Keys)
        else:
            L2_dict = U2_dict = {}

    if convexity == -1:
#        print('asdf')
#        L_dict, U_dict = U_dict, L_dict
        tmp2 = deriv(_argmax.view(multiarray)).view(ndarray).flatten()
        tmp2[ind_inf] = 0.0

        d_new = dict((v, tmp2 * val) for v, val in U_dict.items())
        
        if len(U2_dict) == 0:
            U_new = surf(d_new, 0.0)
        else:
            d2_new = dict((v, tmp2 * val) for v, val in U2_dict.items())
            U_new = surf2(d2_new, d_new, 0.0)

        U_new.c = new_u_resolved - U_new.maximum(domain, domain_ind)
        ind_inf2 = np.isinf(new_u_resolved)
        if any(ind_inf2):
            U_new.c = where(ind_inf2, new_u_resolved, U_new.c)
        
        # for some simple cases
        if len(L_dict) >= 1 or len(L2_dict) >= 1:
            if ind_eq.size:
                koeffs[ind_eq] = tmp2[ind_eq]
            d_new = dict((v, koeffs * val) for v, val in L_dict.items())
            
            if len(L2_dict) == 0:
                L_new = surf(d_new, 0.0)
            else:
                d2_new = dict((v, koeffs * val) for v, val in L2_dict.items())
                L_new = surf2(d2_new, d_new, 0.0)

            L_new.c = new_l_resolved -  L_new.minimum(domain, domain_ind)
#            print L_new.c, L_new.d, U_new.c, U_new.d
            if any(ind_inf2):
                L_new.c = where(ind_inf2, new_l_resolved, L_new.c)
        else:
            L_new = surf({}, new_l_resolved)                        
    elif convexity == 1:
        tmp2 = deriv(_argmin.view(multiarray)).view(ndarray).flatten()
        tmp2[ind_inf] = 0.0
        
        d_new = dict((v, tmp2 * val) for v, val in L_dict.items())
        if len(L2_dict) == 0:
            L_new = surf(d_new, 0.0)
        else:
            d2_new = dict((v, tmp2 * val) for v, val in L2_dict.items())
            L_new = surf2(d2_new, d_new, 0.0)
        L_new.c = new_l_resolved - L_new.minimum(domain, domain_ind)
        ind_inf2 = np.isinf(new_l_resolved)
        if any(ind_inf2):
            L_new.c = where(ind_inf2, new_l_resolved, L_new.c)
        
        # for some simple cases
        if len(U_dict) >= 1 or len(U2_dict) >= 1:
            if ind_eq.size:
                koeffs[ind_eq] = tmp2[ind_eq]
            d_new = dict((v, koeffs * val) for v, val in U_dict.items())
            if len(U2_dict) == 0:
                U_new = surf(d_new, 0.0)
            else:
                d2_new = dict((v, koeffs * val) for v, val in U2_dict.items())
                U_new = surf2(d2_new, d_new, 0.0)

            U_new.c = new_u_resolved - U_new.maximum(domain, domain_ind)
            if any(ind_inf2):
                U_new.c = where(ind_inf2, new_u_resolved, U_new.c)
#            print L_new.c, L_new.d, U_new.c, U_new.d
        else:
            U_new = surf({}, new_u_resolved)
    elif convexity == -101:
        if monotonity == 1:
            argvals = (_argmax, _argmin)
            vals = (new_u_resolved, new_l_resolved)[::-1]
            Attributes = ('maximum', 'minimum')
        elif monotonity == -1:
            argvals = (_argmin, _argmax)
            vals = (new_l_resolved, new_u_resolved)
            Attributes = ('minimum', 'maximum')
        else:
            assert 0
        
        tmp2 = deriv(argvals[0].view(multiarray)).view(ndarray).flatten()
        ind_k = where((tmp2 > koeffs) if monotonity == 1 else (tmp2 < koeffs))[0]
        tmp2[ind_k] = koeffs[ind_k]
        tmp2[ind_inf] = 0.0
        
        d_new = dict((v, tmp2 * val) for v, val in U_dict.items())
        if len(L2_dict) == 0:
            L_new = surf(d_new, 0.0)
        else:
            d2_new = dict((v, tmp2 * val) for v, val in U2_dict.items())
            L_new = surf2(d2_new, d_new, 0.0)

        L_new.c = vals[0] - getattr(L_new, Attributes[0])(domain, domain_ind)
#        L_new.c = vals[0] - L_new.minimum(domain, domain_ind)
#        L_new.c = new_l_resolved - L_new.minimum(domain, domain_ind)

        ind_inf2 = np.isinf(vals[0])
        if any(ind_inf2):
            L_new.c = where(ind_inf2, new_l_resolved, L_new.c)
        
        tmp2 = deriv(argvals[1].view(multiarray)).view(ndarray).flatten()
        ind_k = where((tmp2 > koeffs) if monotonity == 1 else (tmp2 < koeffs))[0]
        tmp2[ind_k] = koeffs[ind_k]
        tmp2[ind_inf] = 0.0
        
        d_new = dict((v, tmp2 * val) for v, val in L_dict.items())
#        U_new = surf(d_new, 0.0)
        if len(L2_dict) == 0:
            U_new = surf(d_new, 0.0)
        else:
            d2_new = dict((v, koeffs * val) for v, val in L2_dict.items())
            U_new = surf2(d2_new, d_new, 0.0)
                
        U_new.c = vals[1] - getattr(U_new, Attributes[1])(domain, domain_ind)
#        U_new.c = vals[1] - U_new.maximum(domain, domain_ind)
#        U_new.c = new_u_resolved - U_new.maximum(domain, domain_ind)
        ind_inf2 = np.isinf(vals[1])
        if any(ind_inf2):
            U_new.c = where(ind_inf2, new_u_resolved, U_new.c)
            
    elif convexity == 9: # 1 0 -1
        if monotonity == 1:
            argvals = (_argmin, _argmax)
            vals = (new_l_resolved, new_u_resolved)
            Attributes = ('minimum', 'maximum')
        elif monotonity == -1:
            argvals = (_argmax, _argmin)
            vals = (new_u_resolved, new_l_resolved)[::-1]
            Attributes = ('maximum','minimum')
        else:
            assert 0
        tmp2 = deriv(argvals[0].view(multiarray)).view(ndarray).flatten()
        ind_k = where(tmp2 > koeffs)[0]
        tmp2[ind_k] = koeffs[ind_k]
        tmp2[ind_inf] = 0.0
        
        d_new = dict((v, tmp2 * val) for v, val in L_dict.items())
        
        if len(L2_dict) == 0:
            L_new = surf(d_new, 0.0)
        else:
            d2_new = dict((v, tmp2 * val) for v, val in L2_dict.items())
            L_new = surf2(d2_new, d_new, 0.0)

        L_new.c = vals[0] - getattr(L_new, Attributes[0])(domain, domain_ind)
        ind_inf2 = np.isinf(vals[0])
        if any(ind_inf2):
            L_new.c = where(ind_inf2, vals[0], L_new.c)
        
        tmp2 = deriv(argvals[1].view(multiarray)).view(ndarray).flatten()
        ind_k = where(tmp2 > koeffs)[0]
        tmp2[ind_k] = koeffs[ind_k]
        tmp2[ind_inf] = 0.0
        
        d_new = dict((v, tmp2 * val) for v, val in U_dict.items())
        if len(U2_dict) == 0:
            U_new = surf(d_new, 0.0)
        else:
            d2_new = dict((v, tmp2 * val) for v, val in U2_dict.items())
            U_new = surf2(d2_new, d_new, 0.0)
        
        U_new.c = vals[1] - getattr(U_new, Attributes[1])(domain, domain_ind)
        ind_inf2 = np.isinf(vals[1])
        if any(ind_inf2):
            U_new.c = where(ind_inf2, vals[1], U_new.c)
            
    else:
        # linear oofuns with convexity = 0 calculate their intervals in other funcs
        raise FuncDesignerException('bug in FD kernel')
    if type(L_new) == type(U_new) == surf:
        R = boundsurf(L_new, U_new, definiteRange, domain)
    else:
        R = boundsurf2(L_new, U_new, definiteRange, domain)
    return R, definiteRange

def adjustBounds(R0, definiteRange, feasLB, feasUB):
    # adjust feasLB and feasUB
    r_l, r_u = R0
    ind_L = r_l < feasLB
    ind_l = where(ind_L)[0]
    ind_U = r_u > feasUB
    ind_u = where(ind_U)[0]
    if ind_l.size != 0 or ind_u.size != 0:
        R0 = R0.copy()
        r_l, r_u = R0
        
    if ind_l.size != 0:
        r_l[logical_and(ind_L, r_u >= feasLB)] = feasLB
        if definiteRange is not False:
            if type(definiteRange) != np.ndarray:
                definiteRange = np.empty_like(r_l, bool)
                definiteRange.fill(True)
            definiteRange[ind_l] = False
    if ind_u.size != 0:
        r_u[logical_and(ind_U, r_l <= feasUB)] = feasUB
        if definiteRange is not False:
            if type(definiteRange) != np.ndarray:
                definiteRange = np.empty_like(r_l, bool)
                definiteRange.fill(True)
            definiteRange[ind_u] = False
            
    return R0, definiteRange

dict_reduce = lambda d, ind: dict((k, v if v.size == 1 else v[ind]) for k, v in d.items())
