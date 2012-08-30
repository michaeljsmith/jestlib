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

def memoized(fn):
  results = {}
  def evaluate(*args):
    try:
      return results[args]
    except KeyError:
      result = fn(*args)
      results[args] = result
      return result
  return evaluate

def emitFunctionSignature(name, type, namedParams):
  print(type.name + ' ' + name + '(' +
      ', '.join(type.declaration(name) for name, type in namedParams) +
      ')', end='')

def emitAssignment(dst, src):
  print(dst + ' = ' + src + ';')

def checkArgs(params, args):
  if len(params) != len(args): raise Exception()
  for param, arg in zip(params, args):
    if param is not arg.type: raise Exception()

def callFunction(head, type, params, args):
  checkArgs(params, args)
  local = declareLocalInitialized(type,
      lambda: emitFunctionCall(head, args))
  return type(local)

def getCallFunction(name, type, params):
  return lambda args: callFunction(name, type, params, args)

def getCallMethod(name, type, params):
  def call(self, args):
    head = self.instance + '.' + name
    callFunction(head, type, params, args)
  return call

def return_(type):
  def handle(val):
    print('return ' + val.name + ';')
  return handle

class Type(object):

  def __init__(self, name):
    self.name = name

  @property
  def type(self):
    return type(self)

  @classmethod
  def declaration(cls, name):
    return cls.name + ' ' + name

class Void(Type):
  name = 'void'

@memoized
def Reference(type):
  class ReferenceImpl(object):
    def __init__(self, name):
      self.name = name
  return ReferenceImpl

@memoized
def Pointer(type):
  class PointerImpl(Type):
    name = type.name + '*'
  return PointerImpl

class Char(Type):
  name = 'char'

class String(Type):
  name = 'string'

def class_(content):
  className = allocClassName()

  with outputtingDefLock, memberNamesScope, methodNamesScope:

    print('')
    print('class ' + className + ' {')
    obj = content()
    print('};')

  return obj

def emitFunctionContent(content, namedParams):
  content(*list(type(name) for name, type in namedParams))

def method(type, *params):
  def decorate(content):
    name = allocMethodName()
    namedParams = list(('x' + str(i), type) for i, type in enumerate(params))
    print('')
    emitFunctionSignature(name, type, namedParams)
    print(' {')
    emitFunctionContent(content, namedParams)
    print('}')

    return getCallMethod(type, name, params)

  return decorate

def foreignVar(name, type):
  print(type.declaration(name) + ';')
  return Reference(type)(name)

def foreignFunc(name, type, *params):
  namedParams = list(('x' + str(i), type) for i, type in enumerate(params))
  emitFunctionSignature(name, type, namedParams)
  print(';')
  return getCallFunction(type, name, params)

def VoidMethod(*params):
  class VoidMethod(object):
    def __init__(self, fn):
      self.fn = fn

    def __call__(self, *args):
      checkArgs(params, args)
      self.fn(*args)

    def emit(self):
      @method(Void, *params)
      def setter(val):
        self(val)

  return VoidMethod

def GetMethod(type):
  class GetMethod(object):
    def __init__(self, varName):
      self.varName = varName

    def __call__(self, target):
      target(type(self.varName))
     
    def emit(self):
      @method(type)
      def getter():
        self(return_(type))

  return GetMethod

class Object(object):
  def __init__(self, **elements):
    vars(self).update(elements)

  def emitMethods(self):
    for name, element in vars(self).items():
      element.emit()

def emitMethods(inst):
  return inst.emitMethods()

def primitive(type):
  def generate():
    memberName = allocMemberName()
    print(type.declaration(memberName) + ';')
    return Object(
        set=VoidMethod(type)(lambda value:
          emitAssignment(memberName, value.name)),
        get=GetMethod(type)(memberName))
  return generate

def Composite(content):
  generators = {}

  @class_
  def content():
    content(generators)

  def generate():
    return Object(**dict((name, generator(parentVar))
      for name, generator in generators.items()))
  return generate

def record(**elements):
  @Composite
  def RecordImpl(generators):
    for name, gen in elements.items():
      generators[name] = emitMethods(gen())

  return RecordImpl

class StdFile(object):
  name = 'FILE'

stdout = foreignVar('stdout', Pointer(StdFile))
fputs = foreignFunc('fputs', Void, Pointer(StdFile), Pointer(Char))

Customer = record(
  firstName = primitive(String),
  secondName = primitive(String))

@function(Void, Customer)
def printToCanvas(customer):
  do(fputs(stdout, customer.firstName.c_str()))
  do(fputs(stdout, stringLiteral(' ').c_str()))
  do(fputs(stdout, customer.secondName.c_str()))
  do(fputs(stdout, stringLiteral('\\n').c_str()))

Model = record(
  customers = Vector(Customer))
