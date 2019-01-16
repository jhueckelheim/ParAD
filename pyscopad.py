import ompparser
import loopinspector
import ompdiff
import sys
from fparser.common.readfortran import FortranFileReader, FortranStringReader
from fparser.two.parser import ParserFactory
import fparser.two.Fortran2003 as f2003

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

def getparloops_file(filename):
  '''
  Find do-loops with OpenMP pragma
  '''
  reader = FortranFileReader(filename, ignore_comments=False)
  f_parser = ParserFactory().create(std="f2003")
  ast = f_parser(reader)
  return __getparloops_walker__(ast)

def getparloops_string(string):
  '''
  Find do-loops with OpenMP pragma
  '''
  reader = FortranStringReader(string, ignore_comments=False)
  f_parser = ParserFactory().create(std="f2003")
  ast = f_parser(reader)
  return __getparloops_walker__(ast)

def diffparloop(parloop):
  '''
  Analyse and differentiate an OpenMP pragma in reverse mode.
  The argument must be the root node of an OpenMP-parallel loop.
  Returns the scopes for all primal and adjoint variables.
  '''
  omppragmastr = parloop.content[0].tostr()
  inspector = loopinspector.ReadWriteInspector()
  inspector.visitNode(parloop)
  # hack to determine loop counter, which is default private
  counter_name = parloop.content[1].items[1].items[1][0].tostr()
  inspector.vars[counter_name].makeLoopCounter()
  varset = inspector.vars
  scopes = ompparser.getscopes(omppragmastr, varset)
  scopes_b = ompdiff.scope_reverse(scopes, varset, inspector)
  return scopes, scopes_b

if __name__ == "__main__":
  if(len(sys.argv)<2):
    raise Exception("Input f90 file must be specified")
  parloops = getparloops_file(sys.argv[1])
  
  # For each parloop, diff the pragma separately from the actual program. For
  # now we'll not do any loop transformations, can just call Tapenade for the
  # rest. omp simd should be roughly the same, with additional mechanics for
  # aligned push/pop and TF-MAD, maybe polyhedral transformations.
  for parloop in parloops:
    scopes, scopes_b = diffparloop(parloop)
    print(parloop)
    print("Original scopes:")
    for varname,scope in scopes.items():
      print("%s: %s"%(varname,scope))
    print("Diff scopes:")
    for varname,scope in scopes_b.items():
      print("%s: %s"%(varname,scope))
    print("\n")




