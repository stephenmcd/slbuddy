
import sys
from os.path import dirname, join as pathjoin
from locale import setlocale, LC_ALL, format
from tools import Pdict, Odict


args = sys.argv[1:]
if not args:
	args = ("Location", "Product")
setlocale(LC_ALL, "")
sales = Pdict(pathjoin(dirname(__file__), "sales"))
paddings = [max([max([len(sale["name"]), len(sale["item"]), 
	len(sale["location"])]) for sale in sales.values()]), 10, 6]
	
	
def get_field(record, field):
	if field == "month":
		date = (record["date"] + " ").split(" ")[0]
		if "-" in date:
			month = "/".join(date.split("-")[:2])
		elif "/" in date:
			month = "/".join(reversed(date.split("/")[0:3:2]))
		else:
			month = "unknown"
		return month
	else:
		return record[field]


def groupby(data, field):
	grouped = Odict()
	for record in data.values():
		if int(record["amount"]) > 0:
			value = get_field(record, field)
			current = grouped.get(value, (0, 0))
			grouped[value] = (current[0] + int(record["amount"]), current[1] + 1)
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


def sort(x, y):
	if x[1][0] == y[1][0]:
		i = 1
	else:
		i = 0
	return cmp(x[1][i], y[1][i])

if __name__ == "__main__":
	for label, field in (("Location", "location"), ("Month", "month"), ("Product", "item"), ("Customer", "name")):
		if label in args or args[0] == "all":
			grouped = groupby(sales, field)
			grouped.sort(cmp=sort if field != "month" else cmp, reverse=True)
			print
			print header("By %s" % label, "Sales", "Qty")
			for name, totals in grouped.items():
				print row(name, totals[0], totals[1])
			print header("TOTAL", total(grouped, 0), total(grouped, 1))
			print
