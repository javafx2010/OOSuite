# created by Dmitrey
from numpy import copy, isnan, array, argmax, abs, vstack, zeros, any, isfinite, all, where, asscalar, \
sign, dot, sqrt, array_equal, nanmax, inf, hstack, isscalar, logical_or, matrix, asfarray, prod, arange
from numpy.linalg import norm
from nonOptMisc import Copy

from pointProjection import pointProjection



try:
    from scipy.sparse import csr_matrix
except:
    pass

__docformat__ = "restructuredtext en"
empty_arr = array(())
try:
    import scipy
    scipyInstalled = True
    from scipy.sparse import isspmatrix
except:
    scipyInstalled = False
    isspmatrix = lambda *args,  **kwargs:  False

class Point:
    """
    the class is used to prevent calling non-linear constraints more than once
    f, c, h are funcs for obtaining objFunc, non-lin ineq and eq constraints.
    df, dc, dh are funcs for obtaining 1st derivatives.
    """
    __expectedArgs__ = ['x', 'f', 'mr']
    def __init__(self, p, x, *args, **kwargs):
        self.p = p
        self.x = copy(x)
        for i, arg in enumerate(args):
            setattr(self, '_' + self.__expectedArgs__[i], args[i])
        for name, val in kwargs.iteritems():
            setattr(self, '_' + name, val)
        #assert self.x is not None

    def f(self):
        if not hasattr(self, '_f'): 
            if self.p._baseClassName == 'NonLin':
                self._f = self.p.f(self.x)
            else:
                self._f = self.p.objFunc(self.x)
        return copy(self._f)
        

    def df(self):
        if not hasattr(self, '_df'): self._df = self.p.df(self.x)
        return Copy(self._df)

    def c(self, ind=None):
        if not self.p.userProvided.c: return empty_arr.copy()
        if ind is None:
            if not hasattr(self, '_c'): self._c = self.p.c(self.x)
            return copy(self._c)
        else:
            if hasattr(self, '_c'): return copy(self._c[ind])
            else: return copy(self.p.c(self.x, ind))


    def dc(self, ind=None):
        if not self.p.userProvided.c: return empty_arr.copy().reshape(0, self.p.n)
        if ind is None:
            if not hasattr(self, '_dc'): self._dc = self.p.dc(self.x)
            return Copy(self._dc)
        else:
            
            if hasattr(self, '_dc'): return Copy(self._dc[ind])
            else: return Copy(self.p.dc(self.x, ind))


    def h(self, ind=None):
        if not self.p.userProvided.h: return empty_arr.copy()
        if ind is None:
            if not hasattr(self, '_h'): self._h = self.p.h(self.x)
            return copy(self._h)
        else:
            if hasattr(self, '_h'): return copy(self._h[ind])
            else: return copy(self.p.h(self.x, ind))

    def dh(self, ind=None):
        if not self.p.userProvided.h: return empty_arr.copy().reshape(0, self.p.n)
        #raise 0
        if ind is None:
            if not hasattr(self, '_dh'): self._dh = self.p.dh(self.x)
            return Copy(self._dh)
        else:
            if hasattr(self, '_dh'): 
                return Copy(self._dh[ind])
            else: 
                return Copy(self.p.dh(self.x, ind))

    def d2f(self):
        if not hasattr(self, '_d2f'): self._d2f = self.p.d2f(self.x)
        return copy(self._d2f)

