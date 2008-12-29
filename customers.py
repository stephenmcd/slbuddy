
from os.path import dirname, join as pathjoin
from tools import Pdict

open(pathjoin(dirname(__file__), "customers"), "w").write(
	"\n".join(set([sale["name"] for sale in 
	Pdict(pathjoin(dirname(__file__), "sales")).values()])))

