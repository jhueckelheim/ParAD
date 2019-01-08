import fparser.two.Fortran2003 as f2003
from fparser.common.readfortran import FortranFileReader
from fparser.two.parser import ParserFactory
import ompparser

class varscope:
  def __init__(self, exclusive, loopvar):
    self.exclusiveread = exclusive
    self.loopvariable = loopvar
  def __repr__(self):
    return "%s %s"%(self.exclusiveread, self.loopvariable)

def __getusedvars_walker__(node):
  """
  Recursive helper function for getusedvars
  """
  usedvars = {}
  children = []
  if hasattr(node, "content"):
    children = node.content
  elif hasattr(node, "items"):
    children = node.items
  elif type(node) in (tuple, list):
    children = node
  for child in children:
    if(type(child) == f2003.Name):
      usedvars[child.tostr()] = varscope(exclusive=False, loopvar=False)
    usedvars.update(__getusedvars_walker__(child))
  return usedvars

def getusedvars(node):
  """
  Get list of all variables that are read or written within this piece
  of ast, along with the list of indices.
  Example input: r[i] += u[i-1]+u[i]
  """
  usedvars = __getusedvars_walker__(node)
  # hack to determine loop counter, which is default private
  do_stmt = node.content[1]
  loop_control = do_stmt.items[1]
  counter_declaration = loop_control.items[1][0]
  usedvars[counter_declaration.tostr()] = varscope(exclusive=False, loopvar=True)
  # TODO use Z3 with expression, loop strides/bounds etc to determine exclusive read
  return usedvars

def __getparloops_walker__(node):
  '''
  Recursive helper function for getparloops
  '''
  local_list = []
  children = []
  if hasattr(node, "content"):
    children = node.content
  elif hasattr(node, "items"):
    children = node.items
  for child in children:
    if(type(child) == f2003.Comment and ompparser.ispragma(child.tostr())):
      local_list.append(node)
    local_list += __getparloops_walker__(child)
  return local_list

def getparloops(filename):
  '''
  Find do-loops with OpenMP pragma
  '''
  reader = FortranFileReader(filename, ignore_comments=False)
  f_parser = ParserFactory().create(std="f2003")
  ast = f_parser(reader)
  return __getparloops_walker__(ast)

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