#    def intConstraints(self):
#        if self.p.intVars == {} or self.p.intVars == []: return 0
#        if not hasattr(self, '_intConstraint'):
#            r = [norm(self.x[k]-self.p.intVars[k], -inf) for k in self.p.intVars.keys()]
#            self._intConstraints = max(r)
#
#        return copy(self._intConstraints)

    def lin_ineq(self):
        if not hasattr(self, '_lin_ineq'): self._lin_ineq = self.p._get_AX_Less_B_residuals(self.x)
        return copy(self._lin_ineq)

    def lin_eq(self):
        if not hasattr(self, '_lin_eq'): self._lin_eq = self.p._get_AeqX_eq_Beq_residuals(self.x)
        return copy(self._lin_eq)

    def lb(self):
        if not hasattr(self, '_lb'): self._lb = self.p.lb - self.x
        return copy(self._lb)

    def ub(self):
        if not hasattr(self, '_ub'): self._ub = self.x - self.p.ub
        return copy(self._ub)

    def mr(self, retAll = False):
        # returns max residual
        if not hasattr(self, '_mr'):
            r, fname, ind = 0, None, None
            ineqs = ['lin_ineq', 'lb', 'ub']
            eqs = ['lin_eq']
            if self.p._baseClassName == 'NonLin':
                ineqs.append('c')
                eqs.append('h')
            elif self.p.probType in ['MILP', 'MINLP']:
                pass
                #ineqs.append('intConstraints')
            for field in ineqs:
                fv = array(getattr(self, field)()).flatten()
                if fv.size > 0:
                    #ind_max = argmax(fv)
                    #val_max = fv[ind_max
                    val_max = nanmax(fv)
                    if not isnan(val_max):
                        ind_max = where(fv==val_max)[0][0]
                        if r < val_max:
                            r, ind, fname = val_max, ind_max, field
            for field in eqs:
                fv = array(getattr(self, field)()).flatten()
                if fv.size > 0:
                    fv = abs(fv)
                    ind_max = argmax(fv)
                    val_max = fv[ind_max]
                    if r < val_max:
                        r, ind, fname = val_max, ind_max, field
            self._mr, self._mrName,  self._mrInd= r, fname, ind
        if retAll:
            return asscalar(copy(self._mr)), self._mrName, asscalar(copy(self._mrInd))
        else: return asscalar(copy(self._mr))

    def mr_alt(self, retAll = False):
        if not hasattr(self, '_mr_alt'):
            mr, fname, ind = self.mr(retAll = True)
            self._mr_alt, self._mrName_alt,  self._mrInd_alt= mr, fname, ind
            c, h= self.c(), self.h()
            all_lin_ineq = self.__all_lin_ineq()
            r = 0.0
            Type = 'all_lin_ineq'
            if c.size != 0:
                ind_max = argmax(c)
                val_max = c[ind_max]
                if val_max > r:
                    r = val_max
                    Type = 'c'
                    ind = ind_max
            if h.size != 0:
                h = abs(h)
                ind_max = argmax(h)
                val_max = h[ind_max]
                #hm = abs(h).max()
                if val_max > r:
                    r = val_max
                    Type = 'h'
                    ind = ind_max
