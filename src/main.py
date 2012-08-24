nextClassId = 0

class Object(object):
  def __init__(self, name, members, methods):
    self.name = name
    self.members = members
    self.methods = methods

class Record(object):
  def __init__(self, **elements):
    self.__dict__.update(elements)

  def emitMethods(self, prefix):
    elements = self.__dict__
    for name, element in elements.iteritems():
      element.emitMethods(prefix + name + '_') # TODO: Avoid collisions

def record(**childElements):
  return Record(**childElements)

objectBuilder = None

def member(tp):
  return objectBuilder.declareMember(tp)

nextFrameId = 0
def allocFrameId():
  global nextFrameId
  frameId = nextFrameId
  nextFrameId += 1
  return frameId

parentFrames = {}
def getParentFrame(frameId):
  return parentFrames[frameId]

def setParentFrame(frameId, val):
  parentFrames[frameId] = val

syncKey = 0

def incSyncKey():
  global syncKey
  syncKey += 1

class Property(object):
  def __init__(self, tp, set, get):
    self.tp = tp
    self.parentFrameId = objectBuilder.frameId
    self.set = set
    self.get = get

  def emitMethods(self, prefix):
    setterName = prefix + 'set'
    incSyncKey()
    setParentFrame(
    emitMethod(setterName, Types.void,
        [('val', self.tp)], lambda: self.set('val'))
    getterName = prefix + 'get'
    emitMethod(getterName, self.tp, [],
        lambda: self.get(lambda val: emitReturn(val)))
    def makeWrapper():
      return MethodProperty(tp, setterName, getterName)
    return makeWrapper

class Instance(Property):
  def __init__(self, tp, mbr):
    Property.__init__(self, tp, self.setValue, self.getValue)
    self.mbr = mbr
    self.syncKey = syncKey

  def setValue(self, value):
    if self.syncKey != syncKey:
      self.syncKey = syncKey
      emitAssignment(
          lambda: emitMemberLookup(self.parentFrameId, self.mbr), value)

  def getValue(self, target):
    target(lambda: emitMemberLookup(self.parentFrameId, self.mbr))

def instance(tp):
  mbr = member(tp)
  return Instance(tp, objectBuilder.frameId, mbr)

def class_(fn):
  return emitClass(fn)

def emitClass(fn):
  global objectBuilder
  oldObjectBuilder = objectBuilder

  class ObjectBuilder(object):
    def __init__(self, frameId):
      self.frameId = frameId
      self.nextMemberId = 0
      self.members = []

    def declareMember(self, tp):
      name = 'member' + str(self.nextMemberId)
      self.nextMemberId += 1
      self.members.append((tp, name))
      return name

  objectBuilder = ObjectBuilder(allocFrameId())

  global nextClassId
  name = 'class' + str(nextClassId)
  nextClassId += 1
  ref = fn()

  members = objectBuilder.members

  objectBuilder = oldObjectBuilder

  print 'class ' + name + ' {'
  for tp, mbr in members:
    emitMember(tp, mbr)
  print ''
  wrappedRef = emitMethods(ref)
  print '}'

  return wrappedRef

def emitAssignment(dest, val):
  print dest() + ' = ' + val

def emitMemberLookup(frameId, mbr):
  print getParentFrame(frameId) + '.' + mbr

def emitMethod(methodName, methodType, args, content):
  print (methodType + ' ' + methodName + '(' +
      ', '.join((argType + ' ' + argName for argName, argType in args))
      + ') {')
  content()
  print '}'

def emitMethods(ref):
  ref.emitMethods('')

def emitMember(tp, mbr):
  print tp + ' ' + mbr + ';'

class Types(object):
  void = 'void'
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
