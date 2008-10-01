from chesstools.ai import AI

WEIGHT = {'King':100, 'Queen':9, 'Rook':5, 'Bishop':3, 'Knight':2, 'Pawn':1}

class Brain(AI):
    def evaluate(self, board):
        score = 0
        for piece in board.pieces():
            mult = piece.color == board.turn and 1 or -1
            score += mult*WEIGHT[piece.name]
        return score