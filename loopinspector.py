from fparser.two.Fortran2003 import Comment
from fparser.common.readfortran import FortranFileReader
from fparser.two.parser import ParserFactory

class varscope:
  def __init__(self,read,write,excl):
    self.readindices = read
    self.writeindices = write
    self.exclusiveread = excl

def getusedvars(ast):
  """
  Get list of all variables that are read or written within this piece
  of ast, along with the list of indices.
  Example input: r[i] += u[i-1]+u[i]
  """
  usedvars = {}
  usedvars['u'] = varscope(('i-1','i'),None,False)
  usedvars['r'] = varscope(('i'),('i'),True)
  usedvars['a'] = varscope(('0'),('0'),False)
  usedvars['x'] = varscope(('0'),('0'),False)
  # TODO use Z3 with expression, loop strides/bounds etc to determine exclusive read
  return usedvars

def getparloops_walker(children):
    '''
    Find loops in program that are marked with !$omp
    '''
    local_list = []
    appendNext = False
    for child in children:
        if(appendNext):
            local_list.append(child)
            appendNext = False
        if type(child) == Comment:
            if(child.tostr() == '!$omp'):
                appendNext = True

        # Depending on their level in the tree produced by fparser2003,
        # some nodes have children listed in .content and some have them
        # listed under .items. If a node has neither then it has no
        # children.
        if hasattr(child, "content"):
            local_list += getparloops_walker(child.content)
        elif hasattr(child, "items"):
            local_list += getparloops_walker(child.items)
    return local_list

def getparloops(filename):
  reader = FortranFileReader(filename, ignore_comments=False)
  f_parser = ParserFactory().create(std="f2003")
  ast = f_parser(reader)
  return getparloops_walker(ast.content)

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
