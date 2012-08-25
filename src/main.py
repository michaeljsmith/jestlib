nextClassId = 0

def allocClassName():
  global nextClassId
  className = 'class' + str(nextClassId)
  nextClassId += 1
  return className

outputtingClass = False

nextMemberId = 0

def clearMemberNames():
  global nextMemberId

def allocMemberName():
  global nextMemberId
  memberName = 'member' + str(nextMemberId)
  nextMemberId += 1
  return memberName

nextMethodId = 0

def clearMethodNames():
  global nextMethodId

def allocMethodName():
  global nextMethodId
  methodName = 'method' + str(nextMethodId)
  nextMethodId += 1
  return methodName

def class_(fn):
  global outputtingClass
  if outputtingClass: raise Exception()

  className = allocClassName()

  class Object(object):
    name = className
    def __init__(self):
      self.instance = declareMember(Object)

  clearMemberNames()
  clearMethodNames()
  outputtingClass = True

  print 'class ' + className + ' {'
  fn(Object)
  print '};'

  outputtingClass = False

  return Object

def declareMember(type):
  name = allocMemberName();
  print type.name + ' ' + name + ';'
  return name

def assign(instanceName, value):
  print instanceName + ' = ' + value + ';'

def callGetMethod(getName, target):
  target(lambda: callMethod(getName, []))

def declareMethod(type, args, content):
  methodName = allocMethodName()
  print (type.name + ' ' + methodName + '(' + ', '.join(
    type.name + ' x' + str(idx) for idx, type in enumerate(args)) + ') {')
  content(*['x' + str(idx) for idx, x in enumerate(args)])
  print '}'
  print ''
  return methodName

def property_(var):
  setName = declareMethod(Void, [type(var)], lambda val: var.set(val))
  getName = declareMethod(var.type, [],
      lambda: var.get(lambda val: return_(val)))

  class Property(object):
    def __init__(self, setName, getName):
      self.setName = setName
      self.getName = getName

    def set(self, value):
      callMethod(self.setName, [value])

    def get(self, target):
      callGetMethod(self.getName, target)

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

    self.instanceName = declareMember(type(self))

  def set(self, value):
    assign(self.instanceName, value)

class String(Primitive):
  name = 'string'

@class_
def Customer(cls):
  cls.firstName = property_(String())
  cls.secondName = property_(String())

@class_
def Model(cls):
  cls.draw = method(Void, [Customer], lambda canvas: printToCanvas(canvas))
  cls.customers = property_(Vector(Customer))
