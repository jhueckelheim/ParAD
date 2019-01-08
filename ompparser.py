private = "PRIVATE"
shared  = "SHARED"
reduction_add = "REDUCTION+"
firstprivate = "FIRSTPRIVATE"

def getscopes(pragmastr, varset):
  """
  Try to determine the scope (private, public, firstprivate, ...) for
  all variables provided in varset under the OpenMP pragma provided
  in pragmastr.
  """
  scopes = {}
  scopes['u'] = shared
  scopes['r'] = shared
  scopes['a'] = private
  scopes['x'] = reduction_add
  return scopes

