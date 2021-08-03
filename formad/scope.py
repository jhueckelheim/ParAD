class Scope:
  '''
  Variables and their properties are sometimes only valid in a particular
  scope (e.g. within a branch or loop body). This class holds variables and
  their index expressions that appear in a particular scope.
  '''
  def __init__(self, parent):
    self.parent = parent
    self.siblingNumber = 0
    if(parent):
      self.siblingNumber = len(parent.children)
      parent.children.append(self)
    self.children = []
    self.props = {}

  def __repr__(self):
    parentrepr = ""
    if (self.parent):
      return repr(self.parent)+"_"+str(self.siblingNumber)
    else:
      return str(self.siblingNumber)
