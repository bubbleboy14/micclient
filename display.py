import rel, os, pygame
pygame.init()
from chesstools import Timer
from chesstools.move import from_tile
from input import Input
from config import config

sizes = config.sizes
rects = config.rects
colors = config.colors
GAME_COLORS = {'white': colors.bright, 'black':colors.pitch}

class Display(object):
    def __init__(self, move_cb, promotion_cb, draw_cb, new_cb, save_cb, quit_cb, timeout_cb, seek_cb, chat_cb):
        self.cbs = {'move':move_cb, 'promotion':promotion_cb, 'draw':draw_cb, 'new':new_cb, 'save':save_cb, 'quit':quit_cb, 'timeout':timeout_cb, 'seek':seek_cb, 'chat':chat_cb}
        UNIT = sizes.unit
        HALF = sizes.half
        BRIGHT = colors.bright
        for folder in [os.path.join('skins','default',sub) for sub in ['white','black','misc']]:
            for p in next(os.walk(folder))[2]:
                img = pygame.image.load(os.path.join(folder,p))
                if sizes.mult == 2:
                    img = pygame.transform.scale2x(img)
                setattr(self, p[:-4], img)
                piece = getattr(self, p[:-4])
                piece.set_colorkey(colors.green)
                if folder != 'misc':
                    setattr(self, p[:-4]+'_small', pygame.transform.scale(piece, (HALF, HALF)))
        self.set_caption('MICS Chess Client')
        pygame.display.set_icon(self.N_small)
        self.input = Input(quit_cb, self.draw_input, chat_cb)
        rel.timeout(0.05, self.input.poll)
        self.screen = pygame.display.set_mode((int(sizes.width*UNIT),int(sizes.height*UNIT)))
        self.highlighted = None
        self.captured = {'white':[-1,0],'black':[-1,0]}
        self.small_font = pygame.font.Font(None, int(HALF*9/10))
        self.medium_font = pygame.font.Font(None, int(HALF))
        self.banner_font = pygame.font.Font(None, UNIT)
        self.timer_font = pygame.font.Font(None, int(UNIT*8/7))
        self.timer = Timer(300, 0)
        self.ticker = rel.timeout(1, self.refresh_time)
        self.chats = [('',BRIGHT),('',BRIGHT),('',BRIGHT)]
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
        self.input.tile(self._x1y1, x_max=7, y_max=7)

    def _x1y1(self, x1, y1):
        UNIT = sizes.unit
        self.highlighted = [x1, y1]
        self.box((x1*UNIT, y1*UNIT, UNIT, UNIT), border=colors.red)
        self.input.tile(self._x2y2, x_max=7, y_max=7)

    def _x2y2(self, x2, y2):
        self.cbs['move'](self.get_algebraic(*self.highlighted), self.get_algebraic(x2, y2))

    def get_promotion(self):
        UNIT = sizes.unit
        HALF = sizes.half
        choices = self.color == 'white' and ['Q','R','B','N'] or ['q','r','b','n']
        self.screen.fill(colors.red, (8*UNIT, 0, 2*UNIT, HALF))
        c = 0
        for letter in choices:
            self.box((8*UNIT + c*HALF, 0, HALF, HALF), attr="%s_small"%letter)
            c += 1
        def cb(x, y):
            self.draw_logo()
            self.cbs['promotion'](choices[x-16].upper())
        self.input.tile(cb, HALF, x_min=16, y_max=0)

    def get_game_settings(self):
        UNIT = sizes.unit
        self.seeking = True
        ini_square = {2:2,3:5,4:10,5:20}
        inc_square = {2:0,3:2,4:5,5:12}
        var_square = {4:"standard",5:"960"} # room for more!
        def draw_options(txt, ops, big=False):
            self.box(rects.banner, fill=colors.pitch, border=colors.red, blit=self.banner_font.render(txt, 1, colors.banner))
            if big:
                for y, v in list(var_square.items()):
                    for x in range(2,6):
                        self.box((x*UNIT, y*UNIT, UNIT, UNIT), fill=self.get_color(x, y))
                    self.box((2*UNIT, y*UNIT, 4*UNIT, UNIT), border=colors.green, blit=self.banner_font.render(v, 1, colors.red))
            else:
                for tile, option in list(ops.items()):
                    self.box((tile*UNIT, 4*UNIT, UNIT, UNIT), fill=self.get_color(tile, 4), blit=self.banner_font.render(str(option), 1, colors.moves))
        def get_initial(x, y):
            initial = ini_square[x]*60
            def get_increment(x, y):
                increment = inc_square[x]
                def get_variant(x, y):
                    variant = var_square[y]
                    self.seeking = False
                    self.cbs['seek'](initial, increment, variant)
                draw_options("Select Variant", var_square, big=True)
                self.input.tile(get_variant, x_min=2, x_max=5, y_min=4, y_max=5)
            draw_options("Select Increment", inc_square)
            self.input.tile(get_increment, x_min=2, x_max=5, y_min=4, y_max=4)
        draw_options("Select Initial Time", ini_square)
        self.input.tile(get_initial, x_min=2, x_max=5, y_min=4, y_max=4)

    def list_seeks(self, seeks):
        THIRD = sizes.third
        UNIT = sizes.unit
        if self.seeking:
            seeks = seeks[:9]
            rect = [UNIT*8, UNIT, UNIT*2, 2*THIRD]
            for n in range(len(seeks)):
                self.box(rect, fill=colors.pitch, border=colors.bright, blit=self.medium_font.render(seeks[n][0], 1, colors.green))
                rect[1] += THIRD
                self.screen.blit(self.medium_font.render(seeks[n][1], 1, colors.red), rect)
                rect[1] += THIRD
            pygame.display.update(rects.move)

    def unselect(self):
        UNIT = sizes.unit
        x, y = self.highlighted
        self.box((x*UNIT, y*UNIT, UNIT, UNIT), border=self.get_color(x,y))

    def capture(self, piece):
        side = piece.color == 'black' and 1 or 0
        pos = self.captured[piece.color]
        HALF = sizes.half
        pos[0] += 1
        if pos[0] == 8:
            pos[0] = 0
            pos[1] += 1
        self.box((side*4*sizes.unit+pos[0]*HALF, (18+pos[1])*HALF, HALF, HALF), attr='%s_small'%piece)

    def text(self, msg):
        self.box(rects.text, fill=colors.pitch, blit=self.medium_font.render(msg, 1, colors.text))

    def draw_moves(self, moves):
        self.screen.fill(colors.pitch, rects.move)
        UNIT = sizes.unit
        x = 8*UNIT
        c = 0
        for move in moves:
            text = self.medium_font.render(move, 1, colors.moves)
            if text.get_width() > 2*UNIT:
                text = self.small_font.render(move, 1, colors.moves)
            self.screen.blit(text, (x, (2+c)*sizes.half))
            c += 1
        pygame.display.update(rects.move)

    def draw_timers(self):
        cols = [colors.white, colors.black]
        UNIT = sizes.unit
        c = 0
        for time in self.timer.get():
            self.box((8*UNIT, 8*UNIT+c*UNIT, 2*UNIT, UNIT), fill=cols[c], border=colors.red, blit=self.timer_font.render(time, 1, colors.green))
            c += 1

    def _add_chat(self, txt, color):
        if txt:
            test_txt = self.small_font.render(txt, 1, colors.bright)
            txt = txt.split(' ')
            overflow = []
            while len(txt) > 1 and test_txt.get_width() > sizes.chat:
                overflow.append(txt.pop())
                test_txt = self.small_font.render(' '.join(txt), 1, colors.bright)
            self.chats.pop(0)
            self.chats.append((' '.join(txt), color))
            overflow.reverse()
            self._add_chat(' '.join(overflow), color)

    def draw_chat(self, txt=None, player='white'):
        THIRD = sizes.third
        CHAT_RECT = rects.chat
        self._add_chat(txt, GAME_COLORS[player])
        self.box(CHAT_RECT, fill=colors.black, border=colors.bright)
        for x in range(3):
            self.box([CHAT_RECT[0], CHAT_RECT[1]+x*THIRD, CHAT_RECT[2], THIRD], blit=self.small_font.render(self.chats[x][0], 1, self.chats[x][1]))

    def draw_logo(self):
        UNIT = sizes.unit
        HALF = sizes.half
        self.screen.fill(colors.pitch, (8*UNIT, 0, 2*UNIT, HALF))
        c = 0
        for letter in ['m','i','c','s']:
            self.box((8*UNIT+c*HALF, 0, HALF, HALF), attr=letter)
            c += 1

    def draw_input(self, txt=''):
        self.box(rects.input, fill=colors.pitch, border=colors.bright, blit=self.small_font.render(txt, 1, colors.bright))

    def reset(self, color):
        UNIT = sizes.unit
        HALF = sizes.half
        self.color = color
        for x in range(8):
            for y in range(8):
                self.update((x,y), None)
        self.draw_logo()
        c = 0
        for color in [colors.black, colors.white]:
            self.box((c*4*UNIT, 9*UNIT, 4*UNIT, UNIT), fill=color, border=colors.green)
            c += 1
        self.draw_timers()
        self.draw_chat()
        self.draw_input()
        for name, x, y in [ ['draw',0,0], ['new',1,0], ['save',0,1], ['quit',1,1] ]:
            r = ((8+x)*UNIT, (14+y)*HALF, UNIT, HALF)
            self.box(r, attr='b_%s'%name)
            self.input.add_interrupt(r, self.cbs[name])
        r = (8*UNIT, HALF, 2*UNIT, HALF)
        self.box(r, blit=self.fullscreen)
        self.input.add_interrupt(r, self.toggle_fs)

    def toggle_fs(self):
        pygame.display.toggle_fullscreen()

    def get_color(self, x, y):
        return (x+y)%2 and colors.black or colors.white

    def update(self, xxx_todo_changeme, piece):
        UNIT = sizes.unit
        (y,x) = xxx_todo_changeme
        x, y = self.adjust_perspective(x,y)
        self.box((x*UNIT, y*UNIT, UNIT, UNIT), fill=self.get_color(x, y), attr=piece)