#            if lin_eq.size != 0:
#                l_eq = abs(lin_eq)
#                ind_max = argmax(l_eq)
#                val_max = l_eq[ind_max]
#                if val_max > r:
#                    r = val_max
#                    Type = 'lin_eq'
#                    ind = ind_max
            p = self.p
            #tol = 0.0
            tol = p.contol / 2.0
            if p.solver.approach == 'all active':
                val = (c[c>tol] - 0).sum() + (h[h>tol] - tol).sum() - (h[h<-tol] + tol).sum() + all_lin_ineq
                self._mr_alt, self._mrName_alt,  self._mrInd_alt = val, 'all active', 0
            else:
                val = r
                self._mr_alt, self._mrName_alt,  self._mrInd_alt = val, Type, 0
            assert p.nbeq == 0
        if retAll:
            return asscalar(copy(self._mr_alt)), self._mrName_alt, asscalar(copy(self._mrInd_alt))
        else: return asscalar(copy(self._mr_alt))

    def dmr(self, retAll = False):
        # returns direction for max residual decrease
        #( gradient for equality < 0 residuals ! )
        if not hasattr(self, '_dmr') or (retAll and not hasattr(self, '_dmrInd')):
            g = zeros(self.p.n)
            maxResidual, resType, ind = self.mr(retAll=True)
            if resType == 'lb':
                g[ind] -= 1 # N * (-1), -1 = dConstr/dx = d(lb-x)/dx
            elif resType == 'ub':
                g[ind] += 1 # N * (+1), +1 = dConstr/dx = d(x-ub)/dx
            elif resType == 'lin_ineq':
                g += self.p.A[ind]
            elif resType == 'lin_eq':
                rr = self.p.matmult(self.p.Aeq[ind], self.x)-self.p.beq[ind]
                if rr < 0:  g -= self.p.Aeq[ind]
                else:  g += self.p.Aeq[ind]
            elif resType == 'c':
                dc = self.dc(ind=ind).flatten()
                g += dc
            elif resType == 'h':
                dh = self.dh(ind=ind).flatten()
                if self.p.h(self.x, ind) < 0:  g -= dh#CHECKME!!
                else: g += dh#CHECKME!!
            else:
                # TODO: error or debug warning
                pass
                #self.p.err('incorrect resType')

            self._dmr, self._dmrName,  self._dmrInd = g, resType, ind
        if retAll:
            return copy(self._dmr),  self._dmrName,  copy(self._dmrInd)
        else:
            return copy(self._dmr)

    def betterThan(self, point2compare, altLinInEq = False, bestFeasiblePoint = None):
        """
        usage: result = involvedPoint.better(pointToCompare)

        returns True if the involvedPoint is better than pointToCompare
        and False otherwise
        (if NOT better, mb same fval and same residuals or residuals less than desired contol)
        """
        if self.p.isUC:
            return self.f() < point2compare.f()
            
        contol = self.p.contol

        if altLinInEq:
            mr_field = 'mr_alt'
        else:
            mr_field = 'mr'
        mr, point2compareResidual = getattr(self, mr_field)(), getattr(point2compare, mr_field)()
        if bestFeasiblePoint is not None:
            # TODO: fix f == nan cases!
            #if isnan(self_f): 
            mr = max((mr, self.f()  - bestFeasiblePoint.f()))
            #print mr
            point2compareResidual = max((point2compare.f() - bestFeasiblePoint.f(), point2compareResidual))
        criticalResidualValue = max((self.p.contol, point2compareResidual))
        self_nNaNs, point2compare_nNaNs = self.nNaNs(), point2compare.nNaNs()

        if point2compare_nNaNs  > self_nNaNs: return True
        elif point2compare_nNaNs  < self_nNaNs: return False
        
        # TODO: check me
        if self_nNaNs == 0:
            if mr > self.p.contol and mr > point2compareResidual: return False
            elif point2compareResidual > self.p.contol and point2compareResidual > mr: return True
        else: # got here means self_nNaNs = point2compare_nNaNs but not equal to 0
            if mr == 0 and point2compareResidual == 0: 
                self.p.err('you should provide at least one active constraint in each point from R^n where some constraints are undefined')
            return mr < point2compareResidual

        point2compareF_is_NaN = isnan(point2compare.f())
        selfF_is_NaN = isnan(self.f())

        if not point2compareF_is_NaN: # f(point2compare) is not NaN
            if not selfF_is_NaN: # f(newPoint) is not NaN
                return self.f() < point2compare.f()
            else: # f(newPoint) is NaN
                return False
        else: # f(point2compare) is NaN
            if selfF_is_NaN: # f(newPoint) is NaN
                return mr < point2compareResidual
            else: # f(newPoint) is not NaN
                return True

    def isFeas(self, altLinInEq):
        if not all(isfinite(self.f())): return False
        contol = self.p.contol
        if altLinInEq:
            if hasattr(self, '_mr_alt'):
                if self._mr_alt > contol or self.nNaNs() != 0: return False
            else:
                #TODO: simplify it!
                #for fn in residuals: (...)
                if self.__all_lin_ineq() > contol: return False
        else:
            if hasattr(self, '_mr'):
                if self._mr > contol or self.nNaNs() != 0: return False
            else:
                #TODO: simplify it!
                #for fn in residuals: (...)
                if any(self.lb() > contol): return False
                if any(self.ub() > contol): return False
                if any(abs(self.lin_eq()) > contol): return False
                if any(self.lin_ineq() > contol): return False
        if any(abs(self.h()) > contol): return False
        if any(self.c() > contol): return False
        return True

    def nNaNs(self):
        # returns number of nans in constraints
        if self.p._baseClassName != 'NonLin': return 0
        r = 0
        c, h = self.c(), self.h()
        r += len(where(isnan(c))[0])
        r += len(where(isnan(h))[0])
        return r
    
    def linePoint(self, alp, point2, ls=None):
        # returns alp * point1 + (1-alp) * point2
        # where point1 is self, alp is real number
        assert isscalar(alp)
        p = self.p
        r = p.point(self.x * (1-alp) + point2.x * alp)
        
        #lin_eqs = self.lin_eq()*alp +  point2.lin_eq() * (1-alp)
        #print '!>>, ',  p.norm(lin_eqs), p.norm(lin_eqs - r.lin_eq())
        
        # TODO: optimize it, take ls into account!
        #if ls is not None and 
        if not (p.iter % 16):
            lin_ineq_predict = self.lin_ineq()*(1-alp) +  point2.lin_ineq() * alp
            #if 1 or p.debug: print('!>>', p.norm(lin_ineq_predict-r.lin_ineq()))
            r._lin_ineq = lin_ineq_predict
            r._lin_eq = self.lin_eq()*(1-alp) +  point2.lin_eq() * alp
        
        # don't calculate c for inside points
        if 0<alp<1:
            c1, c2 = self.c(), point2.c()
            ind1 = logical_or(c1 > 0,  isnan(c1))
            ind2 = logical_or(c2 > 0,  isnan(c2))
            ind = where(ind1 | ind2)[0]
            
            _c = zeros(p.nc)
            if ind.size != 0:
                _c[ind] = p.c(r.x, ind)
            r._c = _c
        
        # TODO: mb same for h?

        
        return r
        

