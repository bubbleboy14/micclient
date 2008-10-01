import event, os, pygame
pygame.init()
from chesstools import Timer
from chesstools.move import from_tile

UNIT = 32
HALF = UNIT/2
WIDTH = 10
HEIGHT = 9.5
BLACK = 116, 69, 40
WHITE = 204, 166, 85
TRANS = 0, 255, 0
SIDE = 0, 0, 0
HIGHLIGHT = 255, 0, 0
MOVES_COLOR = 200, 200, 200
MOVES_RECT = UNIT*8, UNIT, UNIT*2, UNIT*6
TEXT_COLOR = 92, 255, 42
TEXT_RECT = 0, UNIT*8, UNIT*8, HALF
BANNER_COLOR = 225, 225, 150
BANNER_RECT = UNIT, UNIT*3, UNIT*6, UNIT

class Click(object):
    def __init__(self, quit_cb):
        pygame.event.set_allowed(None)
        pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
        pygame.event.set_allowed(pygame.QUIT)
        self.interrupts = {}
        self.quit_cb = quit_cb
        self.event_cb = None
        event.timeout(0.05, self._poll)

    def _poll(self):
        event = pygame.event.poll()
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            for [x1, y1, x2, y2], int_cb in self.interrupts.items():
                if x > x1 and x < x1+x2 and y > y1 and y < y1+y2:
                    int_cb()
                    return True
            if self.event_cb:
                cb = self.event_cb
                self.event_cb = None
                cb(x, y)
        elif event.type == pygame.QUIT:
            return self.quit_cb()
        return True

    def add_interrupt(self, rect, cb):
        self.interrupts[rect] = cb

    def remove_interrupt(self, rect):
        if rect in self.interrupts:
            del self.interrupts[rect]
        else:
            print '%s not in self.interrupts!'%(rect)

    def get(self, cb):
        pygame.event.clear()
        event = pygame.event.wait()
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if not self.check_interrupts(x,y):
                cb(x, y)
        else:
            self.quit_cb()

    def tile(self, cb, u=UNIT, x_min=None, x_max=None, y_min=None, y_max=None):
        mult = UNIT/u
        if x_min is None: x_min = 0
        if x_max is None: x_max = WIDTH*mult
        if y_min is None: y_min = 0
        if y_max is None: y_max = HEIGHT*mult
        def cb2(a, b):
            x = a/u
            y = b/u
            if x < x_min or x > x_max or y < y_min or y > y_max:
                self.event_cb = cb2
            else:
                cb(x, y)
        self.event_cb = cb2

