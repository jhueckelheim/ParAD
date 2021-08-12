import z3
import json
from formad.scope import Scope
import logging

class TupleTypes:
  def __init__(self):
    self.tuples = {}

  def tupleWithDims(self, dims):
    if not (dims in self.tuples):
      self.tuples[dims] = z3.Datatype('tuple')
      self.tuples[dims].declare(f'tuple', *((str(x), z3.RealSort()) for x in range(dims)))
      self.tuples[dims] = self.tuples[dims].create()
    return self.tuples[dims]

  def tupleFromExpression(self, expr):
    tupletype = self.tupleWithDims(len(expr))
    return tupletype.tuple(*expr)

class ParloopAnalyzer:
  def __init__(self, parloop, parser, questionvars):
    self.omppragmastr = parloop.content[0].tostr()
    self.vars = parser.vars
    self.controlPath = parser.controlPath
    self.loopCounter = parser.vars[parser.loopCounterName]
    self.counter0, self.counter1 = self.getCounterPair()
    self.ttypes = TupleTypes()
    self.isSafe = {x:True for x in self.vars}
    self.checkModel(parser.controlPath, self.counter0 != self.counter1)
    isSafeLower = {x.lower():self.isSafe[x] for x in self.isSafe}
    self.safeQueryVars = {var:isSafeLower[f"{var}_b"] for var in questionvars}

  def getCounterPair(self):
    '''
    We need the two loop counters (i and i') that are guaranteed to be distinct
    in two different iterations, and two different threads. In reality, they
    may of course have different names than i and i'.
    '''
    assert(len(self.loopCounter.instances) == 1)
    # In fortran, the loop counter must not be modified within the loop body.
    # If the loopcounter has more than one instance, something must be wrong.
    counter0 = self.loopCounter.currentInstance.function
    self.loopCounter.pushInstance(True)
    counter1 = self.loopCounter.currentInstance.function
    return counter0, counter1

  def checkModel(self, scope, assertions):
    scope.props["z3"] = z3.Solver()
    scope.props["z3"].add(assertions)
    for varname in self.vars:
      if not varname.endswith("_b"):
        #print(f"known writes for {varname}:")
        var = self.vars[varname]
        if(repr(scope) in var.writeExpressions):
          writeexpr = var.writeExpressions[repr(scope)]
          for expr0t in writeexpr:
            #print(f"  {expr0t}")
            expr0s = self.ttypes.tupleFromExpression(expr0t)
            expr0 = z3.substitute(expr0s, (self.counter0(), self.counter1()))
            for expr1t in writeexpr:
              expr1 = self.ttypes.tupleFromExpression(expr1t)
              scope.props["z3"].add(expr0 != expr1)
          assert(scope.props['z3'].check() == z3.z3.sat)
    for varname in self.vars:
      if varname.endswith("_b") and self.isSafe[varname]:
        # we check the safety of adjoint variables, but only if they haven't
        # already been found unsafe.
        #print(f"checking writes for {varname}:")
        var = self.vars[varname]
        if(repr(scope) in var.writeExpressions):
          writeexpr = var.writeExpressions[repr(scope)]
          for expr0t in writeexpr:
            if(self.isSafe[varname]):
              expr0s = self.ttypes.tupleFromExpression(expr0t)
              expr0 = z3.substitute(expr0s, (self.counter0(), self.counter1()))
              for expr1t in writeexpr:
                expr1 = self.ttypes.tupleFromExpression(expr1t)
                scope.props["z3"].push()
                scope.props["z3"].add(expr0 == expr1)
                if(scope.props["z3"].check() != z3.z3.unsat):
                  logging.debug(f"###found {varname} unsafe with {expr0} == {expr1}")
                  logging.debug(str(scope.props["z3"].assertions()))
                  self.isSafe[varname] = False
                  break
                scope.props["z3"].pop()
    for child in scope.children:
      self.checkModel(child, scope.props["z3"].assertions())
