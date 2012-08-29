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

    class ClassInstance(Type):
      pass

    print('')
    print('class ' + className + ' {')
    content(ClassInstance)
    print('};')

  return ClassInstance

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

def instance(type):
  memberName = allocMemberName()
  print(type.declaration(memberName) + ';')
  return type.referVar(memberName)

class Object(object):
  pass

def emitMethods(inst):
  return inst.emitMethods()

def Primitive(type):

  class Primitive(Object):
    def __init__(self, set, get):
      self.set = set
      self.get = get

    def emitMethods(self):
      @method(Void, type)
      def setter(val):
        self.set(val)
    
      @method(type)
      def getter():
        self.get(return_(type))

      def wrapInstance(getParent):
        def set(val):
          getParent(lambda parent: setter(parent, val))
        def get(target):
          def getChildAndCallMethod(parent):
            local = declareLocalInitialized(type, lambda: getter(parent))
            target(local)
          getParent(getChildAndCallMethod)

    @staticmethod
    def declaration(name):
      return type.declaration(name)

    @classmethod
    def referVar(cls, varName):
      def set(value):
        emitAssignment(varName, value.name)
      def get(target):
        target(type(varName))
      return cls(set, get)

  return Primitive

def Composite(content):
  class CompositeImpl(Object):
    pass

  @class_
  def content(cls):
    CompositeImpl.cls = cls
    content(CompositeImpl)

  return CompositeImpl

def Record(**elements):
  @Composite
  def RecordImpl(cls):
    for name, type in elements.items():
      setattr(cls, name, property(emitMethods(instance(type))))

  return RecordImpl

class StdFile(object):
  name = 'FILE'

stdout = foreignVar('stdout', Pointer(StdFile))
fputs = foreignFunc('fputs', Void, Pointer(StdFile), Pointer(Char))

Customer = Record(
  firstName = Primitive(String),
  secondName = Primitive(String))

@function(Void, Customer)
def printToCanvas(customer):
  do(fputs(stdout, customer.firstName.c_str()))
  do(fputs(stdout, stringLiteral(' ').c_str()))
  do(fputs(stdout, customer.secondName.c_str()))
  do(fputs(stdout, stringLiteral('\\n').c_str()))

Model = record(
  customers = Vector(Customer))
