import rel, optparse, os
rel.override()
rel.initialize(['epoll','poll','select'])
from dez.network import SimpleClient
from dez.xml_tools import XMLNode
from chesstools import Board, Move, List
from chesstools.book import Book, InvalidBookException
from display import Display

class MICSClient(object):
    def __init__(self, host, port, verbose, name, ai, depth, book_name, random):
        self.name = name
        if ai:
            try:
                if book_name:
                    book = Book(os.path.join('books','%s'%book_name))
                else:
                    book_name = '_nobook'
                    book = None
                self.ai = __import__("ai.%s"%ai,fromlist=["ai"]).Brain(depth, self.move, self.ai_out, book, random)
            except InvalidBookException:
                print "invalid opening book specified. make sure your .book file is in the 'books' folder"
                return
            except ImportError:
                print "invalid ai specified. make sure your script is in the 'ai' folder."
                return
            except AttributeError:
                print "invalid ai specified. make sure your AI class is called 'Brain'."
                return
            except TypeError:
                print "invalid ai specified. make sure your AI class's constructor accepts an integer ply-count, a move callback, an output callback, an opening book object, and a randomness integer."
                return
            except:
                print "invalid ai specified. please check your code."
                return
            self.name = '%s::%s'%(ai, book_name)
        else:
            self.ai = None
        self.verbose = verbose
        self.output('connecting to server at %s:%s'%(host,port))
        self.board = Board()
        self.moves = List()
        self.display = Display(self.move, self.promotion, self.draw, self.new, self.save, self.quit, self.timeout, self.seek)
        self.color = None
        self.last_color = None
        self.active = False
        self.client = SimpleClient()
        self.client.connect(host, port, self.__connected)

    def __connected(self, conn):
        self.conn = conn
        self.conn.set_close_cb(self.__closed)
        self.conn.set_rmode_xml(self.recv)
        self.active = True
        self.display.text('connected to server')

    def __closed(self):
        self.active = False
        self.display.text('connection to server lost')

    def ai_out(self, txt):
        self.display.text(txt)

    def output(self, txt):
        if self.verbose:
            print txt

    def draw(self):
        self.display.text('you offer a draw')
        self.send(XMLNode('draw'))

    def new(self):
        if self.color:
            self.send(XMLNode('forfeit'))
        self.display.text('choose initial time and increment')
        self.display.get_time_controls()
        self.send(XMLNode('list'))

    def seek(self, initial, increment):
        self.display.text('finding new game...')
        x = XMLNode('seek')
        x.add_attribute('initial',initial)
        x.add_attribute('increment',increment)
        x.add_attribute('name',self.name)
        self.send(x)

    def save(self):
        self.display.text('game saved')
        self.moves.save(self.last_color)

    def quit(self):
        if self.color:
            self.display.text('you forfeit')
            self.send(XMLNode('forfeit'))
        rel.timeout(.1, rel.abort)

    def timeout(self):
        self.display.text('you lose on time')
        self.send(XMLNode('timeout'))

    def reset_board(self):
        self.display.reset(self.color)
        for x in range(8):
            for y in range(8):
                p = self.board.position[x][y]
                if p:
                    self.display.update((x,y), p)

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
                    self.display.text('select promotion piece')
                    self.display.get_promotion()
                else:
                    self.submit_move(m)
            else:
                self.display.text('illegal move: %s'%m)
                self.display.unselect()
                self.display.get_move()
        else:
                self.display.text('not in game')

    def update(self, msg):
        for pos, piece in self.board.changes:
            self.display.update(pos, piece)
        if self.board.captured:
            self.display.capture(self.board.captured)
        self.display.draw_moves(self.moves.all()[-13:-1])
        self.display.text(msg)

    def get_move(self):
        if self.ai:
            self.ai(self.board)
        else:
            self.display.get_move()

    def recv(self, data):
        self.output("RECV: %s"%data)
        if data.name == 'game':
            self.color = data.attr('color')
            self.last_color = self.color
            initial, increment = data.attr('initial'), data.attr('increment')
            self.display.set_time(initial, increment)
            w, b = data.attr('white'), data.attr('black')
            self.moves.reset((int(initial)/60, increment), w, b)
            self.display.set_caption('%s v %s'%(w,b))
            self.board.reset()
            self.reset_board()
            self.update('game started. you are %s.'%self.color)
            if self.color == 'white':
                self.get_move()
        elif data.name == 'time':
            self.display.update_time(data.attr('white'), data.attr('black'))
        elif data.name == 'confirm':
            self.display.switch_time()
            self.update('move confirmed')
        elif data.name == 'move':
            self.display.switch_time()
            m = Move(data.attr('from'), data.attr('to'), data.attr('promotion'))
            self.moves.add(m)
            self.board.move(m)
            self.update('your move')
            self.get_move()
        elif data.name == 'gameover':
            self.moves.outcome = data.attr('outcome')
            if self.moves.last_move:
                self.moves.last_move.comment = data.attr('reason')
            self.display.text("game over: %s - %s"%(self.moves.outcome, data.attr('reason')))
            self.display.stop_time()
            self.color = None
        elif data.name == 'draw':
            self.display.text('Your opponent offers a draw')
        elif data.name == 'notice':
            self.display.text(data.children[0])
        elif data.name == 'list':
            self.display.list_seeks(['%s-%s'%(int(child.attr('initial'))/60, child.attr('increment')) for child in data.children if int(child.attr('initial')) <= 300], ['%s-%s'%(int(child.attr('initial'))/60, child.attr('increment')) for child in data.children if int(child.attr('initial')) > 300])
        else:
            raise Exception, "invalid data from server: %s"%data

    def send(self, data):
        self.output('SEND: %s'%data)
        if self.active:
            self.conn.write(str(data))

if __name__ == "__main__":
    parser = optparse.OptionParser('client [-s SERVER] [-p PORT] [-a AI] [-v]')
    parser.add_option('-s', '--server', dest='server', default='mariobalibrera.com', help='connect to this server. default: mariobalibrera.com')
    parser.add_option('-p', '--port', dest='port', default='7777', help='connect to MICS server on this port. default: 7777')
    parser.add_option('-n', '--name', dest='name', default='anonymous', help='what do you call yourself?')
    parser.add_option('-a', '--ai', dest='ai', default='', help='use an artificial intelligence script (from the ai folder)')
    parser.add_option('-d', '--depth', dest='depth', default='1', help='change the ply-count of your ai script. default: 1')
    parser.add_option('-b', '--book', dest='book', default='', help='use an opening book (from the books folder)')
    parser.add_option('-r', '--random', dest='random', default='1', help='make your ai/opening book randomly select one of the "r" best moves')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='turn this on to learn the MICS protocol!')
    ops = parser.parse_args()[0]
    try:
        try:    port = int(ops.port)
        except:     print "Invalid port: %s"%ops.port;raise
        try:    depth = int(ops.depth)
        except:     print "Invalid depth: %s"%ops.depth;raise
        try:    random = int(ops.random)
        except:     print "Invalid random: %s"%ops.random;raise
    except:
        print "exiting MICS client"
    else:
        MICSClient(ops.server, port, ops.verbose, ops.name, ops.ai, depth, ops.book, random)