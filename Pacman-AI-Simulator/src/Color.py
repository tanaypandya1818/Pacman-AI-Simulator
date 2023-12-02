##################################################
## Enumeration for colors
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

import curses


class Color:
    WHITE = None
    BLUE = None
    YELLOW = None
    RED = None
    GREEN = None
    CYAN = None
    MAGENTA = None

    @staticmethod
    def initialize():
        # This is oddly formatted cause start_color() and initscr() has to be called by main first...
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # 1: White
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)  # 2: Blue
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # 3: Yellow
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)  # 4: Red
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)  # 5: Green
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)  # 6: Cyan
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # 7: Magenta

        Color.WHITE = curses.color_pair(1)
        Color.BLUE = curses.color_pair(2)
        Color.YELLOW = curses.color_pair(3)
        Color.RED = curses.color_pair(4)
        Color.GREEN = curses.color_pair(5)
        Color.CYAN = curses.color_pair(6)
        Color.MAGENTA = curses.color_pair(7)
