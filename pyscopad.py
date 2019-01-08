import ompparser
import loopinspector
import ompdiff

parloops = loopinspector.getparloops("testinput.f90")

# For each parloop, diff the pragma separately from the actual program.
# For now we'll not do any loop transformations, can just call Tapenade for the rest.
for parloop in parloops:
  omppragmastr = "" # parloop.content[0] # is the first element always the pragma? maybe not.
  varset = loopinspector.getusedvars(parloop)
  scopes = ompparser.getscopes(omppragmastr, varset)
  scopes_b = ompdiff.scope_reverse(scopes, varset)
  print(parloop)
  print(scopes_b)
  print("\n")

#omp simd should be roughly the same, with additional mechanics for aligned push/pop (to be investigated)
#better performance achievable with tf-mad



