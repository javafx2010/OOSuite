from numpy.linalg import norm
from numpy import dot, asfarray, atleast_1d,  zeros, ones, int, float64, where, inf, linalg, ndarray
from openopt.kernel.baseSolver import baseSolver

try:
    import scipy
    scipyInstalled = True
except:
    scipyInstalled = False

class defaultSLEsolver(baseSolver):
    __name__ = 'defaultSLEsolver'
    __license__ = "BSD"
    __authors__ = 'Dmitrey'
    __alg__ = ''
    __info__ = ''
    matrixSLEsolver = 'autoselect'
    sparseSolvers = ['bicg', 'bicgstab', 'cg', 'cgs', 'gmres', 'minres', 'qmr', 'spsolve']
    denseSolvers = ['numpy_linalg_solve']
    defaultSparseSolver = 'spsolve'
    defaultDenseSolver = 'numpy_linalg_solve'
    #__optionalDataThatCanBeHandled__ = []

    def __init__(self): pass

    def __solver__(self, p):
        #p.debug = 1
        # TODO: code clean up
        solver = self.matrixSLEsolver
        if solver in self.denseSolvers:
            useDense = True
        elif solver in self.sparseSolvers:
            useDense = False
        elif solver == 'autoselect':
            if not scipyInstalled or not hasattr(scipy.sparse, 'linalg'):
                useDense = True
                if isinstance(p.C, ndarray) and len(p.C.nonzero()[0]) > 0.25 * p.C.size > 10000: 
                    if not hasattr(scipy.sparse, 'linalg'):
                        s = """you use new version of scipy where scipy.sparse.linalg was moved to scikits.umfpack. 
                        It is not ajusted with the version of our soft you are using yet. 
                        Thus SLE will be solved as dense. 
                        If sparsity is strongly required, you could use rendering (see FuncDesigner doc)"""
                        p.pWarn(s)
                    else:
                        pass
                    #p.pWarn(scipyAbsentMsg)
                    
                solver = self.defaultDenseSolver
                self.matrixSLEsolver = solver
                
            else:
                solver = self.defaultSparseSolver
                self.matrixSLEsolver = solver
                useDense = False
        else:
            p.err('Incorrect SLE solver (%s)' % solver)
                
        if isinstance(solver, str): 
            if solver == 'numpy_linalg_solve':
                solver = linalg.solve
            else:
                solver = getattr(scipy.sparse.linalg, solver)
            
        if useDense:
            #p.debugmsg('dense SLE solver')
            try:
                C = p.C.toarray() if not isinstance(p.C, ndarray) else p.C
                if self.matrixSLEsolver == 'autoselect': 
                    self.matrixSLEsolver = linalg.solve
                xf = solver(C, p.d)
                istop, msg = 10, 'solved'
                p.xf = xf
                p.ff = norm(dot(C, xf)-p.d, inf)
            except linalg.LinAlgError:
                istop, msg = -10, 'singular matrix'
        else: # is sparse
            #p.debugmsg('sparse SLE solver')
            try:
                if not hasattr(p, 'C_as_csc'):p.C_as_csc = scipy.sparse.csc_matrix(p.C)
                xf = solver(p.C_as_csc, p.d)#, maxiter=10000)
                solver_istop = 0
                if solver_istop == 0:
                    istop, msg = 10, 'solved'
                else:
                    istop, msg = -104, 'the solver involved failed to solve the SLE'
                    if solver_istop < 0: msg += ', matter: illegal input or breakdown'
                    else: msg += ', matter: convergence to tolerance not achieved, number of iterations: %d' % solver_istop
                p.xf = xf                
                p.ff = norm(p.C_as_csc._mul_sparse_matrix(scipy.sparse.csr_matrix(xf.reshape(-1, 1))).toarray().flatten()-p.d, inf)                
            except:
                istop, msg = -100, 'unimplemented exception while solving sparse SLE'
        p.istop, p.msg = istop, msg

