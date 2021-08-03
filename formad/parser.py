import formad.ompparser as ompparser
from formad.scope import Scope
from fparser.common.readfortran import FortranFileReader
from fparser.two.parser import ParserFactory
from fparser.two import Fortran2003
import sympy
import operator
import z3
import logging
#logging.basicConfig(level=logging.DEBUG)

class ParloopFinder:
  '''
  This class provides infrastructure to go through an entire Fortran source
  file, and extract all OpenMP parallel loops from it.
  '''
  def __init__(self, filename):
    logging.debug(f"Creating parser for file {filename}")
    self.parloops = self.find_parloops_file(filename)
  
  def find_parloops_file(self, filename):
    '''
    Find do-loops with OpenMP pragma
    '''
    def __find_parloops_walker(node):
      '''
      Recursive helper function for findparloops
      '''
      local_list = []
      children = []
      if hasattr(node, "content"):
        children = node.content
      elif hasattr(node, "items"):
        children = node.items
      for child in children:
        if(type(child) == Fortran2003.Comment and ompparser.ispragma(child.tostr())):
          local_list.append(node)
        local_list += __find_parloops_walker(child)
      return local_list
    reader = FortranFileReader(filename, ignore_comments=False)
    f_parser = ParserFactory().create(std="f2003")
    ast = f_parser(reader)
    return __find_parloops_walker(ast)

class VariableInstance:
  '''
  A VariableInstance corresponds to a Variable during a certain portion
  of the parsed code: Every time a Variable is modified, a new instance
  is created.
  '''
  def __init__(self, varname, numDims):
    logging.debug(f"Creating VariableInstance object {varname}")
    self.name = varname
    self.function = z3.Function(varname,z3.RealSort(),*(z3.RealSort(),)*numDims)

  def __str__(self):
    return self.name

class Variable:
  '''
  Class to hold properties of a variable in the parsed code
  '''
  def __init__(self, varname, numDims):
    logging.debug(f"Creating Variable object {varname} with {numDims} dimensions")
    self.name = varname
    self.instances = []
    self.writeExpressions = {}
    self.readExpressions = {}
    self.numDims = numDims
    self.pushInstance()

  def pushExpression(self, indexExpression, writeAccess, controlPath):
    if(writeAccess):
      logging.debug(f"pushing write {indexExpression} to {self.name} under path {controlPath}")
      if not (repr(controlPath) in self.writeExpressions):
        self.writeExpressions[repr(controlPath)] = set()
      self.writeExpressions[repr(controlPath)].add(indexExpression)
    else:
      logging.debug(f"pushing read {indexExpression} to {self.name} under path {controlPath}")
      if not (repr(controlPath) in self.readExpressions):
        self.readExpressions[repr(controlPath)] = set()
      self.readExpressions[repr(controlPath)].add(indexExpression)

  def pushInstance(self):
    varname = f"{self.name}_{len(self.instances)}"
    logging.debug(f"pushing instance {varname}")
    self.instances.append(VariableInstance(varname, self.numDims))

  def __str__(self):
    return f"Variable {self.name} with instances ("+", ".join([str(x) for x in self.instances])+")\n  read expressions: ("+", ".join([f"{str(x)}:{self.readExpressions[x]}" for x in self.readExpressions])+")\n  write expressions: ("+", ".join([f"{str(x)}:{self.writeExpressions[x]}" for x in self.writeExpressions]) + ")"

  @property
  def currentInstance(self):
    return self.instances[-1]

  def popInstance(self):
    return self.instances.pop()

