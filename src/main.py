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

def function(type, params):
  def decorate(fn):
    name = functionDeclaration(type, params, fn)

    def callFunctionImpl(*args):
      checkArgs(args, params)
      return type.referInstance(lambda: callFunction(name, args))

    return callFunctionImpl

  return decorate

def foreignVar(name, type):
  with outputtingDefLock:
    print('extern ' + type.name + ' ' + name + ';')

  def getInstance(target):
    target(lambda: print(name, end=''))
  return type.referInstance(getInstance)

def foreignFunc(name, type, params):
  with outputtingDefLock:
    print('extern ' + type.name + ' ' + name + '(' + ', '.join(
      type.name for type in params) + ');')

  def callFunctionImpl(*args):
    checkArgs(args, params)
    return type.referInstance(lambda: callFunction(name, args))

  return callFunctionImpl

def class_(fn):
  className = allocClassName()

  class ClassInstance(object):
    name = className
    def __init__(self, getInstance):
      self.getInstance = getInstance

    @property
    def type(self):
      return type(self)

    def evaluate(self):
      self.getInstance(lambda v: v())

    @classmethod
    def referInstance(cls, getInstance):
      # DEBUG
      getInstance(lambda x: None)

      return cls(getInstance)

  with memberNamesScope, methodNamesScope, outputtingDefLock:

    print('class ' + className + ' {')
    fn(ClassInstance)
    print('};')
    print('')

  return ClassInstance

def method(type, params):
  def decorate(content):
    name = methodDeclaration(type, params, content)

    if type is Void:
      def methodImpl(self, *args):
        checkArgs(args, params)
        return Expression(type,
            lambda: callMethod(self, name, args))
    else:
      raise Exception()

    return methodImpl

  return decorate

def memberDeclaration(type):
  name = allocMemberName();
  print(type.name + ' ' + name + ';')
  def getInstance(target):
    target(lambda: print(name, end=''))
  return getInstance

def assign(getInstance, value):
  getInstance(lambda v: v())
  print(' = ', end='')
  value()
  print(';')

def callFunction(name, args):
  print(name + '(', end='')
  for i, arg in enumerate(args):
    if i > 0: print(', ', end='')
    arg.evaluate()
  print(')', end='')

def callMethod(instance, name, args):
  instance.evaluate()
  print('.', end='')
  callFunction(name, args)

def declareFunction(name, type, params, content):
  namedParams = [('x' + str(i), argType)
      for i, argType in enumerate(params)]

  with outputtingDefLock:
    print(type.name + ' ' + name + '(' + ', '.join(
      argType.name + ' ' + name for name, argType in namedParams) + ') {\n')
    content(*[instanceReference(argType,
      lambda target: target(lambda: print(argName, end='')))
      for argName, argType in namedParams])
    print('}')
    print('')

  return name

def methodDeclaration(type, params, content):
  methodName = allocMethodName()
  return declareFunction(methodName, type, params, content)

def functionDeclaration(type, params, content):
  functionName = allocFunctionName()
  return declareFunction(functionName, type, params, content)

def return_(value):
  print('return ', end='')
  value()
  print(';')

def checkArgs(args, params):
  if len(args) != len(params): raise Exception()
  for arg, param in zip(args, params):
    if not (arg.type is param): raise Exception()

def property_(var):
  if not isinstance(var, Primitive): raise Exception()

  setName = methodDeclaration(Void, [var.type], lambda val: var.set(val))
  getName = methodDeclaration(var.type, [],
      lambda: var.get(lambda val: return_(val)))

  def getProperty(self):
    def getInstance(target):
      target(lambda: callMethod(self, getName, []))

    def set(value):
      callMethod(self, setName, [value])

    return var.type(getInstance, set)
  return property(getProperty)

class Void(object):
  name = 'void'

  def __init__(self, getInstance):
    if type(self) is Primitive: raise Exception()

    self.getInstance = getInstance
    self.set = set

  def evaluate(self):
    self.getInstance()

  @property
  def type(self):
    return type(self)

  @classmethod
  def referInstance(cls, getInstance):
    return cls(getInstance)

def instance(type):
  getInstance = memberDeclaration(type)
  return instanceReference(type, getInstance)

def instanceReference(type, getInstance):
  return type.referInstance(getInstance)

class Primitive(object):
  def __init__(self, getInstance, set):
    if type(self) is Primitive: raise Exception()

    self.getInstance = getInstance
    self.set = set

  def evaluate(self):
    self.getInstance(lambda v: v())

  @property
  def type(self):
    return type(self)

  def get(self, target):
    self.getInstance(target)

  @classmethod
  def referInstance(cls, getInstance):
    def set(value):
      assign(getInstance, value.evaluate)

    return cls(getInstance, set)

def Pointer(type):
  try:
    instances = Pointer.instances
  except AttributeError:
    instances = {}
    Pointer.instances = instances

  try:
    return instances[type]
  except KeyError:
    class PointerImpl(Primitive):
      name = type.name + '*'
    instances[type] = PointerImpl
    return PointerImpl

class Char(Primitive):
  name = 'char'

class String(Primitive):
  name = 'string'

  def c_str(self):
    def getCStr(target):
      def addCall(instance):
        instance()
        print('.c_str()', end='')
      self.getInstance(addCall)
    return Pointer(Char).referInstance(getCStr)

def stringLiteral(text):
  def getInstance(target):
    target(lambda: print('string("' + text + '")', end=''))
  return String.referInstance(getInstance)

class FILE(Primitive):
  name = 'FILE'

def do(expr):
  expr.evaluate()
  print(';')

stdout = foreignVar('stdout', Pointer(FILE))
fputs = foreignFunc('fputs', Void, [Pointer(FILE), Pointer(Char)])

@class_
def Customer(cls):
  cls.firstName = property_(instance(String))
  cls.secondName = property_(instance(String))

@function(Void, [Customer])
def printToCanvas(customer):
  do(fputs(stdout, customer.firstName.c_str()))
  do(fputs(stdout, stringLiteral(' ').c_str()))
  do(fputs(stdout, customer.secondName.c_str()))
  do(fputs(stdout, stringLiteral('\\n').c_str()))

@class_
def Model(cls):

  @method(Void, [Customer])
  def draw(customer):
    do(printToCanvas(customer))
  cls.draw = draw

  cls.customers = property_(Vector(Customer))
