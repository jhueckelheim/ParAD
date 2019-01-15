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

  def makeLoopCounter(self):
    self.loopCounter = True

class ReadWriteInspector:
  """
  Inspector that finds read and write access within an AST.
  """

  def __init__(self):
    self.vars = {}
    self.readExpressions = set()
    self.writeExpressions = set()
    self.SLICE = sympy.Symbol("SLICE")
    self.GLOBAL = sympy.Symbol("GLOBAL")

  def hasSafeReadAccess(self, var):
    allWriteIndices = {item.args for item in self.writeExpressions}
    varReadExpressions = set(filter(lambda x: x.func == var.function, self.readExpressions))
    varWriteExpressions = set(filter(lambda x: x.func == var.function, self.writeExpressions))
    varReadIndices = set(item.args for item in varReadExpressions)
    varWriteIndices = set(item.args for item in varWriteExpressions)
    if(self.GLOBAL in varWriteIndices):
      return True
    elif(self.SLICE in varReadIndices):
      return False
    else:
      return varReadIndices.issubset(allWriteIndices)

  def isReadOnly(self, var):
    varWriteExpressions = set(filter(lambda x: x.func == var.function, self.writeExpressions))
    return len(varWriteExpressions) == 0

  def isWriteOnly(self, var):
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
    if(type(node) == f2003.Name):
      # a variable reference, e.g. "i"
      self.visitName(node)
      indexexpr = self.vars[node.tostr()].function()
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
      indexexpr = ops[node.items[1]](self.visitIndexNode(node.items[0]), self.visitIndexNode(node.items[2]))
    elif(type(node) == f2003.Section_Subscript_List):
      # multi-dimensional array access, e.g. "u(i,j)"
      for subscript in node.items:
        indexexpr.append( self.visitIndexNode(subscript) )
      indexexpr = tuple(indexexpr)
    elif(type(node) == f2003.Subscript_Triplet):
      # array slicing, e.g. u(1:5). No analysis done, assume that
      # we access no element, all elements, or any other subset.
      indexexpr = self.SLICE
    elif(type(node) == f2003.Part_Ref):
      indexexpr = self.visitPartRef(node)
    else:
      raise Exception("Unsupported index expression: %s"%(mode.tostr()))
    return indexexpr

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
    indexExpression = self.visitIndexNode(index)
    self.visitNode(index) # visit the node again, this time also analysing read/write of all vars used within the node.
    self.visitName(var, readAccess = False, writeAccess = False)
    expression = self.vars[varname].function(indexExpression)
    if(writeAccess):
      self.writeExpressions.add(expression)
    else:
      self.readExpressions.add(expression)
    return expression

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


# discover all touched variables that are not declared inside the parallel region.
# how to deal with shadowing correctly, e.g. in the following, the externally visible a has exclusive read:
# double a;
# parallel for(i=0;i<n;i++) {
#   a[i] += b[i];
#   {
#     double a = c;
#     b[i]+=a;
#   }
# }
# if we ignore this special case, we underestimate the exclusive read set, which is safe.
#
# also, assume all subroutines/functions are side-effect free, and there is no aliasing
#
# Another complication for C: Several distinct variables may have the same name if they appear in
# different places. This could trip up the equivalence analysis of index expressions.
