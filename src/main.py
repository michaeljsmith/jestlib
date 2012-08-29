from __future__ import print_function

def singleton(cls):
  return cls()

nextClassId = 0

# TODO: Ensure no collisions with foreign symbols.
def allocClassName():
  global nextClassId
  className = 'class' + str(nextClassId)
  nextClassId += 1
  return className

nextMemberId = 0

def allocFunctionName():
  global nextFunctionId
  functionName = 'function' + str(nextFunctionId)
  nextFunctionId += 1
  return functionName

nextFunctionId = 0

@singleton
class memberNamesScope(object):
  def __enter__(self):
    global nextMemberId
    nextMemberId = 0

  def __exit__(self, *args):
    global nextMemberId
    nextMemberId = -1

def allocMemberName():
  global nextMemberId
  if nextMemberId == -1: raise Exception()

  memberName = 'member' + str(nextMemberId)
  nextMemberId += 1
  return memberName

nextMethodId = 0

@singleton
class methodNamesScope(object):
  def __enter__(self):
    global nextMethodId
    nextMethodId = 0

  def __exit__(self, *args):
    global nextMethodId
    nextMethodId = -1

def allocMethodName():
  global nextMethodId
  if nextMethodId == -1: raise Exception()

  methodName = 'method' + str(nextMethodId)
  nextMethodId += 1
  return methodName

@singleton
class outputtingDefLock(object):
  def __init__(self):
    self.outputtingClass = False

  def __enter__(self):
    if self.outputtingClass: raise Exception()
    outputtingClass = True

  def __exit__(self, *args):
    self.outputtingClass = False

stdout = foreignVar('stdout', Pointer(StdFile))
fputs = foreignFunc('fputs', Void, Pointer(StdFile), Pointer(Char))

Customer = Record(
  firstName = instance(String),
  secondName = instance(String))

@function(Void, Customer)
def printToCanvas(customer):
  do(fputs(stdout, customer.firstName.c_str()))
  do(fputs(stdout, stringLiteral(' ').c_str()))
  do(fputs(stdout, customer.secondName.c_str()))
  do(fputs(stdout, stringLiteral('\\n').c_str()))

Model = record(
  customers = Vector(Customer))
