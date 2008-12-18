
from os.path import dirname, join as pathjoin
from locale import setlocale, LC_ALL, format
from tools import Pdict, Odict


setlocale(LC_ALL, "")
sales = Pdict(pathjoin(dirname(__file__), "sales"))
paddings = [max([max([len(sale["name"]), len(sale["item"]), 
	len(sale["location"])]) for sale in sales.values()]), 10, 5]


def groupby(data, field):
	grouped = Odict()
	for value in data.values():
		if int(value["amount"]) > 0:
			item = value[field]
			current = grouped.get(item, (0, 0))
			grouped[item] = (current[0] + int(value["amount"]), current[1] + 1)
	return grouped


def header(*values):
	sep = "-" * sum(paddings)
	return "\n".join([sep, row(*values), sep])
	

def row(*values):
	values = list(values)
	for i, value in enumerate(values):
		if not i:
			just = str.ljust
		else:
			just = str.rjust
		if str(value).isdigit():
			value = format("%d", value, True)
		values[i] = just(value, paddings[i])
	return "".join(values)
	
	
def total(data, index):
	return sum(v[index] for v in data.values())


for label, field in (("Location", "location"), ("Product", "item"), ("Customer", "name")):
	grouped = groupby(sales, field)
	grouped.sort(cmp=lambda x, y: cmp(x[1][1], y[1][1]), reverse=True)
	print
	print header("By %s" % label, "Sales", "Qty")
	for name, totals in grouped.items():
		print row(name, totals[0], totals[1])
	print header("TOTAL", total(grouped, 0), total(grouped, 1))
	print

