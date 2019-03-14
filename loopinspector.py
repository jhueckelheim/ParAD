import fparser.two.Fortran2003 as f2003
import ompparser
import sympy
import operator

class VariableProperty:
  """
  Manage information available for a variable:
   - expressions to index the variable for read and write,
   - a sympy.Symbol for this variable,
   - whether this variable is the loop counter,
   - whether this variable has symmetric read/write access
  """

  def __init__(self, varname):
    self.name = varname
    self.function = sympy.Function(varname)
    self.loopCounter = False
    self.indexFunctions = set()

  def makeLoopCounter(self):
    self.loopCounter = True

  def addIndexFunctions(self, func):
    self.indexFunctions.update(func)

class ReadWriteInspector:
  """
  Inspector that finds read and write access within an AST.
  ThreAD threADiff  ThreADder ShReADor OpenMP-ShRedDer OpenMP-ShaRD OpenMP-Shadowed-Read-Derivatives 
  OpenMP shared memory automatic differentiator
SPREAD	  Shared PaRallEl Automatic Differentiation
PARADE	  PARallel Automatic DiffErentiation OpenMP-ParAD
  """

  def __init__(self):
    self.vars = {}
    self.readExpressions = set()
    self.writeExpressions = set()
    self.SLICE = sympy.Symbol("SLICE")
    self.GLOBAL = sympy.Symbol("GLOBAL")

  def hasSafeReadAccess(self, var):
    """
    Return True if the adjoint of var can be shared. This is the case if in the primal
     - var is written globally, without index. This can only be safe if only one thread can reach this statement.
     - the set of expressions from which var is read is a subset of set of expressions to which any variable is written,
       and all variables appearing in these expressions are not modified.
    """
    allWriteIndices = {item.args for item in self.writeExpressions}
    varReadExpressions = set(filter(lambda x: x.func == var.function, self.readExpressions))
    varWriteExpressions = set(filter(lambda x: x.func == var.function, self.writeExpressions))
    varReadIndices = set(item.args for item in varReadExpressions)
    varWriteIndices = set(item.args for item in varWriteExpressions)
    if(self.GLOBAL in varWriteIndices):
      return True
    if(self.SLICE in varReadIndices):
      # We currently do not do anything smart for slices, assume that this read is unsafe.
      return False
    for indexFunction in var.indexFunctions:
      if not (self.isReadOnly(indexFunction)):
        return False
    return varReadIndices.issubset(allWriteIndices)

  def isReadOnly(self, var):
    """
    Return True if var is never written
    """
    varWriteExpressions = set(filter(lambda x: x.func == var.function, self.writeExpressions))
    return len(varWriteExpressions) == 0

  def isWriteOnly(self, var):
    """
    Return True if var is never read
    """
    varReadExpressions = set(filter(lambda x: x.func == var.function, self.readExpressions))
    return len(varReadExpressions) == 0

  def visitName(self, node, writeAccess = False, readAccess = True):
    """
    Every time we encounter a node of type Name, we found a reference
    to a variable. Check if it is already in the set of known variables,
    and add it if not. Also, add all expressions that are used to index
    this variable for eiher read or write access.
    """
    varname = node.tostr()
    if not (varname in self.vars):
      self.vars[varname] = VariableProperty(varname)
    expression = self.vars[varname].function(self.GLOBAL)
    if(writeAccess):
      self.writeExpressions.add(expression)
    if(readAccess):
      self.readExpressions.add(expression)

  def visitIndexNode(self, node):
    """
    Visit the expression inside a partial reference, e.g. the "i-1,2"
    in "u(i-1,2)". We support multi-dimensional arrays, but do not
    currently attempt to analyse slices, e.g. "1:2" or even "1:2:10".
    """
    indexexpr = []
    indexfunc = set()
    if(type(node) == f2003.Name):
      # a variable reference, e.g. "i"
      self.visitName(node)
      indexexpr = self.vars[node.tostr()].function()
      indexfunc.add(self.vars[node.tostr()])
    elif(type(node) == f2003.Int_Literal_Constant):
      # a constant, e.g. "2"
      indexexpr = int(node.tostr())
    elif(type(node) == f2003.Level_2_Expr):
      # an expression with an infix operator, e.g. "i+2"
      ops = { "+": operator.add,
              "-": operator.sub,
              '*': operator.mul,
              '/': operator.truediv,
              '%': operator.mod }
      leftexpr, leftfunc = self.visitIndexNode(node.items[0])
      rightexpr, rightfunc = self.visitIndexNode(node.items[2])
      indexexpr = ops[node.items[1]](leftexpr, rightexpr)
      indexfunc = leftfunc.union( rightfunc )
    elif(type(node) == f2003.Section_Subscript_List):
      # multi-dimensional array access, e.g. "u(i,j)"
      for subscript in node.items:
        thisexpr, thisfunc = self.visitIndexNode(subscript) 
        indexexpr.append( thisexpr )
        indexfunc.update( thisfunc )
      indexexpr = tuple(indexexpr)
    elif(type(node) == f2003.Subscript_Triplet):
      # array slicing, e.g. u(1:5). No analysis done, assume that
      # we access no element, all elements, or any other subset.
      indexexpr = self.SLICE
    elif(type(node) == f2003.Part_Ref):
      indexexpr, indexfunc = self.visitPartRef(node)
    else:
      raise Exception("Unsupported index expression: %s"%(mode.tostr()))
    return indexexpr, indexfunc

  def visitPartRef(self, node, writeAccess = False):
    """
    Visit a partial reference, e.g. "u(i)" or "u(i-1,1:3)".
    Assemble a sympy expression from the index AST, and add
    it to the set of index expressions for that variable.
    For example: "i-1" will be added to the set of index
    expressions of "u". The writeAccess flag determines if
    this is a write or read access.
    """
    var = node.items[0]
    varname = var.tostr()
    index = node.items[1]
    indexExpression, indexFunctions = self.visitIndexNode(index)
    self.visitNode(index) # visit the node again, this time also analysing read/write of all vars used within the node.
    self.visitName(var, readAccess = False, writeAccess = False)
    self.vars[varname].addIndexFunctions(indexFunctions)
    expression = self.vars[varname].function(indexExpression)
    indexFunctions.add(self.vars[varname])
    if(writeAccess):
      self.writeExpressions.add(expression)
    else:
      self.readExpressions.add(expression)
    return expression, indexFunctions

  def visitAssignment(self, node):
    """
    Visit an assignment. The left hand side must be a Name or PartRef,
    the right hand side can be any node.
    """
    leftSide = node.items[0]
    rightSide = node.items[2]
    if(type(leftSide) == f2003.Name):
      self.visitName(leftSide, writeAccess = True)
    if(type(leftSide) == f2003.Part_Ref):
      self.visitPartRef(leftSide, writeAccess = True)
    else:
      raise Exception("Assignment with unsupported left side: %s"%(node.tostr()))
    self.visitNode(rightSide)

  def visitNode(self, node):
    """
    Recursively go through the AST and find all read and write accesses to
    variables.
    """
    children = []
    if hasattr(node, "content"):
      children = node.content
    elif hasattr(node, "items"):
      children = node.items
    elif type(node) in (tuple, list):
      children = node
    for child in children:
      if(type(child)==f2003.Assignment_Stmt):
        # Visit an assignment statement, e.g. "a = b + c"
        self.visitAssignment(child)
      elif(type(child) == f2003.Part_Ref):
        # Visit a partial reference, e.g. "u(i)" or "u(i-1,1:3)".
        # If we encounter this outside an assignment statement, then it
        # must be a read access.
        self.visitPartRef(child, writeAccess = False)
      elif(type(child) == f2003.Name):
        # If we encounter a name outside an assignment or partial reference,
        # then it must be a read access to the entire variable.
        self.visitName(child)
      else:
        self.visitNode(child)

