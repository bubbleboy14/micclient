import os
from fyg.util import Named
from random import choice as ranchoice
from chesstools.book import Book, InvalidBookException

class Player(Named):
	def __init__(self, mover, outer, ai="simple", book="random", depth=1, random=1):
		self.name = '%s:%s'%(ai, book)
		self.ai = None
		try:
			if book:
				if book == "random": # omit white-only minchev
					book = ranchoice(["fischer", "morphy", "najdorf", "spassky"])
					self.name = '%s:%s'%(ai, book)
				bookinst = Book(os.path.join('books', book))
			else:
				book = '_nobook'
				bookinst = None
			self.ai = __import__("ai.%s"%(ai,),fromlist=["ai"]).Brain(depth, mover, outer, bookinst, random)
		except InvalidBookException:
			self.log("invalid opening book specified. make sure your .book file is in the 'books' folder")
		except ImportError:
			self.log("invalid ai specified. make sure your script is in the 'ai' folder.")
		except AttributeError:
			self.log("invalid ai specified. make sure your AI class is called 'Brain'.")
		except TypeError:
			self.log("invalid ai specified. make sure your AI class's constructor accepts an integer ply-count, a move callback, an output callback, an opening book object, and a randomness integer.")
		except Exception as e:
			self.log("invalid ai specified. please check your code.")
			self.log(e)

	def __call__(self, board):
		self.log("passing board to ai")
		self.ai(board)

def getPlayer(mover, outer, ai="simple", book="random", depth=1, random=1):
	if not ai: return
	player = Player(mover, outer, ai="simple", book="random", depth=1, random=1)
	return player.ai and player