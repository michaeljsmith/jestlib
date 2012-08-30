from __future__ import print_function
from __future__ import unicode_literals

def singleton(cls):
  return cls()

nextClassId = 0

# TODO: Ensure no collisions with foreign symbols.
def allocClassName():
  global nextClassId
  className = 'class' + str(nextClassId)
  nextClassId += 1
  return className

nextFunctionId = 0

def allocFunctionName():
  global nextFunctionId
  functionName = 'function' + str(nextFunctionId)
  nextFunctionId += 1
  return functionName

nextLocalId = -1

@singleton
class localNamesScope(object):
  def __enter__(self):
    global nextLocalId
    nextLocalId = 0

  def __exit__(self, *args):
    global nextLocalId
    nextLocalId = -1

def allocLocalName():
  global nextLocalId
  if nextLocalId == -1: raise Exception()

  localName = 'local' + str(nextLocalId)
  nextLocalId += 1
  return localName

nextMemberId = -1

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

nextMethodId = -1

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

def emitMemberDeclaration(type, name):
  print(type.declaration(name) + ';')

def emitFunctionSignature(name, type, namedParams):
  print(type.name + ' ' + name + '(' +
      ', '.join(type.declaration(name) for name, type in namedParams) +
      ')', end='')

def emitAssignment(dst, src):
  print(dst + ' = ' + src + ';')

def emitFunctionCall(head, args):
  print(head + '(' +
      ', '.join(arg.name for arg in args) +
      ')', end='')

def declareLocalInitialized(type, content):
  localName = allocLocalName()
  print(type.declare(localName) + ' = ', end='')
  content()
  return localName

def checkArgs(params, args):
  if len(params) != len(args):
    print(params)
    print(args)
    raise Exception()
  for param, arg in zip(params, args):
    if param is not arg.type: raise Exception()

def callFunction(target, head, type, params, args):
  checkArgs(params, args)
  if type is Void:
    emitFunctionCall(head, args)
    print(';')
  else:
    local = declareLocalInitialized(type,
        lambda: emitFunctionCall(head, args))
    target(type(local))

def getCallFunction(name, type, params):
  return lambda target, args: callFunction(target, name, type, params, args)

def getCallMethodGenerator(name, type, params):
  def generateCall(instanceName):
    def call(target, *args):
      head = instanceName + '.' + name
      callFunction(target, head, type, params, args)
    return call
  return generateCall

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

  with outputtingDefLock, memberNamesScope, methodNamesScope, localNamesScope:

    print('')
    print('class ' + className + ' {')
    generate = content()
    print('};')

  class ClassImpl(Type):
    name = className

  def instantiate():
    memberName = allocMemberName()
    emitMemberDeclaration(ClassImpl, memberName)
    return generate(memberName)

  return instantiate

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

    return getCallMethodGenerator(name, type, params)

  return decorate

def foreignVar(name, type):
  print(type.declaration(name) + ';')
  return Reference(type)(name)

def foreignFunc(name, type, *params):
  namedParams = list(('x' + str(i), type) for i, type in enumerate(params))
  emitFunctionSignature(name, type, namedParams)
  print(';')
  return getCallFunction(type, name, params)

def function(type, *params):
  def decorate(content):
    name = allocFunctionName()

    namedParams = list(('x' + str(i), type) for i, type in enumerate(params))
    print('')
    emitFunctionSignature(name, type, namedParams)
    print(' {')
    emitFunctionContent(content, namedParams)
    print('}')
    return getCallFunction(type, name, params)
  return decorate

def evaluate():
  asdf

def VoidMethod(*params):
  class VoidMethod(object):
    def __init__(self, fn):
      self.fn = fn

    @property
    def type(self):
      return Void

    def __call__(self, *args):
      checkArgs(params, args)
      self.fn(lambda _: None, *args)

    def emitMethods(self):
      @method(Void, *params)
      def call(*args):
        self(*args)
      generateCallFn = call

      def wrap(memberName):
        return VoidMethod(generateCallFn(memberName))
      return wrap

  return VoidMethod

def TypedMethod(type, *params):
  class TypedMethod(object):
    def __init__(self, fn):
      self.fn = fn

    @property
    def type(self):
      return type

    def __call__(self, target, *args):
      checkArgs(args, params)
      self.fn(target, *args)

    def emitMethods(self):
      @method(Void, *params)
      def call(*args):
        self(return_(type), *args)
      generateCallFn = call

      def wrap(memberName):
        return TypedMethod(generateCallFn(memberName))
      return wrap

  return TypedMethod

def Method(type, *params):
  if type is Void:
    return VoidMethod(*params)
  else:
    return TypedMethod(type, *params)

class Object(object):
  def __init__(self, **elements):
    vars(self).update(elements)

  def emitMethods(self):
    generators = dict((name, element.emitMethods())
        for name, element in vars(self).items())

    def generate(memberName):
      return Object(**dict((name, generator(memberName))
        for name, generator in generators.items()))

    return generate

def emitMethods(inst):
  return inst.emitMethods()

def primitive(type):
  def generate():
    memberName = allocMemberName()
    emitMemberDeclaration(type, memberName)

    @Method(Void, type)
    def set(target, value):
      emitAssignment(memberName, value.name)

    @Method(type)
    def get(target):
      target(type(memberName))

    return Object(set=set, get=get)
  return generate

def composite(content):
  @class_
  def compositeImpl():
    obj = content()
    generator = emitMethods(obj)
    return generator

  return compositeImpl

def record(**elements):
  @composite
  def recordImpl():
    return Object(**dict((name, gen()) for name, gen in elements.items()))

  return recordImpl

class StdFile(object):
  name = 'FILE'

stdout = foreignVar('stdout', Pointer(StdFile))
fputs = foreignFunc('fputs', Void, Pointer(StdFile), Pointer(Char))

Customer = record(
  firstName = primitive(String),
  secondName = primitive(String))

Model = record(
  customer = Customer)
