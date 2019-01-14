import ompparser
import loopinspector
import ompdiff
import sys
from fparser.common.readfortran import FortranFileReader
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

def getparloops(filename):
  '''
  Find do-loops with OpenMP pragma
  '''
  reader = FortranFileReader(filename, ignore_comments=False)
  f_parser = ParserFactory().create(std="f2003")
  ast = f_parser(reader)
  return __getparloops_walker__(ast)

if(len(sys.argv)<2):
  raise Exception("Input f90 file must be specified")
parloops = getparloops(sys.argv[1])

# For each parloop, diff the pragma separately from the actual program. For
# now we'll not do any loop transformations, can just call Tapenade for the
# rest. omp simd should be roughly the same, with additional mechanics for
# aligned push/pop and TF-MAD, maybe polyhedral transformations.
for parloop in parloops:
  omppragmastr = parloop.content[0].tostr()
  inspector = loopinspector.ReadWriteInspector()
  inspector.visitNode(parloop)
  varset = inspector.vars
  print(varset)
  scopes = ompparser.getscopes(omppragmastr, varset)
  print(parloop)
  print("Original scopes:")
  for varname,scope in scopes.items():
    print("%s: %s"%(varname,scope))
  scopes_b = ompdiff.scope_reverse(scopes, varset)
  print("Diff scopes:")
  for varname,scope in scopes_b.items():
    print("%s: %s"%(varname,scope))
  print("\n")