class ParloopParser:
  '''
  This class provides infrastructure to parse an individual OpenMP-parallel
  loop and extract information from it.
  '''
  def __init__(self, parloop):
    self.vars = {}
    self.controlPath = Scope(None)
    self.visitNode(parloop)
    # hack to determine name of loop counter variable
    self.loopCounter = self.vars[parloop.content[1].items[1].items[1][0].tostr()]

  def visitName(self, node, writeAccess = False, indexExpression = None):
    """
    Visitor for references to variables
    """
    varname = node.tostr()
    logging.debug(f"visiting Name node for {varname} with write={writeAccess} and idx={indexExpression}")
    numDims = 0
    if(indexExpression != None):
      numDims = len(indexExpression)
    if not (varname in self.vars):
      # we have discovered a new variable
      self.vars[varname] = Variable(varname, numDims)
    elif (writeAccess):
      # we have seen this variable before, but it is being modified,
      # so we start a new instance here.
      self.vars[varname].pushInstance()
    if(indexExpression != None):
      self.vars[varname].pushExpression(indexExpression, writeAccess, self.controlPath)

  def visitIndexNode(self, node):
    """
    Visit the expression inside a partial reference, e.g. the "i-1,2"
    in "u(i-1,2)".
    """
    if(type(node) == Fortran2003.Name):
      # a variable reference, e.g. "i"
      logging.debug(f"visiting IndexNode/Name node {node.tostr()}")
      self.visitName(node)
      indexexpr = (self.vars[node.tostr()].currentInstance.function(),)
    elif(type(node) == Fortran2003.Int_Literal_Constant):
      logging.debug(f"visiting IndexNode/Literal node {node.tostr()}")
      # a constant, e.g. "2"
      indexexpr = (int(node.tostr()),)
    elif(type(node) == Fortran2003.Level_2_Expr):
      logging.debug(f"visiting IndexNode/Level2 node {node.tostr()}")
      # an expression with an infix operator, e.g. "i+2"
      ops = { "+": operator.add,
              "-": operator.sub,
              '*': operator.mul,
              '/': operator.truediv,
              '%': operator.mod }
      leftexpr = self.visitIndexNode(node.items[0])
      rightexpr = self.visitIndexNode(node.items[2])
      indexexpr = (ops[node.items[1]](leftexpr[0], rightexpr[0]),)
    elif(type(node) == Fortran2003.Section_Subscript_List):
      logging.debug(f"visiting IndexNode/SectionSubscriptList node {node.tostr()}")
      # multi-dimensional array access, e.g. "u(i,j)"
      indexexpr = []
      for subscript in node.items:
        thisexpr = self.visitIndexNode(subscript) 
        indexexpr.append( thisexpr[0] )
      indexexpr = tuple(indexexpr)
    elif(type(node) == Fortran2003.Subscript_Triplet):
      logging.debug(f"visiting IndexNode/SubscriptTriplet node {node.tostr()}")
      # array slicing, e.g. u(1:5). No analysis done, assume that
      # we access no element, all elements, or any other subset.
      indexexpr = (self.SLICE,)
    elif(type(node) == Fortran2003.Part_Ref):
      logging.debug(f"visiting IndexNode/PartRef node {node.tostr()}")
      indexexpr = (self.visitPartRef(node),)
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
    logging.debug(f"visiting PartRef node {node.tostr()} with write={writeAccess}")
    var = node.items[0]
    varname = var.tostr()
    index = node.items[1]
    indexExpression = self.visitIndexNode(index)
    self.visitNode(index) # visit the node again, this time also analysing read/write of all vars used within the node.
    self.visitName(var, writeAccess, indexExpression)
    self.vars[varname].pushExpression(indexExpression, writeAccess, self.controlPath)
    return self.vars[varname].currentInstance.function(*indexExpression)

  def visitAssignment(self, node):
    """
    Visit an assignment. The left hand side must be a Name or PartRef,
    the right hand side can be any node.
    """
    logging.debug(f"visiting assignment {node.tostr()}")
    leftSide = node.items[0]
    rightSide = node.items[2]
    if(type(leftSide) == Fortran2003.Name):
      self.visitName(leftSide, writeAccess = True)
    if(type(leftSide) == Fortran2003.Part_Ref):
      self.visitPartRef(leftSide, writeAccess = True)
    else:
      raise Exception("Assignment with unsupported left side: %s"%(node.tostr()))
    self.visitNode(rightSide)

  def visitNode(self, node):
    """
    Recursively go through the AST and find all read and write accesses to
    variables.
    """
    # While traversing the AST, we encounter many nodes that are not interesting
    # for this analysis, and nothing is done when we encounter them. Note that
    # we still visit the children of these nodes, and they may very well be
    # important. For example, we do not care about the Block nodes of branches
    # or loops, since our analysis instead looks out for the start & end
    # statements that are always contained in these blocks.
    ignoredNodeTypes = ( Fortran2003.Comment,
                         Fortran2003.Loop_Control,
                         Fortran2003.Block_Nonlabel_Do_Construct,
                         Fortran2003.If_Construct,
                         Fortran2003.Section_Subscript_List,
                         type(None),
                         type([]),
                         type(()),
                         type(""),
                         Fortran2003.Int_Literal_Constant,
                         Fortran2003.Real_Literal_Constant,
                         Fortran2003.Add_Operand,
                         Fortran2003.Level_2_Expr,
                       )
    logging.debug(f"visiting node {node}")
    if(type(node)==Fortran2003.Assignment_Stmt):
      # Visit an assignment statement, e.g. "a = b + c"
      self.visitAssignment(node)
    elif(type(node) == Fortran2003.Part_Ref):
      # Visit a partial reference, e.g. "u(i)" or "u(i-1,1:3)".
      # If we encounter this outside an assignment statement, then it
      # must be a read access.
      self.visitPartRef(node, writeAccess = False)
    elif(type(node) == Fortran2003.Name):
      # If we encounter a name outside an assignment or partial reference,
      # then it must be a read access to the entire variable.
      self.visitName(node)
    elif(type(node) in (Fortran2003.If_Then_Stmt,
                        Fortran2003.Nonlabel_Do_Stmt,
                       )):
      # We start branching
      curScope = Scope(self.controlPath)
      self.controlPath = curScope
    elif(type(node) in (Fortran2003.Else_If_Stmt,
                        Fortran2003.Else_Stmt,
                       )):
      # We are inside a branching construct, and enter a different branch
      curScope = Scope(self.controlPath.parent)
      self.controlPath = curScope
    elif(type(node) in (Fortran2003.End_If_Stmt,
                        Fortran2003.End_Do_Stmt,
                       )):
      # We finish branching (merge of paths)
      self.controlPath = self.controlPath.parent
    elif not (type(node) in ignoredNodeTypes):
      # If we encounter other nodes that are not in the white list of
      # unimportant node types, we print an error message (but continue
      # execution). If this happens, you probably want to double-check if
      # this node type is important for this analysis (and develop some theory
      # for it), or else, add it to the white list.
      logging.error(f"other node type: {type(node)}\n{node}")
    children = []
    if hasattr(node, "content"):
      children = node.content
    elif hasattr(node, "items"):
      children = node.items
    elif type(node) in (tuple, list):
      children = node
    for child in children:
      self.visitNode(child)
