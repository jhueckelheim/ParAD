import re
from enum import Enum, auto

class Scopes(Enum):
  private = auto()
  shared = auto()
  reduction_add = auto()
  firstprivate = auto()
  atomic_add = auto() # interal scope type that is not part of OpenMP standard

reductions = {
  '+'  : '_add',
  'max': '_max'
}

class OpenMPError(Exception):
  def __init__(self, message):
    Exception("OpenMP parser error: %s"%message)

def parsepragma(pragmastr):
  """
  Parse OpenMP pragma string. TODO: replace this with something
  more robust written in e.g. pyparsing
  Returns a dict where each type of clause occurs only once and contains all variables within
  that type of clause. Also returns the default scope for all variables that do not appear
  explicitly in any clause.
  TODO: If the expression inside the numthreads() or if() clause contains something that looks
        like a valid openmp clause, this simple regex will match this even though it should not
  TODO: This currently probably does not deal correctly with multi-line pragmas
  TODO: each variable can only appear in at most one pragma (e.g. can not be shared and private
        at the same time)
  """
  pragmascopes = {}
  defaultscope = None
  variables = set()
  for clausetype in ("shared", "private", "firstprivate", "reduction", "default", "copyin"):
    currentclausetype = re.findall("[,\s]+%s\s*\(([^)]*)\)"%clausetype,pragmastr,re.IGNORECASE)
    for clause in currentclausetype:
      newvariables = {}
      if(clausetype == "reduction"):
        reductiontype,reductionvars = clause.split(':')
        clausetype_r = "%s%s"%(clausetype,reductions[reductiontype])
        newvariables = re.split('\s*[,|\s]\s*',reductionvars)
        pragmascopes[clausetype_r] = pragmascopes.get(clausetype_r, []) + newvariables
      elif(clausetype == 'default'):
        if(defaultscope): # we already encountered a default
          raise OpenMPError("More than one default scope")
        elif(clause.lower() in Scopes.__members__):
          defaultscope = Scopes.__members__[clause.lower()]
        elif(clause.lower() == "none"):
          defaultscope = False
        else:
          raise OpenMPError("Invalid default scope")
      else:
        newvariables = re.split('\s*[,|\s]\s*',clause)
        pragmascopes[clausetype] = pragmascopes.get(clausetype, []) + newvariables
      lowervarset = set([item.lower() for item in newvariables])
      if(lowervarset & variables):
        raise OpenMPError("Variables in multiple clauses: %s"%(newvariables & variables))
      else:
        variables |= lowervarset
  if defaultscope == None:
    defaultscope = Scopes.shared
  return pragmascopes, defaultscope

def getscopes(pragmastr, varset):
  """
  Try to determine the scope (private, public, firstprivate, ...) for
  all variables provided in varset under the OpenMP pragma provided
  in pragmastr.
  """
  varscopes = {}
  scopes, defaultscope = parsepragma(pragmastr)
  for varname, varproperties in varset.items():
    if(varproperties.loopCounter):
      varscopes[varname] = Scopes.private
    else:
      for clause,variables in scopes.items():
        if(varname.lower() in [item.lower() for item in variables]):
          varscopes[varname] = Scopes.__members__[clause]
      if not varname in varscopes:
        if defaultscope:
          varscopes[varname] = defaultscope
        else:
          raise OpenMPError("No explicit scope given for %s, and default(none)"%varname)
  return varscopes

def ispragma(commentstr):
  if(re.match("!\$\s*omp",commentstr,re.IGNORECASE)):
    return True
