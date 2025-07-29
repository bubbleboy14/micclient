import rel, optparse

class Opponent(object):
	def __init__(self, log=print):
		self.logger = log
		self.client = None

	def log(self, *msg):
		self.logger("Opponent", *msg)

	def getClient(self, **kwargs):
		if not self.client:
			from client import MICSClient
			from config import config
			opps = config.opponent
			defs = config.defaults
			for d in opps.keys():
				if d not in kwargs:
					kwargs[d] = opps[d]
			self.log("building client", kwargs)
			self.client = MICSClient(defs.server, defs.port, **kwargs)
		return self.client

	def __call__(self, initial, increment, variant="standard", lurk=False, invisible=True):
		self.log("seeking", initial, increment, variant)
		self.getClient(invisible=invisible).seek(initial, increment, variant, lurk)

VAGENT = None

def vagent():
	global VAGENT
	if not VAGENT:
		from venvr import getagent
		VAGENT = getagent("opp", ["requirements.txt"], "pypy3")
		VAGENT.register(Opponent, withpath=True)
	return VAGENT

def getOpponent(initial, increment, variant="standard", lurk=False, invisible=True):
	vagent().run("Opponent", initial, increment, variant, lurk, invisible)

if __name__ == "__main__":
	parser = optparse.OptionParser("vopp [--visible]")
	parser.add_option("-v", "--visible", action="store_true",
		dest="visible", default=False, help="visible board")
	ops = parser.parse_args()[0]
	getOpponent(600, 5, lurk=True, invisible=not ops.visible)
	rel.signal(2, rel.abort)
	rel.dispatch()