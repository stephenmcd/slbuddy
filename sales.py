#! /usr/bin/python

import sys
from os.path import dirname, exists, join as pathjoin
from locale import setlocale, LC_ALL, format
from tools import Pdict, Odict


args = sys.argv[1:]
if not args:
    args = ("Location", "Product")
setlocale(LC_ALL, "")
sales = Pdict(pathjoin(dirname(__file__), "sales"))
paddings = [max([max([len(sale["name"]), len(sale["item"]), 
    len(sale["location"])]) for sale in sales.values()]), 10, 6]


def cleanup():
    # perform one-time clean up of sales data corrupted by 
    # Linden Lab's change from 10 char IDs to 36 char IDs with
    # no defined way of comparing a sale that was recorded twice
    # with each type of id
    cleaned_file = pathjoin(dirname(__file__), "ll_id_change_cleaned")
    if exists(cleaned_file):
        return
    f = open(cleaned_file, "w")
    f.write("done")
    f.close()
    sale_str = "%(date)s%(name)s%(item)s"
    new_values = [sale_str % v for k, v in sales.items() if len(k) == 36]
    if len(new_values) == len(sales):
        return
    duplicate_keys = [k for k, v in sales.items() 
        if len(k) == 10 and sale_str % v in new_values]
    for k in duplicate_keys:
        del sales[k]
    sales.save()

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
        if int(record["amount"]) > 1 and ("/" not in args[0] or 
            args[0] == get_field(record, "month")):
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
    cleanup()
    for label, field in (("Location", "location"), ("Month", "month"), ("Product", "item"), ("Customer", "name")):
        if label in args or args[0] == "all" or ("/" in args[0] and label not in ("Month", "Customer")):
            grouped = groupby(sales, field)
            grouped.sort(cmp=sort if field != "month" else cmp, reverse=True)
            if "/" in args[0]:
                label += " for %s" % args[0]
            print
            print header("By %s" % label, "Sales", "Qty")
            for name, totals in grouped.items():
                print row(name, totals[0], totals[1])
            print header("TOTAL", total(grouped, 0), total(grouped, 1))
            print
