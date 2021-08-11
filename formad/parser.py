import formad.ompparser as omp
from formad.scope import Scope
from fparser.common.readfortran import FortranStringReader
from fparser.two.parser import ParserFactory
from fparser.two import Fortran2003
import sympy
import operator
import z3
import logging
#logging.basicConfig(level=logging.DEBUG)
from enum import Enum, auto
import re

class Answer(Enum):
  '''
  Enum to model answers that could be yes, no, or maybe (unknown).
  '''
  yes = auto()
  no = auto()
  maybe = auto()

class Preprocessor:
  def __init__(self, filename, adjointstmts):
    '''
    Helper function that reads a Fortran source file, and inserts statement
    labels to allow the parser to keep track of line numbers.
    '''
    out = []
    staged = []
    with open(filename, 'r') as fp:
      for i, line in enumerate(fp):
        linenumber = i+1
        nonwhite = re.findall("\s*(\S)", line)
        if((not nonwhite in (None, [])) and (not nonwhite[0] in ("!", "&"))):
          out += staged
          staged = []
          out.append(str(linenumber) + " " + line)
        elif(omp.OpenMPParser.ispragma(line)):
          out += staged
          staged = []
          out.append(line.rstrip() + f", line({linenumber})\n")
        else:
          out.append(line)
        if(linenumber in adjointstmts):
          staged += adjointstmts[linenumber]
    self.source = "".join(out)

class ParloopFinder:
  '''
  This class provides infrastructure to go through an entire Fortran source
  file, and extract all OpenMP parallel loops from it.
  '''
  def __init__(self, source, querylinenumber):
    logging.debug(f"Creating parser")
    self.parser, self.parloop, self.pragma = self.find_parloop(source, querylinenumber)

  
  def find_parloop(self, source, querylinenumber):
    '''
    Find do-loop with OpenMP pragma. A match is only returned if it
    starts at the queried line number.
    '''
    def __find_parloops_walker(node):
      '''
      Recursive helper function for findparloops
      '''
      children = []
      if hasattr(node, "content"):
        children = node.content
      elif hasattr(node, "items"):
        children = node.items
      for child in children:
        if(type(child) == Fortran2003.Comment and omp.OpenMPParser.ispragma(child.tostr())):
          parser = omp.OpenMPParser(child.tostr())
          if(parser.linenumber == querylinenumber):
            return parser, node, child
        ret = __find_parloops_walker(child)
        if(ret != None):
          return ret
      return None
    reader = FortranStringReader(source, ignore_comments=False)
    f_parser = ParserFactory().create(std="f2003")
    ast = f_parser(reader)
    return __find_parloops_walker(ast)

class VariableInstance:
  '''
  A VariableInstance corresponds to a Variable during a certain portion
  of the parsed code: Every time a Variable is modified, a new instance
  is created.
  '''
  def __init__(self, varname, numDims, implicitCounter = None):
    logging.debug(f"Creating VariableInstance object {varname} with iCounter {implicitCounter}")
    self.name = varname
    self.implicitCounter = implicitCounter
    if(self.implicitCounter):
      numDims += 1
    self._function = z3.Function(varname,z3.RealSort(),*(z3.RealSort(),)*numDims)

  def __str__(self):
    return self.name

  def function(self, *exprs):
    if(self.implicitCounter):
      exprs += (self.implicitCounter.currentInstance.function(),)
    logging.debug(f"Calling {self.name} with exprs {exprs}")
    return self._function(*exprs)

