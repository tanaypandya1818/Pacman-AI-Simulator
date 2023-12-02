##################################################
## Core file for Pacman machine learning project
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

import curses
from time import sleep
from Color import *
import numpy as np

from Maze import Maze
from MazeObject import MazeObject

# Global configuration
maze_size = 32
frame_per_second = 30


def main(screen):
    curses.start_color()
    Color.initialize()

    # Term options
    screen.clear()
    curses.noecho()  # Do not echo keys back to the client
    curses.cbreak()  # Do not wait for Enter key to be pressed.
    curses.curs_set(False)  # Turn off blinking cursor
    screen.nodelay(True)  # Turn off keystroke waiting
    curses.use_default_colors()  # Use terminal color

    # Maze setup
    maze = Maze(maze_size, wall_coverage=0.2, filled_reward=False, seed=0)

    # Main UI loop
    while True:
        # Move agent
        maze.play()

        # Re-draw
        screen.refresh()
        maze.refresh()
        screen.getch()

        # Wait for next frame
        sleep(1 / frame_per_second)


curses.wrapper(main)
