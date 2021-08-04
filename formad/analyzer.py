import z3
from formad.scope import Scope

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
  def __init__(self, parloop, parser):
    self.omppragmastr = parloop.content[0].tostr()
    self.vars = parser.vars
    self.controlPath = parser.controlPath
    self.loopCounter = parser.vars[parser.loopCounterName]
    self.counter0, self.counter1 = self.getCounterPair()
    self.ttypes = TupleTypes()
    self.buildModel(parser.controlPath, self.counter0 != self.counter1)

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
    self.loopCounter.pushInstance()
    counter1 = self.loopCounter.currentInstance.function
    return counter0, counter1

  def buildModel(self, scope, assertions):
    scope.props["z3"] = z3.Solver()
    scope.props["z3"].add(assertions)
    for varname in self.vars:
      var = self.vars[varname]
      if(repr(scope) in var.writeExpressions):
        writeexpr = var.writeExpressions[repr(scope)]
        for expr0t in writeexpr:
          expr0s = self.ttypes.tupleFromExpression(expr0t)
          expr0 = z3.substitute(expr0s, (self.counter0(), self.counter1()))
          for expr1t in writeexpr:
            expr1 = self.ttypes.tupleFromExpression(expr1t)
            scope.props["z3"].add(expr0 != expr1)
        print(f"scope {repr(scope)} has model {scope.props['z3'].assertions()}")
    for child in scope.children:
      self.buildModel(child, scope.props["z3"].assertions())




