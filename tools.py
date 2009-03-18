
from cPickle import load, dump


class Odict(dict):
	"""ordered dictionary"""
	
	def __init__(self, data={}):
		dict.__init__(self)
		self._keys = []
		self.update(data)

	def __setitem__(self, key, value):
		if key not in self._keys:
			self._keys.append(key)
		dict.__setitem__(self, key, value)
		
	def __delitem__(self, key):
		if key in self._keys:
			self._keys.remove(key)
			dict.__delitem__(self, key)
			
	def __iter__(self):
		for key in self.keys():
			yield key, self[key]

	def items(self):
		return list(self.__iter__())
		
	def keys(self):
		return self._keys

	def values(self):
		return [value for key, value in self]
			
	def update(self, data):
		for key, value in dict(data).items():
			self[key] = value
			
	def sort(*args, **kwargs):
		args = list(args)
		self = args.pop(0)
		items = self.items()
		items.sort(*args, **kwargs)
		self._keys = [k for k, v in items]

		
class Pdict(dict):
	"""file persisted dictionary"""
	
	def __init__(self, path):
		try:
			f = open(path, "rb")
		except IOError:
			pass
		else:
			self.update(load(f))
			f.close()
		self._path = path
	
	def save(self):
		try:
			f = open(self._path, "wb")
		except IOError:
			pass
		else:
			dump(self, f)
			f.close()
			

class Events(object):
	"""publisher/subscriber for events"""
	
	_topics = {}
		
	@staticmethod
	def subscribe(topic, subscriber, bubble=True):
		topics = Events._topics.get(topic, [])
		topics.append((subscriber, bubble))
		Events._topics[topic] = topics
		
	@staticmethod
	def publish(topic, data=None):
		for subscriber, bubble in Events._topics.get(topic, []):
			subscriber(data)
			if not bubble:
				break

