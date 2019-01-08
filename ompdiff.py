import ompparser

def scope_reverse(scopes,varset):
  scopes_b = {}
  for varname,scope in scopes.items(): 
    var = varset[varname]
    if(scope == ompparser.private):
      scopes_b[varname] = ompparser.private
    if(scope == ompparser.shared):
      if(var.exclusiveread):
        scopes_b[varname] = ompparser.shared
      else:
        scopes_b[varname] = ompparser.reduction_add
    if(scope == ompparser.reduction_add):
      scopes_b[varname] = ompparser.firstprivate
  return scopes_b

