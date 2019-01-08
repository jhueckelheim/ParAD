import ompparser
import loopinspector
import ompdiff
import sys

if(len(sys.argv)<2):
  raise Exception("Input f90 file must be specified")
parloops = loopinspector.getparloops(sys.argv[1])

# For each parloop, diff the pragma separately from the actual program. For
# now we'll not do any loop transformations, can just call Tapenade for the
# rest. omp simd should be roughly the same, with additional mechanics for
# aligned push/pop and TF-MAD, maybe polyhedral transformations.
for parloop in parloops:
  omppragmastr = parloop.content[0].tostr()
  varset = loopinspector.getusedvars(parloop)
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




