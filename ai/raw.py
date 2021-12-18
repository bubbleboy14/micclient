class Brain(object):
    def __init__(self, depth, move, output, book, random):
        self.cb = move

    def __call__(self, board):
        self.cb(input("enter from:"), input("enter to:"))
