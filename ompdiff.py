import ompparser

def scope_reverse(scopes,varset,inspector):
  scopes_b = {}
  for varname,scope in scopes.items(): 
    var = varset[varname]
    if(scope == ompparser.Scopes.private):
      scopes_b[varname] = ompparser.Scopes.private
    if(scope == ompparser.Scopes.shared):
      if(inspector.hasSafeReadAccess(var)):
        scopes_b[varname] = ompparser.Scopes.shared
      elif(inspector.isWriteOnly(var)):
        scopes_b[varname] = ompparser.Scopes.shared
      elif(inspector.isReadOnly(var)):
        scopes_b[varname] = (ompparser.Scopes.reduction_add, ompparser.Scopes.atomic_add)
      else:
        scopes_b[varname] = ompparser.Scopes.atomic_add
    if(scope == ompparser.Scopes.reduction_add):
      scopes_b[varname] = ompparser.Scopes.firstprivate
  return scopes_b

