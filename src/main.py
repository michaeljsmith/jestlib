nextClassId = 0

class Object(object):
  def __init__(self, name, members, methods):
    self.name = name
    self.members = members
    self.methods = methods

class Reference(object):
  def __init__(self, methods):
    self.methods = methods

def reference(**methods):
  return Reference(methods)

class Record(Reference):
  pass

def record(**childElements):
  class RecordImpl(Record):
    def __init__(self, methods):
      Record.__init__(self, methods)

  methods = {}
  for name, childElement in childElements.iteritems():
    wrappedMethodNames = []
    for childMethodName, childMethod in childElement.methods.iteritems():
      methodName = name + '_' + childMethodName
      methods[methodName] = childMethod # TODO: Avoid collisions...
      wrappedMethodNames.append(methodName)

    elementType = type(childElement)
    def getElement(self):
      methods = dict(
          ((name, self.methods[name]) for name in wrappedMethodNames))
      return elementType(methods)

    setattr(RecordImpl, name, getElement)

  return RecordImpl(methods)

class Socket(object):
  def __init__(self, handler, listener):
    self.handler = handler
    self.listener = listener
socket = Socket

objectBuilder = None

def object_(fn):
  global objectBuilder
  oldObjectBuilder = objectBuilder

  class ObjectBuilder(object):
    def __init__(self):
      self.nextMemberId = 0
      self.members = []

    def declareMember(self, tp):
      name = 'member' + str(self.nextMemberId)
      self.nextMemberId += 1
      self.members.append((tp, name))
      return name

  objectBuilder = ObjectBuilder()

  global nextClassId
  name = 'class' + str(nextClassId)
  nextClassId += 1
  ref = fn()

  members = objectBuilder.members

  objectBuilder = oldObjectBuilder

  return Object(name, members, ref.methods)

def member(tp):
  return objectBuilder.declareMember(tp)

def instance(tp):
  mbr = member(tp)
  return reference(
        set=Socket(lambda val: emitAssignment(mbr, val), lambda val: None),
        get=Socket(lambda getter: None, lambda getter: None))

def class_(fn):
  obj = object_(fn)

  return emitClass(obj)

def emitClass(cls):
  print 'class ' + cls.name + ' {'

  for tp, mbr in cls.members:
    emitMember(tp, mbr)

  print ''

  methodWrappers = {}
  for methodName, method in cls.methods.iteritems():
    methodWrapper = emitMethod(methodName, method)
    methodWrappers[methodName] = methodWrapper

  print '}'

  return Reference(**methodWrappers)

def emitMethod(methodName, method):
  fn = method.handler
  argNames = inspect.getargspec(fn)[0]
  return methodWrapper

def emitMember(tp, mbr):
  print tp + ' ' + mbr + ';'

class Types(object):
  string = 'string'

def string():
  return instance(Types.string)

@class_
def customer():
  return record(
      firstName=string(),
      secondName=string())

@class_
def model():
  return vector(customer)
