class ParloopAnalyzer:
  def __init__(self, parloop, parser):
    self.omppragmastr = parloop.content[0].tostr()
    self.varset = {}
    self.clauses = {}