#    def directionType(self, *args, **kwargs):
#        if not hasattr(self, 'dType'):
#            self.__getDirection__(*args, **kwargs)
#        return self.dType

    #def __getDirection__(self, useCurrentBestFeasiblePoint = False):
    #def __getDirection__(self, altLinInEq = False):

    def __all_lin_ineq(self): # TODO: rename it wrt lin_eq that are present here
        if not hasattr(self, '_all_lin_ineq'):
            lb, ub, lin_ineq = self.lb(), self.ub(), self.lin_ineq()
            r = 0.0
            # TODO: CHECK IT - when 0 (if some nans), when contol
            #threshold = self.p.contol/2.0
            threshold = 0.0
#            if all(isfinite(self.f())): threshold = self.p.contol
#            else: threshold = 0

            lb, ub = self.lb(), self.ub()
            lin_ineq = self.lin_ineq()
            lin_eq = self.lin_eq()
            ind_lb, ind_ub = where(lb>threshold)[0], where(ub>threshold)[0]
            ind_lin_ineq = where(lin_ineq>threshold)[0]
            ind_lin_eq = where(abs(lin_eq)>threshold)[0]
            USE_SQUARES = 1
            if USE_SQUARES:
                if ind_lb.size != 0:
                    r += sum((lb[ind_lb]-threshold) ** 2)
                if ind_ub.size != 0:
                    r += sum((ub[ind_ub]-threshold) ** 2)
                if ind_lin_ineq.size != 0:
                    r += sum((lin_ineq[ind_lin_ineq]-threshold) ** 2)
                if ind_lin_eq.size != 0:
                    r += sum((lin_eq[ind_lin_eq]-threshold) ** 2)
                #self._all_lin_ineq = sqrt(r)
                self._all_lin_ineq = r / self.p.contol
            else:
                if ind_lb.size != 0:
                    r += sum(lb[ind_lb])
                if ind_ub.size != 0:
                    r += sum(ub[ind_ub])
                if ind_lin_ineq.size != 0:
                    r += sum(lin_ineq[ind_lin_ineq])
                if ind_lin_eq.size != 0:
                    r += sum(abs(lin_eq[ind_lin_eq]))
                self._all_lin_ineq = r
                    
        return copy(self._all_lin_ineq)

    def __all_lin_ineq_gradient(self):
        if not hasattr(self, '_all_lin_ineq_gradient'):
            p = self.p
            n = p.n
            d = zeros(n)
            threshold = 0.0
            #threshold = self.p.contol/2.0

            lb, ub = self.lb(), self.ub()
            lin_ineq = self.lin_ineq()
            lin_eq = self.lin_eq()
            ind_lb, ind_ub = where(lb>threshold)[0], where(ub>threshold)[0]
            ind_lin_ineq = where(lin_ineq>threshold)[0]
            ind_lin_eq = where(abs(lin_eq)>threshold)[0]
            

            USE_SQUARES = 1
            if USE_SQUARES:
                if ind_lb.size != 0:
                    d[ind_lb] -= lb[ind_lb]-threshold# d/dx((x-lb)^2) for violated constraints
                if ind_ub.size != 0:
                    d[ind_ub] += ub[ind_ub]-threshold# d/dx((x-ub)^2) for violated constraints
                if ind_lin_ineq.size != 0:
                    # d/dx((Ax-b)^2)
                    b = p.b[ind_lin_ineq]
                    if hasattr(p, '_A'):
                        a = p._A[ind_lin_ineq] 
                        tmp = a._mul_sparse_matrix(csr_matrix((self.x, (arange(n), zeros(n))), shape=(n, 1))).toarray().flatten() - b - threshold
                        
                        #tmp = a._mul_sparse_matrix(csr_matrix((self.x, reshape(p.n, 1))).toarray().flatten() - b - threshold
                        d += a.T._mul_sparse_matrix(tmp.reshape(tmp.size, 1)).A.flatten()
                        #d += dot(a.T, dot(a, self.x)  - b) 
                    else:
                        a = p.A[ind_lin_ineq] 
                        d += dot(a.T, dot(a, self.x)  - b-threshold) # d/dx((Ax-b)^2)
                if ind_lin_eq.size != 0:
                    raise ('nonzero threshold is not ajusted with lin eq yet')
                    aeq = p.Aeq[ind_lin_eq]
                    beq = p.beq[ind_lin_eq]
                    d += dot(aeq.T, dot(aeq, self.x)  - beq) # 0.5*d/dx((Aeq x - beq)^2)
                    
                #devider = self.__all_lin_ineq()
                devider = 0.5*self.p.contol
                if devider != 0:
                    self._all_lin_ineq_gradient = d / devider
                else:
                    self._all_lin_ineq_gradient = d
            else:
                if ind_lb.size != 0:
                    d[ind_lb] -= 1# d/dx(lb-x) for violated constraints
                if ind_ub.size != 0:
                    d[ind_ub] += 1# d/dx(x-ub) for violated constraints
                if ind_lin_ineq.size != 0:
                    # d/dx(Ax-b)
                    b = p.b[ind_lin_ineq]
                    if hasattr(p, '_A'):
                        d += (p._A[ind_lin_ineq]).sum(0).A.flatten()
                    else:
                        d += (p.A[ind_lin_ineq]).sum(0).flatten()
                if ind_lin_eq.size != 0:
                    # currently for ralg it should be handled in dilation matrix
                    p.err('not implemented yet, if you see it inform OpenOpt developers')
