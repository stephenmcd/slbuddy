
from os.path import dirname, join as pathjoin
from os import startfile
from sys import argv
from tools import Pdict

path = lambda f: pathjoin(dirname(__file__), f)
product = "" if len(argv) < 2 else argv[1]
print argv[1]
csv = path("customers%s.csv" % ("" if not product else "_%s" % product.lower().replace(" ", "_")))
sales = Pdict(path("sales"))
customers = set([sale["name"] for sale in sales.values() if not product or product == sale["item"]])

try:
	f = open(csv, "w")
	f.write("\n".join(customers))
	f.close()
except IOError, e:
	print "failed to create customer csv file: %s" % e
else:
	startfile(csv)
