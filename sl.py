
import urllib2, os.path
from urlparse import urlparse
from sys import argv
from urllib import urlencode
from cookielib import CookieJar
from threading import Thread
from time import sleep, strftime
from getpass import getpass
from BeautifulSoup import BeautifulSoup
from tools import Pdict


# add cookie persistance to requests
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(CookieJar()))
opener.addheaders = [("Content-type", 
	"application/x-www-form-urlencoded")]
urllib2.install_opener(opener)


_urls = {
	"domain": "http://secondlife.com/account",
	"login": "/account/login.php?lang=en",
	"friends": "/account/friends.php?lang=en",
	"sales": "/account/transactions.php?lang=en",}


class Checker(Thread):
	"""main threaded friends list checker"""
	
	def __init__(*args):
		"""push credentials into login fields and start thread"""
		
		args = list(args)
		self = args.pop(0)
		self._args = args
		self._events = []
		self._urls = _urls
		self.friends = {}
		self.sales = Pdict(os.path.join(os.path.dirname(__file__), "sales"))
		self.interval = 15
		self.empty = False
		Thread.__init__(self)
		self.start()
			
	def _get(self, url, redirected="", data={}):
		"""downloads the html for an account page"""

		error = ""
		if not redirected:
			redirected = url
		if redirected in self._urls:
			redirected = self._urls[redirected]
		redirected = self._urls["domain"] + redirected
		if url in self._urls:
			url = self._urls[url]
		url = self._urls["domain"] + url
		try:
			response = urllib2.urlopen(url, urlencode(data))
		except urllib2.URLError, e:
			error = "Couldn't connect"
		if not error and response.url != redirected:
			error = "Invalid user/password"
		if error:
			raise Exception, error
		return BeautifulSoup(response.read())

	def _login(self):
		
		# update the domain with the random secure server address
		self._events += [("System", "Connecting to secure server", "")]
		try:
			urlparts = urlparse(urllib2.urlopen(self._urls["domain"]).url)
			self._urls["domain"] = "%s://%s" % (urlparts.scheme, 
				urlparts.hostname)
		except urllib2.URLError, e:
			self._events += [("Error", str(e), "")]
			return False

		# push credentials into login form fields
		names = (
			("First name: ", raw_input),
			("Last Name: ", raw_input),
			("Password: ", getpass))
		for i, name in enumerate(names):
			if i + 1 > len(self._args) or not self._args[i]:
				self._args.append(name[1](name[0]))
		fields = {
			"form[type]": "second-life-member",
			"form[nextpage]": self._urls["friends"].split("?")[0],
			"form[persistent]": "Y", "form[form_action]": "Log In",
			"form[form_lang]": "en", "submit": "Submit"}
		fields.update(dict(zip(["form[username]", "form[lastname]", 
			"form[password]"], self._args[:3])))

		# do login
		self._events += [("System", "Logging in", "")]
		try:
			self._get("login", "friends", fields)
		except Exception, e:
			self._events += [("Error", str(e), "")]
			return False
		else:
			return True

	def _friends(self):
		"""parse friends list from friends page"""
		
		#dict([(line.a.string, line.a["href"].split("/")[2])
		#if line.a else (line.string, "") for line in html("td") 
		#if line.get("headers", "") == "avatar-name"]),

		friends = {}
		for li in self._get("friends")("li"):
			name, location = "", ""
			if li.a["href"].startswith("secondlife://"):
				name = li.a.string
				location = li.a["href"].split("/")[2]
				if location == "Object":
					location = "[UNKNOWN]"
			elif li.string and not li.a:
				name = li.string
			if name:
				friends[name] = location
		return friends
		
	def _sales(self):
		"""parse sales from sales page"""

		# get max date range
		html = self._get("sales")
		dates = {}
		for field, i in {"date_start": -1, "date_end": 0}.items():
			dates[field] = html("select", 
				attrs={"name": field})[0]("option")[i]["id"]

		# get sales
		html = self._get(self._urls["sales"] + "&" + urlencode(dates))
		sales = {}
		for tr in html("tr", attrs={"bgcolor":"#FFFFFF"}):
			if ("Object Sale" in str(tr) and not 
				str(tr).split("Destination:")[0].strip().endswith("<td>")):
				sale = []
				for i, td in enumerate(tr("td")):
					if td.string.strip() and i in [1, 3, 5, 6, 7, 9]:
						for part in reversed((td.string.strip() + 
							":").split(":", 1)):
							part = part.strip().strip(":")
							if part:
								sale.append(part.replace("&quot;", ""))
								break
				sale[-1] = int("".join([c for c in sale[-1] if c.isdigit()]))
				id = sale.pop(0)
				if id not in self.sales:
					sales[id] = dict(zip(["date", "item", "location", 
						"name", "amount"], sale))
		return sales
			
	def run(self):
		"""pull friend updates and new sales from account pages 
		and push to events list"""
		
		if not self._login():
			return
		first = True
		while True:

			if first:
				self._events += [("System", "Getting sales", "")]
			try:
				sales = self._sales()
			except Exception, e:
				self._events += [("Error", str(e), "")]
				sales = {}
			if first:
				self._events += [("System", "Getting friends", "")]
			for id, sale in sales.items():
				self._events += [("Sale", 
					"%(name)s, %(item)s, %(amount)s" % sale, 
					sale["location"])]
			self.sales.update(sales)
			self.sales.save()
			
			try:
				friends = self._friends()
			except Exception, e:
				self._events += [("Error", str(e), "")]
			else:
				for friend in friends:
					if friend not in self.friends:
						self._events += [("Online" if first else "Log In", 
							friend, friends[friend])]
				for friend in self.friends:
					if friend not in friends:
						self._events += [("Log Out", friend, 
							self.friends[friend])]
					elif self.friends[friend] != friends[friend]:
						self._events += [("Teleport", friend, friends[friend])]
				if not friends:
					if not self.empty:
						self.empty = True
						self._events += [("No friends online", "", "")]
				elif self.empty:
					self.empty = False
				self.friends = friends

			first = False
			sleep(self.interval)

	def __iter__(self):
		"""yield and remove events"""
		
		while self._events:
			yield self._events.pop(0)


if __name__ == "__main__":
	# log in and print events
	checker = Checker(*argv[1:])
	while True:
		try:
			for event, name, location in checker:
				print "[%s] %s %s %s" % (strftime("%I:%M:%S"), 
					event.ljust(10), name.ljust(20), location)
			if checker.isAlive():
				sleep(1.)
			else:
				break
		except KeyboardInterrupt, SystemExit:
			break
	raw_input("Press enter to quit")