#                    beq = p.beq[ind_lin_eq]
#                    if hasattr(p, '_Aeq'):
#                        tmp = p._Aeq[ind_lin_eq]
#                        ind_change = where()
#                        tmp
#                        d += ().sum(0).A.flatten()
#                    else:
#                        #d += (p.Aeq[ind_lin_eq]).sum(0).flatten()

#                    aeq = p.Aeq[ind_lin_eq]
#                    beq = p.beq[ind_lin_eq]
#                    d += dot(aeq.T, dot(aeq, self.x)  - beq) # 0.5*d/dx((Aeq x - beq)^2)
                self._all_lin_ineq_gradient = d
        return copy(self._all_lin_ineq_gradient)

    def _getDirection(self, approach, currBestFeasPoint = None):
#        if hasattr(self, 'direction'):
#            return self.direction.copy()
        p = self.p
        contol = p.contol
        maxRes, fname, ind = self.mr_alt(1)
        x = self.x
        if self.isFeas(altLinInEq=True):
            self.direction, self.dType = self.df(),'f'
            if hasattr(self.direction, 'toarray'): self.direction = self.direction.toarray().flatten()
            return self.direction.copy()
        else:
            if approach == 'all active':
                direction = self.__all_lin_ineq_gradient()
                new = 1
                if p.userProvided.c:
                    th = 0.0
                    #th = contol / 2.0
                    C = p.c(x)
                    ind = where(C>th)[0]
                    activeC = C[ind]
                    if len(ind) > 0:
                        tmp = p.dc(x, ind)
                        if new:
                            if tmp.ndim == 1 or min(tmp.shape) == 1:
                                if hasattr(tmp, 'toarray'): 
                                    tmp = tmp.toarray()#.flatten()
                                if activeC.size == prod(tmp.shape):
                                    activeC = activeC.reshape(tmp.shape)
                                tmp *= (activeC-th*(1.0-1e-15))/norm(tmp)
                            else:
                                if hasattr(tmp, 'toarray'):
                                    tmp = tmp.toarray()
                                tmp *= ((activeC - th*(1.0-1e-15))/sqrt((tmp**2).sum(1))).reshape(-1, 1)
                            
                        if tmp.ndim > 1:
                            tmp = tmp.sum(0)
                        direction += (tmp.A if isspmatrix(tmp) or isinstance(tmp, matrix) else tmp).flatten()
                

                if p.userProvided.h:
                    #th = 0.0
                    th = contol / 2.0
                    H = p.h(x)
                    ind1 = where(H>th)[0]
                    H1 = H[ind1]
                    if len(ind1) > 0:
                        tmp = p.dh(x, ind1)
                        if new:
                            if tmp.ndim == 1 or min(tmp.shape) == 1:
                                if hasattr(tmp, 'toarray'): 
                                    tmp = tmp.toarray()#.flatten()
                                if H1.size == prod(tmp.shape):
                                    H1 = H1.reshape(tmp.shape)
                                tmp *= (H1-th*(1.0-1e-15))/norm(tmp)
                            else:
                                if hasattr(tmp, 'toarray'):
                                    tmp = tmp.toarray()
                                tmp *= ((H1 - th*(1.0-1e-15))/sqrt((tmp**2).sum(1))).reshape(-1, 1)
                        
                        if tmp.ndim > 1: 
                            tmp = tmp.sum(0)
                        direction += (tmp.A if isspmatrix(tmp) or isinstance(tmp, matrix) else tmp).flatten()
                    ind2 = where(H<-th)[0]
                    H2 = H[ind2]
                    if len(ind2) > 0:
                        tmp = p.dh(x, ind2)
                        if new:
                            if tmp.ndim == 1 or min(tmp.shape) == 1:
                                if hasattr(tmp, 'toarray'): 
                                    tmp = tmp.toarray()#.flatten()
                                if H2.size == prod(tmp.shape):
                                    H2 = H2.reshape(tmp.shape)                                    
                                tmp *= (-H2-th*(1.0-1e-15))/norm(tmp)
                            else:
                                if hasattr(tmp, 'toarray'):
                                    tmp = tmp.toarray()
                                tmp *= ((-H2 - th*(1.0-1e-15))/sqrt((tmp**2).sum(1))).reshape(-1, 1)
                        
                        if tmp.ndim > 1: 
                            tmp = tmp.sum(0)
                        direction -= (tmp.A if isspmatrix(tmp) or isinstance(tmp, matrix) else tmp).flatten()
                self.dType  = 'all active'
                self.direction = direction
            else:
                if fname == 'all_lin_ineq':
                    d = self.__all_lin_ineq_gradient()
                    self.dType = 'all_lin_ineq'
                elif fname == 'lin_eq':
                    self.p.err("kernel error, inform openopt developers")
                    #d = self.dmr()
                    #self.dType = 'lin_eq'
                elif fname == 'c':
                    d = self.dmr()
                    #if p.debug: assert array_equal(self.dc(ind).flatten(), self.dmr())
                    self.dType = 'c'
                elif fname == 'h':
                    d = self.dmr()#sign(self.h(ind))*self.dh(ind)
                    #if p.debug: assert array_equal(self.dh(ind).flatten(), self.dmr())
                    self.dType = 'h'
                else:
                    p.err('error in getRalgDirection (unknown residual type ' + fname + ' ), you should report the bug')
                self.direction = d.flatten()
            if currBestFeasPoint is not None:
                DF = self.df()
                nDF = norm(DF)
                if nDF > 1e-50:
                    Ftol = p.Ftol/2.0 if hasattr(p, 'Ftol') else 15 * p.ftol
                    self.direction += (self.f()-currBestFeasPoint.f()-Ftol) * DF / nDF
            if hasattr(self.direction, 'toarray'): self.direction = self.direction.toarray().flatten()
            return self.direction.copy() # it may be modified in ralg when some constraints coords are NaN

