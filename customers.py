
from os.path import dirname, join as pathjoin
from os import startfile
from tools import Pdict

path = lambda f: pathjoin(dirname(__file__), f)
csv = path("customers.csv")
sales = Pdict(path("sales"))
customers = set([sale["name"] for sale in sales.values()])

try:
	f = open(csv, "w")
	f.write("\n".join(customers))
	f.close()
except IOError, e:
	print "failed to create customer csv file: %s" % e
else:
	startfile(csv)