class Display(object):
    def __init__(self, move_cb, promotion_cb, draw_cb, new_cb, save_cb, quit_cb, timeout_cb, seek_cb):
        self.cbs = {'move':move_cb, 'promotion':promotion_cb, 'draw':draw_cb, 'new':new_cb, 'save':save_cb, 'quit':quit_cb, 'timeout':timeout_cb, 'seek':seek_cb}
        for folder in [os.path.join('skins','default',sub) for sub in ['white','black','misc']]:
            for p in os.walk(folder).next()[2]:
                setattr(self, p[:-4], pygame.image.load(os.path.join(folder,p)))
                piece = getattr(self, p[:-4])
                piece.set_colorkey(TRANS)
                if folder != 'misc':
                    setattr(self, p[:-4]+'_small', pygame.transform.scale(piece, (HALF, HALF)))
        self.set_caption('MICS Chess Client')
        pygame.display.set_icon(self.N_small)
        self.click = Click(quit_cb)
        self.screen = pygame.display.set_mode((int(WIDTH*UNIT),int(HEIGHT*UNIT)))
        self.highlighted = None
        self.captured = {'white':[-1,0],'black':[-1,0]}
        self.move_font = pygame.font.SysFont('Monospace', HALF)
        self.text_font = pygame.font.SysFont('Monospace', UNIT*2/3)
        self.timer_font = pygame.font.SysFont('Monospace', UNIT)
        self.timer = Timer(300, 0)
        self.ticker = event.timeout(1, self.refresh_time)
        self.reset('white')
        self.seeking = False

    def set_caption(self, txt):
        pygame.display.set_caption(txt)

    def set_time(self, initial, increment):
        self.timer.set(initial, increment)

    def stop_time(self):
        self.timer.stop()
        self.timer.reset()

    def refresh_time(self):
        self.timer.update()
        if self.timer.get_opponent(self.color) < 0:
            self.cbs['timeout']()
        self.draw_timers()
        return True

    def update_time(self, w, b):
        self.timer.set_clocks(w, b)
        if not self.timer.start_time:
            self.timer.start()

    def switch_time(self):
        self.timer.switch()

    def box(self, rect, fill=None, border=None, blit=None, attr=None):
        if fill:
            self.screen.fill(fill, rect)
        if border:
            pygame.draw.rect(self.screen, border, rect, 1)
        if blit:
            self.screen.blit(blit, rect)
        if attr:
            self.screen.blit(getattr(self, str(attr)), rect)
        if fill or border or blit or attr:
            pygame.display.update(rect)

    def adjust_perspective(self, x, y):
        if self.color == 'white':
            y = 7-y
        else:
            x = 7-x
        return x, y

    def get_algebraic(self, x, y):
        x, y = self.adjust_perspective(x, y)
        return from_tile([x, y])

    def get_move(self):
        self.click.tile(self._x1y1, x_max=7, y_max=7)

    def _x1y1(self, x1, y1):
        self.highlighted = [x1, y1]
        self.box((x1*UNIT, y1*UNIT, UNIT, UNIT), border=HIGHLIGHT)
        self.click.tile(self._x2y2, x_max=7, y_max=7)

    def _x2y2(self, x2, y2):
        self.cbs['move'](self.get_algebraic(*self.highlighted), self.get_algebraic(x2, y2))

    def get_promotion(self):
        choices = self.color == 'white' and ['Q','R','B','N'] or ['q','r','b','n']
        self.screen.fill(HIGHLIGHT, (8*UNIT, 0, 2*UNIT, HALF))
        c = 0
        for letter in choices:
            self.box((8*UNIT + c*HALF, 0, HALF, HALF), attr="%s_small"%letter)
            c += 1
        def cb(x, y):
            self.draw_logo()
            self.cbs['promotion'](choices[x-16].upper())
        self.click.tile(cb, HALF, x_min=16, y_max=0)

    def get_time_controls(self):
        self.seeking = True
        ini_square = {2:2,3:5,4:10,5:20}
        inc_square = {2:0,3:2,4:5,5:12}
        def draw_options(txt, ops):
            self.box(BANNER_RECT, fill=SIDE, border=HIGHLIGHT, blit=self.timer_font.render(txt, 1, BANNER_COLOR))
            for tile, option in ops.items():
                self.box((tile*UNIT, 4*UNIT, UNIT, UNIT), fill=self.get_color(tile, 4), blit=self.timer_font.render(str(option), 1, MOVES_COLOR))
        def get_initial(x, y):
            initial = ini_square[x]*60
            def get_increment(x, y):
                increment = inc_square[x]
                self.seeking = False
                self.cbs['seek'](initial, increment)
            draw_options("Select Increment", inc_square)
            self.click.tile(get_increment, x_min=2, x_max=5, y_min=4, y_max=4)
        draw_options("Select Initial Time", ini_square)
        self.click.tile(get_initial, x_min=2, x_max=5, y_min=4, y_max=4)

    def list_seeks(self, smalls, bigs):
        if self.seeking:
            self.box(MOVES_RECT, fill=SIDE, blit=self.text_font.render("_seeks_", 1, MOVES_COLOR))
            for y in range(len(smalls)):
                self.screen.blit(self.move_font.render(smalls[y], 1, MOVES_COLOR), (8*UNIT, (3+y)*HALF))
            for y in range(len(bigs)):
                self.screen.blit(self.move_font.render(bigs[y], 1, MOVES_COLOR), (9*UNIT, (3+y)*HALF))
            pygame.display.update(MOVES_RECT)

    def unselect(self):
        x, y = self.highlighted
        self.box((x*UNIT, y*UNIT, UNIT, UNIT), border=self.get_color(x,y))

    def capture(self, piece):
        side = piece.color == 'black' and 1 or 0
        pos = self.captured[piece.color]
        pos[0] += 1
        if pos[0] == 8:
            pos[0] = 0
            pos[1] += 1
        self.box((side*4*UNIT+pos[0]*HALF, (17+pos[1])*HALF, HALF, HALF), attr='%s_small'%piece)

    def text(self, msg):
        self.box(TEXT_RECT, fill=SIDE, blit=self.text_font.render(msg, 1, TEXT_COLOR))

    def draw_moves(self, moves):
        self.screen.fill(SIDE, MOVES_RECT)
        x = 8*UNIT
        c = 0
        for move in moves:
            text = self.move_font.render(move, 1, MOVES_COLOR)
            self.screen.blit(text, (x, (2+c)*HALF))
            c += 1
        pygame.display.update(MOVES_RECT)

    def draw_timers(self):
        colors = [WHITE, BLACK]
        c = 0
        for time in self.timer.get():
            self.box((8*UNIT, 8*UNIT+c*HALF*3/2, 2*UNIT, HALF*3/2), fill=colors[c], border=HIGHLIGHT, blit=self.timer_font.render(time, 1, TRANS))
            c += 1

    def draw_logo(self):
        self.screen.fill(SIDE, (8*UNIT, 0, 2*UNIT, HALF))
        c = 0
        for letter in ['m','i','c','s']:
            self.box((8*UNIT+c*HALF, 0, HALF, HALF), attr=letter)
            c += 1

    def reset(self, color):
        self.color = color
        for x in range(8):
            for y in range(8):
                self.update((x,y), None)
        self.draw_logo()
        c = 0
        for color in [BLACK, WHITE]:
            self.box((c*4*UNIT, 17*HALF, 4*UNIT, UNIT), fill=color, border=TRANS)
            c += 1
        self.draw_timers()
        for name, x, y in [ ['draw',0,0], ['new',1,0], ['save',0,1], ['quit',1,1] ]:
            r = ((8+x)*UNIT, (14+y)*HALF, UNIT, HALF)
            self.box(r, attr='b_%s'%name)
            self.click.add_interrupt(r, self.cbs[name])
        r = (8*UNIT, HALF, 2*UNIT, HALF)
        self.box(r, blit=self.fullscreen)
        self.click.add_interrupt(r, self.toggle_fs)

    def toggle_fs(self):
        pygame.display.toggle_fullscreen()

    def get_color(self, x, y):
        return (x+y)%2 and BLACK or WHITE

    def update(self, (y,x), piece):
        x, y = self.adjust_perspective(x,y)
        self.box((x*UNIT, y*UNIT, UNIT, UNIT), fill=self.get_color(x, y), attr=piece)