#    def __getDirection__(self, useCurrentBestFeasiblePoint = False):
#        if hasattr(self, 'direction'):
#            return self.direction
#        p = self.p
#        contol = p.contol
#        maxRes, fname, ind = self.mr(retAll=True)
#        if (maxRes <= p.contol and all(isfinite(self.df())) and (p.isNaNInConstraintsAllowed or self.nNaNs() == 0)) \
#        or (useCurrentBestFeasiblePoint and hasattr(p, 'currentBestFeasiblePoint') and self.f() - p.currentBestFeasiblePoint.f() > self.mr()):
#        #if (maxRes <= p.contol and all(isfinite(self.df())) and (p.isNaNInConstraintsAllowed or self.nNaNs() == 0)) :
#            self.direction, self.dType = self.df(),'f'
#            return self.direction
#        else:
#            d = zeros(p.n)
#            #if any(self.lb()>contol) or any(self.ub()>contol) or any(self.lin_eq()>contol) or any(self.lin_ineq()>contol):
#            lb = self.lb()
#            ub = self.ub()
#            lin_ineq = self.lin_ineq()
#            lin_eq = self.lin_eq()
#            c = self.c()
#            h = self.h()
#
#            LB = lb[lb>contol/2]
#            UB = ub[ub>contol/2]
#            LIN_INEQ = lin_ineq[lin_ineq>contol/2]
#            nActiveLinInEq = LB.size + UB.size + LIN_INEQ.size
#            LinConstraints = sum(LB** 2) + sum(UB ** 2)
#            if  LIN_INEQ.size > 0: LinConstraints+= sum(LIN_INEQ ** 2)
#            #if  lin_eq.size > 0: LinConstraints+= sum(lin_eq[abs(lin_eq)>contol] ** 2)
##
#            maxNonLinConstraint = 0.0
#            if c.size > 0: maxNonLinConstraint = max((maxNonLinConstraint, max(c)))
#            if h.size > 0: maxNonLinConstraint = max((maxNonLinConstraint, max(abs(h))))
#
#            if nActiveLinInEq != 0 and LinConstraints/nActiveLinInEq >= p.contol * maxNonLinConstraint and (lin_eq.size == 0 or LinConstraints/nActiveLinInEq >= p.contol * abs(lin_eq).max()):#fname in ['lb',  'ub',  'lin_eq',  'lin_ineq']:# or tmp > maxNonLinConstraint:
#                threshold = contol
#                ind_lb = where(lb>contol)[0]
#                ind_ub = where(ub>contol)[0]
#                ind_lin_ineq = where(lin_ineq>threshold)[0]
#                #ind_lin_eq = where(abs(lin_eq)>threshold)[0]
#
#                if ind_lb.size != 0:
#                    d[ind_lb] -= lb[ind_lb]# 0.5*d/dx((x-lb)^2) for violated constraints
#                if ind_ub.size != 0:
#                    d[ind_ub] += ub[ind_ub]# 0.5*d/dx((x-ub)^2) for violated constraints
#                if ind_lin_ineq.size != 0:
#                    a = p.A[ind_lin_ineq]
#                    b = p.b[ind_lin_ineq]
#                    d += dot(a.T, dot(a, self.x)  - b) # 0.5*d/dx((Ax-b)^2)
##                if ind_lin_eq.size != 0:
##                    aeq = p.Aeq[ind_lin_eq]
##                    beq = p.beq[ind_lin_eq]
##                    d += dot(aeq.T, dot(aeq, self.x)  - beq) # 0.5*d/dx((Ax-b)^2)
#                self.direction, self.dType = d/p.contol/nActiveLinInEq, 'linear'
#            elif fname == 'lin_eq':
#                d = self.dmr()
#                self.direction = d.flatten()
#                self.dType = 'lin_eq'
#            elif fname == 'c':
#                d = self.dmr()#self.dc(ind)
#                self.direction = d.flatten()
#                self.dType = 'c'
#            elif fname == 'h':
#                d = self.dmr()#sign(self.h(ind))*self.dh(ind)
#                self.direction = d.flatten()
#                self.dType = 'h'
#            else:
#                p.err('error in getRalgDirection (unknown residual type ' + fname + ' ), you should report the bug')
#            return self.direction

