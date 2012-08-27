def singleton(cls):
  return cls()

nextClassId = 0

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

def function(type, params):
  def decorate(fn):
    functionName = allocFunctionName()

    namedParams = [('x' + str(i), type) for i, type in enumerate(params)]

    with outputtingDefLock:
      print (type.name + ' ' + functionName + '(' + ', '.join(
        type.name + ' ' + name for name, type in namedParams) + ') {')
      fn(name for name, type in namedParams)
      print '}'
      print ''

    def callFunctionImpl(*args):
      checkArgs(args, params)
      callFunction(functionName, args)

    return callFunctionImpl

  return decorate

def class_(fn):
  className = allocClassName()

  class Object(object):
    name = className
    def __init__(self):
      self.instance = memberDeclaration(Object)

  with memberNamesScope, methodNamesScope, outputtingDefLock:

    print 'class ' + className + ' {'
    fn(Object)
    print '};'
    print ''

  return Object

def memberDeclaration(type):
  name = allocMemberName();
  print type.name + ' ' + name + ';'
  return name

def assign(instanceName, value):
  print instanceName + ' = ' + value + ';'

def callGetMethod(self, getName, target):
  target(lambda: callMethod(self, getName, []))

def methodDeclaration(type, args, content):
  methodName = allocMethodName()
  print (type.name + ' ' + methodName + '(' + ', '.join(
    type.name + ' x' + str(idx) for idx, type in enumerate(args)) + ') {')
  content(*['x' + str(idx) for idx, x in enumerate(args)])
  print '}'
  print ''
  return methodName

def return_(value):
  print 'return ' + value + ';'

def checkArgs(args, params):
  if len(args) != len(params): raise Exception()
  for arg, param in zip(args, params):
    if not (arg.type is param): raise Exception()

def method(type, params, content):
  name = methodDeclaration(type, params, content)

  if type is Void:
    def methodImpl(self, *args):
      checkArgs(args, params)
      callMethod(self, name, args)
  else:
    raise Exception()

  return methodImpl

def property_(var):
  setName = methodDeclaration(Void, [type(var)], lambda val: var.set(val))
  getName = methodDeclaration(var.type, [],
      lambda: var.get(lambda val: return_(val)))

  class Property(object):
    def __init__(self, setName, getName):
      self.setName = setName
      self.getName = getName

    def set(self, value):
      callMethod(self, self.setName, [value])

    def get(self, target):
      callGetMethod(self, self.getName, target)

  def getProperty(self):
    return Property(setName, getName)
  return property(getProperty)

class Void(object):
  name = 'void'

  def __init__(self):
    raise Exception()

class Primitive(object):
  def __init__(self):
    if type(self) is Primitive: raise Exception()

    self.instanceName = memberDeclaration(self.type)

  def set(self, value):
    assign(self.instanceName, value)

  def get(self, target):
    target(self.instanceName)

  @property
  def type(self):
    return type(self)

class String(Primitive):
  name = 'string'

@class_
def Customer(cls):
  cls.firstName = property_(String())
  cls.secondName = property_(String())

@function(Void, [Customer])
def printToCanvas(customer):
  fputs(stdout, customer.firstName)
  fputs(stdout, " ")
  fputs(stdout, customer.secondName)

@class_
def Model(cls):
  cls.draw = method(Void, [Customer], lambda customer:
    printToCanvas(customer))
  cls.customers = property_(Vector(Customer))
