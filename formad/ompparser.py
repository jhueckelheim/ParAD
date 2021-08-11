import re
from enum import Enum, auto

class Scopes(Enum):
  private = auto()
  shared = auto()
  reduction_add = auto()
  firstprivate = auto()
  atomic_add = auto() # scope type that is not part of OpenMP standard
  
class OpenMPError(Exception):
  def __init__(self, message):
    Exception("OpenMP parser error: %s"%message)

class OpenMPParser:
  reductions = {
    '+'  : '_add'
  }

  def __init__(self, pragmastr):
    self.scopes, self.default, self.linenumber = self.parsepragma(str(pragmastr))
  
  def parsepragma(self, pragmastr):
    """
    Parse OpenMP pragma string. TODO: replace this with something
    more robust written in e.g. pyparsing
    Returns a dict where each type of clause occurs only once and contains all variables within
    that type of clause. Also returns the default scope for all variables that do not appear
    explicitly in any clause.
    TODO: If the expression inside the numthreads() or if() clause contains something that looks
          like a valid openmp clause, this simple regex will match this even though it should not
    TODO: This currently probably does not deal correctly with multi-line pragmas
    """
    pragmascopes = {}
    defaultscope = None
    variables = set()
    linenumber = 0
    for clausetype in ("shared", "private", "firstprivate", "reduction", "default", "copyin", "line"):
      currentclausetype = re.findall("[,\s]+%s\s*\(([^)]*)\)"%clausetype,pragmastr,re.IGNORECASE)
      for clause in currentclausetype:
        newvariables = {}
        if(clausetype == "reduction"):
          reductiontype,reductionvars = clause.split(':')
          clausetype_r = "%s%s"%(clausetype,reductions[reductiontype])
          newvariables = re.split('\s*[,|\s]\s*',reductionvars)
          newvariables = list(filter(None, newvariables))
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
        elif(clausetype == 'line'):
          # not really an OpenMP clause type, but we are using this fake clause to
          # get the line number where this pragma lives in the input file.
          linenumber = int(clause)
        else:
          newvariables = re.split('\s*[,|\s]\s*',clause)
          newvariables = list(filter(None, newvariables))
          pragmascopes[clausetype] = pragmascopes.get(clausetype, []) + newvariables
        lowervarset = set([item.lower() for item in newvariables])
        if(len(lowervarset & variables) > 0):
          raise OpenMPError("Variables in multiple clauses: %s"%(lowervarset & variables))
        else:
          variables |= lowervarset
    if defaultscope == None:
      defaultscope = Scopes.shared
    return pragmascopes, defaultscope, linenumber
  
  def getscope(self, varname):
    """
    Try to determine the scope (private, public, firstprivate, ...) for a given
    variable. Note that the answer may be wrong for the loop index: it is default
    private, but we can not know the name of the loop index just from looking at
    the pragma.
    """
    varscope = None
    for clause,variables in self.scopes.items():
      if(varname.lower() in [item.lower() for item in variables]):
        varscope = Scopes.__members__[clause]
    if not varscope:
      if self.default:
        varscope = self.default
      else:
        raise OpenMPError("No explicit scope given for %s, and default(none)"%varname)
    return varscope
  
  @staticmethod
  def ispragma(commentstr):
    if(re.match("!\$\s*omp",commentstr,re.IGNORECASE)):
      return True
