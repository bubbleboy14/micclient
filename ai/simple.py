from chesstools.ai import AI

WEIGHT = {'King':100, 'Queen':9, 'Rook':5, 'Bishop':3, 'Knight':2, 'Pawn':1}

class Brain(AI):
    def evaluate(self, board):
        score = len(board.all_legal_moves()) - len(board.all_opponent_moves())
        for piece in board.pieces():
            mult = piece.color == board.turn and 1 or -1
            score += mult*WEIGHT[piece.name]*10
            if piece.name == "Pawn":
                score += mult*piece.supporting_pawns()
                score -= mult*piece.opposing_pawns()
                score += mult*piece.advancement()
        return score