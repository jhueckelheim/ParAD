class ParloopDifferentiator:
  def __init__(self, parser, analysis, questions):
    self.parser = parser
    self.analysis = analysis
    self.questions = questions
    self.writeIndices = self.getIndexSet(analysis, questions)

  def getIndexSet(self, analysis, questions):
    for question in questions:
      varname = question["name"]
      writes = question["write"]
      for write in writes:
        linenumber = write["line"]
        indices = write["idx"]
        expression = [self.parser.currentInstanceByLineNumber[linenumber][index].function() for index in indices]
        ttuple = analysis.ttypes.tupleFromExpression(expression)
        print(f"qt {varname}: "+str(ttuple))
    return ""#writeIndices

#[{'name': 'cr', 'read': [], 'write': [{'idx': ['idu', 'j'], 'line': 148}, {'idx': ['iud', 'j'], 'line': 148}, {'idx': ['iud', 'j'], 'line': 145}, {'idx': ['idu', 'j'], 'line': 145}, {'idx': ['iuu', 'j'], 'line': 142}, {'idx': ['idd', 'j'], 'line': 140}, {'idx': ['idu', 'j'], 'line': 138}, {'idx': ['iud', 'j'], 'line': 138}, {'idx': ['idd', 'j'], 'line': 137}, {'idx': ['iuu', 'j'], 'line': 136}, {'idx': ['idu', 'j'], 'line': 121}, {'idx': ['iud', 'j'], 'line': 121}, {'idx': ['iud', 'j'], 'line': 118}, {'idx': ['idu', 'j'], 'line': 118}, {'idx': ['iuu', 'j'], 'line': 115}, {'idx': ['idd', 'j'], 'line': 113}, {'idx': ['idu', 'j'], 'line': 111}, {'idx': ['iud', 'j'], 'line': 111}, {'idx': ['idd', 'j'], 'line': 110}, {'idx': ['iuu', 'j'], 'line': 109}, {'idx': ['i', 'jp'], 'line': 69}]}, {'name': 'cl', 'read': [], 'write': [{'idx': ['idu', 'j'], 'line': 148}, {'idx': ['iud', 'j'], 'line': 145}, {'idx': ['iuu', 'j'], 'line': 142}, {'idx': ['idd', 'j'], 'line': 140}, {'idx': ['idu', 'j'], 'line': 121}, {'idx': ['iud', 'j'], 'line': 118}, {'idx': ['iuu', 'j'], 'line': 115}, {'idx': ['idd', 'j'], 'line': 113}]}]