class Variable:
  '''
  Class to hold properties of a variable in the parsed code
  '''
  def __init__(self, varname, numDims, implicitCounter = None, isCounter = False):
    logging.debug(f"Creating Variable object {varname} with {numDims} dimensions")
    self.name = varname
    self.instances = []
    self.writeExpressions = {}
    self.readExpressions = {}
    self.numDims = numDims
    self.implicitCounter = implicitCounter
    self.isCounter = False
    self.pushInstance()
    self.isCounter = isCounter
    self.currentInstance = self.instances[0]

  def pushExpression(self, indexExpression, writeAccess, controlPath):
    if(writeAccess == Answer.yes):
      logging.debug(f"pushing write {indexExpression} to {self.name} under path {controlPath}")
      if not (repr(controlPath) in self.writeExpressions):
        self.writeExpressions[repr(controlPath)] = set()
      self.writeExpressions[repr(controlPath)].add(indexExpression)
    else:
      logging.debug(f"pushing read {indexExpression} to {self.name} under path {controlPath}")
      if not (repr(controlPath) in self.readExpressions):
        self.readExpressions[repr(controlPath)] = set()
      self.readExpressions[repr(controlPath)].add(indexExpression)

  def pushInstance(self, forcePush = False):
    varname = f"{self.name}_{len(self.instances)}"
    if(not self.isCounter or forcePush):
      logging.debug(f"pushing instance {varname}")
      self.instances.append(VariableInstance(varname, self.numDims, self.implicitCounter))
      self.currentInstance = self.instances[-1]

  def __str__(self):
    return f"Variable {self.name} with instances ("+", ".join([str(x) for x in self.instances])+")\n  read expressions: ("+", ".join([f"{str(x)}:{self.readExpressions[x]}" for x in self.readExpressions])+")\n  write expressions: ("+", ".join([f"{str(x)}:{self.writeExpressions[x]}" for x in self.writeExpressions]) + ")"

