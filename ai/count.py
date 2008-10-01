from chesstools.ai import AI

class Brain(AI):
    def evaluate(self, board):
        return len(board.all_legal_moves())