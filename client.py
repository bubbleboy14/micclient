import rel, optparse
from fyg.util import Named, log
from dez.network import SimpleClient
from dez.xml_tools import XMLNode
from chesstools import Board, Move, List, COLORS
from chesstools.piece import LETTER_TO_PIECE
from config import config, setScale
from player import getPlayer
from vopp import getOpponent
from display import Display

class MICSClient(Named):
    def __init__(self, host, port, verbose=False, name="anonymous", ai="", depth=1, book="", random=1, tiny=False, opponent=False, invisible=False, game=None):
        setScale(not tiny)
        self.ai = getPlayer(self.move, self.displog, ai, book, depth, random)
        self.name = self.ai and self.ai.name or name
        self.game = game
        self.verbose = verbose
        self.opponent = opponent
        self.output('connecting to %s:%s'%(host,port))
        self.board = Board()
        self.moves = List()
        self.display = not invisible and Display(self.move, self.promotion, self.draw, self.new, self.save, self.quit, self.timeout, self.seek, self.chat)
        self.color = None
        self.last_color = None
        self.timelock = None
        self.active = False
        self.client = SimpleClient()
        self.client.connect(host, port, self.__connected)

    def __connected(self, conn):
        self.conn = conn
        self.conn.set_close_cb(self.__closed)
        self.conn.set_rmode_xml(self.recv)
        self.active = True
        self.displog('logged in')
        self.next_game()

    def __closed(self):
        self.active = False
        self.displog('connection lost')

    def displog(self, txt):
        self.display and self.display.text(txt) or self.log(txt)

    def output(self, txt):
        self.verbose and self.log(txt)

    def next_game(self):
        if self.game:
            self.log("here for a", *self.game, "game")
            self.seek(*self.game)

    def chat(self, txt):
        x = XMLNode('chat')
        x.add_child(txt.replace('<','&lt;').replace('>','&gt;'))
        self.send(x)
        self.display and self.display.draw_chat(txt, self.color)

    def draw(self):
        self.displog('you offer a draw')
        self.send(XMLNode('draw'))

    def new(self):
        if self.color:
            self.send(XMLNode('forfeit'))
        self.displog('time controls')
        self.display and self.display.get_game_settings()
        self.send(XMLNode('list'))

    def seek(self, initial, increment, variant="standard"):
        self.displog('finding new game...')
        x = XMLNode('seek')
        x.add_attribute('initial',initial)
        x.add_attribute('increment',increment)
        x.add_attribute('variant', variant)
        x.add_attribute('name',self.name)
        self.send(x)
        self.opponent and getOpponent(initial, increment, variant)

    def save(self):
        self.displog('game saved')
        self.moves.save(self.last_color)

    def quit(self):
        if self.color:
            self.displog('you forfeit')
            self.send(XMLNode('forfeit'))
        rel.timeout(.1, rel.abort)

    def timeout(self):
        self.displog('you lose on time')
        self.send(XMLNode('timeout'))

    def reset_board(self):
        self.display and self.display.reset(self.color)
        for x in range(8):
            for y in range(8):
                p = self.board.position[x][y]
                if p:
                    self.display and self.display.update((x,y), p)

    def promotion(self, choice):
        last = self.moves.last_move
        last.promotion = choice
        self.submit_move(last)

    def submit_move(self, m):
        self.board.move(m)
        x = XMLNode('move')
        x.add_attribute('from',m.start)
        x.add_attribute('to',m.end)
        if m.promotion:
            x.add_attribute('promotion',m.promotion)
        outcome = self.board.check_position()
        if outcome:
            x.add_attribute('gameover',outcome)
        self.send(x)

    def move(self, start, end, promotion=None):
        if self.color:
            m = Move(start, end, promotion)
            if self.board.is_legal(m):
                p = self.board.get_square(m.source)
                self.moves.add(m)
                if hasattr(p,'promotion_row') and p.promotion_row == m.destination[0] and not m.promotion:
                    self.display.text('select promotion')
                    self.display.get_promotion()
                else:
                    self.submit_move(m)
            else:
                self.displog('bad move: %s'%(m,))
                if self.display:
                    self.display.unselect()
                    self.display.get_move()
        else:
            self.displog('not in game')

    def update(self, msg):
        if self.display:
            for pos, piece in self.board.changes:
                self.display.update(pos, piece)
            if self.board.captured:
                self.display.capture(self.board.captured)
            self.display.draw_moves(self.moves.all()[-13:-1])
        self.displog(msg)

    def get_move(self):
        if self.ai:
            self.ai(self.board)
        elif self.display:
            self.display.get_move()
        else:
            self.log("can't get move - no ai or display!")

    def recv(self, data):
        self.output("RECV: %s"%data)
        if data.name == 'game':
            self.color = data.attr('color')
            self.last_color = self.color
            initial, increment = data.attr('initial'), data.attr('increment')
            self.timelock = int(data.attr('timelock'))
            self.display and self.display.set_time(initial, increment)
            w, b = data.attr('white'), data.attr('black')
            self.moves.reset((int(initial)/60, increment), w, b)
            self.display and self.display.set_caption('%s v %s'%(w,b))
            if data.attr('lineup'):
                self.board.reset_960([LETTER_TO_PIECE[p] for p in data.attr('lineup')])
            else:
                self.board.reset()
            self.reset_board()
            self.update('you are %s'%self.color)
            if self.color == 'white':
                self.get_move()
        elif data.name == 'time':
            self.display and self.display.update_time(data.attr('white'), data.attr('black'))
        elif data.name == 'confirm':
            self.display and self.display.switch_time()
            self.update('move confirmed')
        elif data.name == 'move':
            if self.timelock:
                self.send(XMLNode('received'))
            self.display and self.display.switch_time()
            m = Move(data.attr('from'), data.attr('to'), data.attr('promotion'))
            self.moves.add(m)
            self.board.move(m)
            self.update('your move')
            self.get_move()
        elif data.name == 'chat':
            self.display and self.display.draw_chat(data.children[0].replace('&lt;','<').replace('&gt;','>'), COLORS[self.color])
        elif data.name == 'gameover':
            self.moves.outcome = data.attr('outcome')
            if self.moves.last_move:
                self.moves.last_move.comment = data.attr('reason')
            self.displog("%s - %s"%(self.moves.outcome, data.attr('reason')))
            self.display and self.display.stop_time()
            self.color = None
            self.game and rel.timeout(5, self.next_game)
        elif data.name == 'draw':
            self.displog('draw?')
        elif data.name == 'notice':
            self.displog(data.children[0])
        elif data.name == 'list':
            self.display and self.display.list_seeks([(child.attr('name'), '%s-%s %s'%(int(child.attr('initial'))/60, child.attr('increment'), child.attr('variant'))) for child in data.children])
        else:
            raise Exception("invalid data from server: %s\ndo you have the most recent client release?"%data)

    def send(self, data):
        self.output('SEND: %s'%data)
        if self.active:
            self.conn.write(str(data))