class ParloopParser:
  '''
  This class provides infrastructure to parse an individual OpenMP-parallel
  loop and extract information from it.
  '''
  def __init__(self, ompparser, parloop):
    self.vars = {}
    self.controlPath = Scope(None)
    self.ompparser = ompparser
    # hack to determine name of loop counter variable
    self.loopCounterName = parloop.content[1].items[1].items[1][0].tostr()
    self.vars[self.loopCounterName] = Variable(self.loopCounterName, 0, isCounter = True)
    self.visitNode(parloop)

  def visitName(self, node, writeAccess = Answer.no, indexExpression = None):
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
      implicitCounter = None
      if(self.ompparser.getscope(varname) != omp.Scopes.shared and varname != self.loopCounterName):
        implicitCounter = self.vars[self.loopCounterName]
      self.vars[varname] = Variable(varname, numDims, implicitCounter)
    elif (writeAccess in (Answer.yes, Answer.maybe)):
      # we have seen this variable before, but it may be modified,
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
    elif(type(node) == Fortran2003.Level_2_Unary_Expr):
      assert(len(node.items) == 2)
      if(node.items[0] == "-"):
        logging.debug(f"visiting unary -{node.items[1]}")
        negexpr = self.visitIndexNode(node.items[1])
        assert(len(negexpr) == 1)
        indexexpr = (operator.neg(negexpr[0]),)
      else:
        assert(node.items[0] == "+")
        logging.debug(f"visiting unary +{node.items[1]}")
        posexpr = self.visitIndexNode(node.items[1])
        assert(len(posexpr) == 1)
        indexexpr = (operator.pos(posexpr[0]),)
    elif(type(node) in (Fortran2003.Level_2_Expr, Fortran2003.Add_Operand)):
      logging.debug(f"visiting IndexNode/Level2 node {node.tostr()}")
      assert(len(node.items)==3)
      # an expression with an infix operator, e.g. "i+2"
      ops = { "+": operator.add,
              "-": operator.sub,
              '*': operator.mul,
              '/': operator.truediv,
              '%': operator.mod }
      leftexpr = self.visitIndexNode(node.items[0])
      rightexpr = self.visitIndexNode(node.items[2])
      logging.debug(f"visiting IndexNode/Level2 node {node.tostr()} with items {node.items}")
      logging.debug(f"  has leftexpr {leftexpr}")
      logging.debug(f"  has rightexpr {rightexpr} from {node.items[2]} type {type(node.items[2])}")
      assert(len(leftexpr) == 1 and len(rightexpr) == 1)
      indexexpr = (ops[node.items[1]](leftexpr[0], rightexpr[0]),)
      logging.debug(f"  has op {node.items[1]}")
    elif(type(node) == Fortran2003.Section_Subscript_List):
      logging.debug(f"visiting IndexNode/SectionSubscriptList node {node}")
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
    elif(type(node) == Fortran2003.Parenthesis):
      logging.debug(f"visiting IndexNode/Parenthesis node {node.tostr()}")
      assert(len(node.items)==3 and node.items[0] == "(" and node.items[2] == ")")
      indexexpr = self.visitIndexNode(node.items[1])
    else:
      raise Exception("Unsupported index expression: %s (type %s)"%(str(node),str(type(node))))
    return indexexpr

  def visitPartRef(self, node, writeAccess = Answer.no):
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
    if(writeAccess == Answer.yes):
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
      self.visitName(leftSide, writeAccess = Answer.yes)
    elif(type(leftSide) == Fortran2003.Part_Ref):
      self.visitPartRef(leftSide, writeAccess = Answer.yes)
    else:
      raise Exception(f"Assignment with unsupported left side: {leftSide.tostr()} (type {type(leftSide)})")
    self.visitNode(rightSide)

  def visitLoopControl(self, node):
    '''
    Visit the loop control (the part that defines loop counter, bounds, and
    stride). This is mostly to spawn a new instance of the loop counter, since
    it is being modified.
    '''
    # we need to skip the very first loop we'll visit, since it is the
    # parallel loop, and its counter is handled differently.
    loopCounter = node.items[1][0]
    self.visitName(loopCounter, writeAccess = Answer.yes)

  def visitDoLoop(self, node):
    changedVars = self.visitNodeDryRun(node)
    for var in changedVars:
      if(var in self.vars):
        self.vars[var].pushInstance()
    for item in node.content:
      self.visitNode(item)
    for var in changedVars:
      self.vars[var].pushInstance()

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
                         Fortran2003.Nonlabel_Do_Stmt,
                         Fortran2003.End_Do_Stmt,
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
                         Fortran2003.Level_2_Unary_Expr,
                         Fortran2003.Cycle_Stmt,
                         Fortran2003.Call_Stmt,
                         Fortran2003.Parenthesis,
                         Fortran2003.Level_4_Expr,
                         Fortran2003.And_Operand,
                       )
    logging.debug(f"visiting node {node}")
    if(type(node)==Fortran2003.Assignment_Stmt):
      # Visit an assignment statement, e.g. "a = b + c"
      self.visitAssignment(node)
    elif(type(node) == Fortran2003.Actual_Arg_Spec_List):
      # Visit the arguments of a subroutine call. They may get overwritten in
      # the subroutine, so we start new instances for affected variables. On
      # the other hand, they might not get overwritten, so we can not add the
      # index expressions for them to our "safe" expressions.
      for arg in node.items:
        if(type(arg) == Fortran2003.Name):
          self.visitName(arg, writeAccess = Answer.maybe)
        elif(type(arg) == Fortran2003.Part_Ref):
          self.visitPartRef(node, writeAccess = Answer.maybe)
    elif(type(node) == Fortran2003.Part_Ref):
      # Visit a partial reference, e.g. "u(i)" or "u(i-1,1:3)".
      # If we encounter this outside an assignment statement, then it
      # must be a read access.
      self.visitPartRef(node, writeAccess = Answer.no)
    elif(type(node) == Fortran2003.Name):
      # If we encounter a name outside an assignment or partial reference,
      # then it must be a read access to the entire variable.
      self.visitName(node)
    elif(type(node) == Fortran2003.Block_Nonlabel_Do_Construct):
      # Loops require special handling, since we may later discover that part
      # of the loop body will overwrite a variable, which might have happened
      # in a previous iteration before we reach the textual representation of a
      # variable. We need to look ahead and find all variables that will be
      # modified, and create new instances for them right from the start.
      self.visitDoLoop(node)
    elif(type(node) == Fortran2003.If_Then_Stmt):
      # We start branching
      # Get the current instance of all variables, and store it in the current scope
      curInstances = {varname:self.vars[varname].currentInstance for varname in self.vars}
      self.controlPath.props["instances"] = curInstances
      self.controlPath.props["changedVars"] = set()
      # TODO new instance at loop start
      # Then, create a new scope for the if branch and make it the new "current" scope
      curScope = Scope(self.controlPath)
      self.controlPath = curScope
    elif(type(node) in (Fortran2003.Else_If_Stmt,
                        Fortran2003.Else_Stmt,
                       )):
      # We are inside a branching construct, and enter a different branch
      # Get the current instance of all variables. These may have been created by
      # another branch, which we have just left. We remember that they have been
      # changed (we need this information at the endif/enddo statement), and revert
      # the instance back to that of the parent scope.
      curInstances = {varname:self.vars[varname].currentInstance for varname in self.vars}
      parentScope = self.controlPath.parent
      curScope = Scope(parentScope)
      self.controlPath = curScope
      parentInstances = parentScope.props["instances"]
      for varname in curInstances:
        if(not varname in parentInstances):
          # We have discovered a new variable inside a branch, and the parent
          # did therefore not yet have an instance for it. By definition, the
          # instance that was valid before we saw the variable for the first
          # time is the initial instance.
          parentInstances[varname] = self.vars[varname].instances[0]
        if(curInstances[varname] != parentInstances[varname]):
          # The more "conventional" case: a variable that already had an
          # instance, and we created yet another instance in the previous
          # branch. Revert back to the parent instance now.
          parentScope.props["changedVars"].add(varname) 
          self.vars[varname].currentInstance = parentInstances[varname]
    elif(type(node) == Fortran2003.End_If_Stmt):
      # We finish branching (merge of paths)
      self.controlPath = self.controlPath.parent
      # If a variable has created a new instance in any branch, we need to
      # create yet another instance of it now.
      for varname in self.controlPath.props["changedVars"]:
        self.vars[varname].pushInstance()
    elif(type(node) == Fortran2003.Loop_Control):
      self.visitLoopControl(node)
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

  def visitNodeDryRun(self, node):
    """
    Recursively go through an AST part and find all variables that may be
    modified, without taking any other action (not pushing instances or
    expressions).
    """
    changedVarNames = set()
    if(type(node) == Fortran2003.Assignment_Stmt):
      # Visit an assignment statement, e.g. "a = b + c"
      leftSide = node.items[0]
      if(type(leftSide) == Fortran2003.Name):
        changedVarNames.add(str(leftSide))
      elif(type(leftSide) == Fortran2003.Part_Ref):
        changedVarNames.add(str(leftSide.items[0]))
    elif(type(node) == Fortran2003.Actual_Arg_Spec_List):
      # Visit the arguments of a subroutine call. They may get overwritten in
      # the subroutine, so we start new instances for affected variables. On
      # the other hand, they might not get overwritten, so we can not add the
      # index expressions for them to our "safe" expressions.
      for arg in node.items:
        if(type(arg) == Fortran2003.Name):
          changedVarNames.add(str(arg))
        elif(type(arg) == Fortran2003.Part_Ref):
          changedVarNames.add(str(arg.items[0]))
    elif(type(node) == Fortran2003.Loop_Control):
      # we need to skip the very first loop we'll visit, since it is the
      # parallel loop, and its counter is handled differently.
      loopCounter = node.items[1][0]
      changedVarNames.add(str(loopCounter))
    children = []
    if hasattr(node, "content"):
      children = node.content
    elif hasattr(node, "items"):
      children = node.items
    elif type(node) in (tuple, list):
      children = node
    for child in children:
      changedVarNames = changedVarNames.union(self.visitNodeDryRun(child))
    return changedVarNames
