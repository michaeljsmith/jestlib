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
      self.members.append([tp, name])
      return name

  objectBuilder = ObjectBuilder()

  obj = fn()

  objectBuilder = oldObjectBuilder

  return obj

def emit(fn):
  obj = object_(fn)

  for attr_key in obj.__dict__:
    emit_function(attr_key, getattr(obj, attr_key))

def member(tp):
  return objectBuilder.declareMember(tp)

def instance(tp):
  mbr = member(tp)
  class Instance(object):
    pass

  result = Instance()
  def setValue(value):
    emitAssignment(mbr, value)
  result.set = setValue

  return result

def class_(fn):
  return emit(fn)

def pair(fst, snd):
  class Pair(object):
    pass

  result = Pair()

  oldFstSet = fst.set
  def firstSet(val):
    oldFstSet(val)
    adsf
  fst.set = firstSet

  snd.set = secondSet

  result.objects = objects

  return result

class Types(object):
  string = 'string'

def string():
  return instance(Types.string)

@class_
def customer():
  return pair(
      string(),
      string())

@class_
def model():
  return vector(customer)