tconts = ["2", "5", "10", "20"]
tincs  = ["0", "2", "5", "12"]

if __name__ == "__main__":
    defs = config.defaults
    parser = optparse.OptionParser('client [-s SERVER] [-p PORT] [-n NAME] [-a AI] [-d DEPTH] [-b BOOK] [-r RANDOM] [-v]')
    parser.add_option('-s', '--server', dest='server', default=defs.server, help='connect to this server. default: %s'%(defs.server,))
    parser.add_option('-p', '--port', dest='port', default=defs.port, help='connect to MICS server on this port. default: %s'%(defs.port,))
    parser.add_option('-n', '--name', dest='name', default=defs.name, help='what do you call yourself?')
    parser.add_option('-a', '--ai', dest='ai', default='', help='use an artificial intelligence script (from the ai folder)')
    parser.add_option('-d', '--depth', dest='depth', default='1', help='change the ply-count of your ai script. default: 1')
    parser.add_option('-b', '--book', dest='book', default='', help='use an opening book (from the books folder)')
    parser.add_option('-r', '--random', dest='random', default='1', help='make your ai/opening book randomly select one of the "r" best moves')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='turn this on to learn the MICS protocol!')
    parser.add_option('-t', '--tiny', action='store_true', dest='tiny', default=False, help='small board')
    parser.add_option('-o', '--opponent', action='store_true', dest='opponent', default=False, help="run opponent")
    parser.add_option('-i', '--invisible', action='store_true', dest='invisible', default=False, help="no visible board")
    parser.add_option('-g', '--game', dest="game", default=None, help="automatically seek with given ('10/5' for instance) time controls")
    ops = parser.parse_args()[0]
    game = ops.game
    try:
        try:
            if game:
                game = game.split("/")
                if game[0] not in tconts or game[1] not in tincs:
                    raise
                game = (int(game[0]) * 60, int(game[1]))
        except:
            log("Invalid time controls: %s"%(ops.game,))
            log("try something like 10/5")
            log("the first value (initial) can be 2, 5, 10, or 20")
            log("the second value (increment) can be 0, 2, 5, or 12")
            raise
        try:
            port = int(ops.port)
        except:
            log("Invalid port: %s"%(ops.port,))
            raise
        try:
            depth = int(ops.depth)
        except:
            log("Invalid depth: %s"%(ops.depth,))
            raise
        try:
            random = int(ops.random)
        except:
            log("Invalid random: %s"%(ops.random,))
            raise
    except:
        log("exiting MICS client")
    else:
        MICSClient(ops.server, port, ops.verbose, ops.name, ops.ai, depth, ops.book, random, ops.tiny, ops.opponent, ops.invisible, game)