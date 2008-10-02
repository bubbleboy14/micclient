import pygame
from config import UNIT, WIDTH, HEIGHT

class Input(object):
    def __init__(self, quit_cb, input_cb, chat_cb):
        pygame.event.set_allowed(None)
        pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
        pygame.event.set_allowed(pygame.KEYDOWN)
        pygame.event.set_allowed(pygame.QUIT)
        self.interrupts = {}
        self.quit_cb = quit_cb
        self.input_cb = input_cb
        self.chat_cb = chat_cb
        self.chat_str = ''
        self.click_cb = None

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
            if event.key < 123:
                letter = chr(event.key)
                if letter.isalpha():
                    self.chat_str += letter
                elif self.chat_str:
                    if letter in " ',.":
                        self.chat_str += letter
                    elif letter == '\r':
                        self.chat_cb(self.chat_str)
                        self.chat_str = ''
                    elif self.chat_str and letter == '\x08':
                        self.chat_str = self.chat_str[:-1]
                self.input_cb(self.chat_str)
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