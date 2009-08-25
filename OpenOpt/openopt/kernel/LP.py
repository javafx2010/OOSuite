from ooMisc import assignScript
from baseProblem import MatrixProblem
from numpy import asarray, ones, inf, dot, nan, zeros
import NLP

class LP(MatrixProblem):
    __optionalData__ = ['A', 'Aeq', 'b', 'beq', 'lb', 'ub']
    expectedArgs = ['f']
    def __init__(self, *args, **kwargs):
        kwargs2 = kwargs.copy()
        if len(args) > 0: kwargs2['f'] = args[0]
        self.probType = 'LP'
        MatrixProblem.__init__(self, *args, **kwargs)
        lp_init(self, kwargs2)

    def __prepare__(self):
        MatrixProblem.__prepare__(self)
        if self.goal in ['max', 'maximum']:
            self.f = -self.f
            
    # TODO: handle this and SDP finalize in single func finalize_for_max
    def __finalize__(self):
        MatrixProblem.__finalize__(self)
        if self.goal in ['max', 'maximum']:
            self.f = -self.f
            for fn in ['fk', ]:#not ff - it's handled in other place in RunProbSolver.py
                if hasattr(self, fn):
                    setattr(self, fn, -getattr(self, fn))

            
    def objFunc(self, x):
        return dot(self.f, x)

    def lp2nlp(self, solver, **solver_params):
        if self.isConverterInvolved and self.goal in ['max', 'maximum']:
            self.err('maximization problems are not implemented lp2nlp converter')
        ff = lambda x: dot(x, self.f)
        dff = lambda x: self.f
        if hasattr(self,'x0'): p = NLP.NLP(ff, self.x0, df=dff)
        else: p = NLP.NLP(ff, zeros(self.n), df=dff)
        self.inspire(p)
        self.iprint = -1

        # for LP plot is via NLP
        p.show = self.show
        p.plot, self.plot = self.plot, 0

        r = p.solve(solver, **solver_params)
        self.xf, self.ff, self.rf = r.xf, r.ff, r.rf

        return r


def lp_init(prob, kwargs):

    prob.goal = 'minimum'
    prob.allowedGoals = ['minimum', 'min', 'max', 'maximum']
    prob.showGoal = True

    f = asarray(kwargs['f'], float)
    kwargs['f'] = f

    prob.n = len(f)
    if prob.x0 is nan: prob.x0 = zeros(prob.n)
    prob.lb = -inf * ones(prob.n)
    prob.ub =  inf * ones(prob.n)

    return assignScript(prob, kwargs)



