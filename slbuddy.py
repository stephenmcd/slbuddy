
from sl import Checker
from gui import Notifier
from tools import Odict, Pdict
import sys, os.path, cPickle, base64


if hasattr(sys, "frozen"): __file__ = sys.executable
path = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))


class Settings(Odict, Pdict):
	"""ordered persistant dict for settings"""

	def __init__(self, path, data={}):
		Pdict.__init__(self, path)
		Odict.__init__(self, data)


class Buddies(Notifier):
	
	def __init__(self):
		
		self.settings = Settings("settings", 
			[("First Name", ""), ("Last Name", ""), ("Password", "")])
		self.settings["Password"] = base64.b64decode(self.settings["Password"])
		self.first = True
		self._started = False
		#	self.start()
		Notifier.__init__(self, os.path.join(path, "sl.ico"))
		Notifier.start(self)		
			
	def start(self):
		self.checker = Checker(self.settings.values())

	def main(self):
		if self._started:
			for event, name, location in self.checker:
				location = location if location != "Object" else ""
				if event != "Online":
					self.showPopup("%s - %s\n%s" % (name, event, location))
		else:
			self.showSettings()
				
	def menu(self):
		data = []
		if False and self._started:
			data = self.checker.friends
		return data #[name, location if location else name for name, location in self.checker.friends]

	def click(self, item):
		print "popup clicked: %s" % item

	def select(self, item):
		print "menu selected: %s" % item
		
	def save(self, settings):
		settings["Password"] = base64.b64encode(settings["Password"])
		self.settings.update(settings)
		self.settings.save()
		if not self._started:
			self._started = True
			self.start()


if __name__ == "__main__":
	buddies = Buddies()
		
