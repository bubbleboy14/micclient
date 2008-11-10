import pygame, string
from config import UNIT, WIDTH, HEIGHT

class Input(object):
    def __init__(self, quit_cb, input_cb, chat_cb):
        pygame.event.set_allowed(None)
        pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
        pygame.event.set_allowed(pygame.KEYDOWN)
        pygame.event.set_allowed(pygame.KEYUP)
        pygame.event.set_allowed(pygame.QUIT)
        self.interrupts = {}
        self.quit_cb = quit_cb
        self.input_cb = input_cb
        self.chat_cb = chat_cb
        self.chat_str = ''
        self.click_cb = None
        self.shift = False
        self.shifter = string.maketrans(string.ascii_lowercase+"1234567890`-=[]\\;',./", string.ascii_uppercase+'!@#$%^&*()~_+{}|:"<>?')

    def poll(self):
        event = pygame.event.poll()
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            for [x1, y1, x2, y2], int_cb in self.interrupts.items():
                if x > x1 and x < x1+x2 and y > y1 and y < y1+y2:
                    int_cb()
                    return True
            if self.click_cb:
                cb = self.click_cb
                self.click_cb = None
                cb(x, y)
        elif event.type == pygame.KEYDOWN:
            if event.key > 32 and event.key < 128 or event.key == 20:
                # normal input
                self.chat_str += self.shift and string.translate(chr(event.key), self.shifter) or chr(event.key)
            #elif event.key in [1,2,3,4,6] or event.key > 15 and event.key < 33:
            elif event.key == pygame.K_SPACE:
                # space
                self.chat_str += " "
            elif event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                # shift on
                self.shift = True
            elif event.key == pygame.K_CAPSLOCK:
                # capslock
                self.shift = not self.shift
            elif self.chat_str:
                #if event.key in [10, 13]:
                if event.key == pygame.K_RETURN:
                    # enter
                    self.chat_cb(self.chat_str)
                    self.chat_str = ''
                elif event.key == pygame.K_BACKSPACE:
                    # delete
                    self.chat_str = self.chat_str[:-1]
            else:
                return True
            self.input_cb(self.chat_str)
        elif event.type == pygame.KEYUP and event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
            # shift off
            self.shift = False
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
                self.click_cb = cb2
            else:
                cb(x, y)
        self.click_cb = cb2