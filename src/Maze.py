##################################################
## Contains all the maze information and valid
## operations to perform
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

import numpy as np
import copy
from collections import deque
from time import sleep

import numpy.random

from MazeObject import MazeObject
from Action import Action
from Color import *
from Agent import Agent
from Astar import *
from AstarAgent import *
import random
import sys


class Maze:
    def __init__(self, size, data=None, wall_coverage=None, filled_reward=False, seed=0):
        self._sprite = {MazeObject.WALL: ("█", "█"), MazeObject.EMPTY: (" ", " "),
                        MazeObject.REWARD: (".", " "), MazeObject.AGENT: ("A", " "), "GHOST": ("G", " ")}
        self._static_color = {MazeObject.WALL: Color.BLUE,
                              MazeObject.EMPTY: Color.MAGENTA,
                              MazeObject.REWARD: Color.WHITE}
        self._move = {Action.STAY: (0, 0), Action.UP: (-1, 0), Action.DOWN: (1, 0),
                      Action.LEFT: (0, -1), Action.RIGHT: (0, 1)}
        self._size = size  # Maze size
        self._wall_coverage = wall_coverage  # Percentage of the maze wall should be covered
        self._filled_reward = filled_reward  # If reward should be filled within non-wall space
        self._seed = seed

        # Main game box
        self._box = curses.newwin(self._size + 2, (self._size + 1) * 2, 4, 0)
        self._box.attrset(Color.BLUE)
        self._box.box()

        # Agent properties
        self._agents = []  # List of agents
        self._red_zone = []  # Coordinates of hostile agents
        self._green_zone = []  # Coordinates of non-hostile agents
        self._reward_positions = []  # Store position of rewards
        self._current_target_reward = None  # Current target reward

        # Score box
        self._score_box = curses.newwin(self._size + 2, (self._size + 1) * 2, 0, 0)
        self._score = 0
        self._iteration = 0

        # Render score box
        for line in range(4):
            self._score_box.addstr(line, 0, " " * (self._size + 1) * 2, self._static_color[MazeObject.REWARD])

        self._score_box.addstr(1, 0, " ITERATIONS", curses.A_BOLD | Color.WHITE)
        self._score_box.addstr(1, (self._size + 1) * 2 - 14, "🍒 HIGH SCORE", curses.A_BOLD | Color.WHITE)
        self._update_score()
        self._update_iteration()

        # Initialize maze data
        self._data = data
        self._initial_agents = []

        self._init_objects()
        self.hill_Climbing()
        self._initial_data = np.copy(self._data)
        self._initial_agents = copy.deepcopy(self._agents)
        self._init_draw()


    def _init_objects(self):
        if self._data is None:
            if self._wall_coverage < 0 or self._wall_coverage >= 1:
                raise Exception("Coverage should be between 0.0 and 1.0")

            non_wall_obj = MazeObject.EMPTY.value
            if self._filled_reward:
                non_wall_obj = MazeObject.REWARD.value

            numpy.random.seed(self._seed)
            self._data = np.random.choice([MazeObject.WALL.value, non_wall_obj], size=(self._size, self._size),
                                          p=[self._wall_coverage, 1.0 - self._wall_coverage])

            # Store reward positions in the _reward_positions list
            self._reward_positions = np.argwhere(self._data == MazeObject.REWARD.value).tolist()
            self._reward_positions = [tuple(sub) for sub in self._reward_positions] # Convert to tuples

            # If filled_reward is False, add rewards automatically
            if not self._filled_reward:
                self._add_rewards()

        self._agents = []
        self.add_agent(Color.YELLOW, False)
        self.add_agent(Color.RED, True, self._sprite["GHOST"])
        # self.add_agent(Color.GREEN, True, self._sprite["GHOST"])
        # self.add_agent(Color.CYAN, True, self._sprite["GHOST"])
        # self.add_agent(Color.MAGENTA, True, self._sprite["GHOST"])

    def _add_rewards(self):
        """
        Add rewards to the maze. This function is called automatically if filled_reward is False.
        """
        num_rewards_to_add = 100  # You can adjust this number
        for _ in range(num_rewards_to_add):
            while self.add_reward() == -1:
                self.add_reward()

    def _init_draw(self):
        # Initialize object drawing
        for j in range(0, self._size):
            for i in range(0, self._size):
                obj = MazeObject(self._data[j][i])
                char = self._sprite[obj]

                self._box.addstr(j + 1, 2 * i + 1, char[0], self._static_color[obj])
                self._box.addstr(j + 1, 2 * i + 2, char[1], self._static_color[obj])

        for agent in self._initial_agents:
            self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 1, agent.get_sprite()[0], agent.get_color())
            self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 2, agent.get_sprite()[1], agent.get_color())

    def bfs(self, agent):
        start = agent.get_position()
        queue = deque([start])
        visited = [[False] * self._size for _ in range(self._size)]
        visited[start[0]][start[1]] = True
        num_reachable = 1
        while len(queue) > 0:
            current = queue.popleft()
            valid_move = self.get_agent_valid_move(current[0], current[1])
            for move in valid_move:
                new_y = current[0] + self._move[move][0]
                new_x = current[1] + self._move[move][1]
                if not visited[new_y][new_x]:
                    visited[new_y][new_x] = True
                    queue.append((new_y, new_x))
                    num_reachable += 1
        return num_reachable

    def energy(self):
        return self.bfs(self._agents[0])

    def hill_Climbing(self):
        while True:
            walls = []
            for j in range(0, self._size):
                for i in range(0, self._size):
                    if self._data[j][i] == MazeObject.WALL.value:
                        walls.append((j, i))
            num_walls = len(walls)
            num_cells = self._size * self._size - num_walls
            current_energy = self.energy()
            if current_energy == num_cells:
                return
            np.random.shuffle(walls)
            for index in range(num_walls):
                remove_wall = walls[index]

                empty_data = MazeObject.EMPTY.value
                if self._filled_reward:
                    empty_data = MazeObject.REWARD.value

                self._data[remove_wall[0]][remove_wall[1]] = empty_data
                new_energy = self.energy() - 1
                if new_energy <= current_energy:
                    self._data[remove_wall[0]][remove_wall[1]] = MazeObject.WALL.value
                else:
                    current_energy = new_energy + 1
                    num_cells += 1

                if current_energy == num_cells:
                    return
            # restart
            self._init_objects()

    def _update_score(self):
        self._score_box.addstr(2, (self._size + 1) * 2 - 1 - len(f'{self._score:08}'), f'{self._score:08}',
                               Color.WHITE)

    def _update_iteration(self):
        self._score_box.addstr(2, 0, " " + f'{self._iteration:06}', Color.WHITE)

    def add_reward(self, y=None, x=None):
        """
        Add reward to the maze. If x and y not given, spawn random on a valid spot

        :param y: y coordinate of the reward (Optional)
        :param x: x coordinate of the reward (Optional)
        :return: tuple of (y, x)
        """

        if x is None or y is None:
            while True:  # Random x and y
                rand_x = np.random.randint(0, self._size)
                rand_y = np.random.randint(0, self._size)

                if (self._data[rand_y][rand_x] == MazeObject.WALL.value or
                        (rand_y, rand_x) in self._red_zone or (rand_y, rand_x) in self._green_zone):
                    continue

                x = rand_x
                y = rand_y
                break
        elif self._data[y][x] == MazeObject.WALL.value or self._data[y][x] == MazeObject.REWARD.value or (y, x) in self._red_zone or (y, x) in self._green_zone:
            return -1  # Not a valid spawn point

        if self._data[y][x] == MazeObject.WALL.value or self._data[y][x] == MazeObject.REWARD.value or (y, x) in self._red_zone or (y, x) in self._green_zone:
            return -1  # Not a valid spawn point

        # Store position in the list
        reward_position = (y, x)
        self._reward_positions.append(reward_position)
        
        # Store and render
        self._data[y][x] = MazeObject.REWARD.value
        self._box.addstr(y + 1, 2 * x + 1, self._sprite[MazeObject.REWARD][0], Color.WHITE)
        self._box.addstr(y + 1, 2 * x + 2, self._sprite[MazeObject.REWARD][1], Color.WHITE)

        return tuple([y, x])

    def add_agent(self, color, is_hostile, sprite=None):
        """
        Add new agent into the maze, given color of the agent, and if agent is hostile

        :param color: color of the agent, use Color class
        :param is_hostile: whether the agent consumes reward and catch non-hostile agents
        :param sprite: custom sprite for this agent
        :return: index of newly added agent
        """

        agent_sprite = sprite
        agent = None

        # Init sprite
        if agent_sprite is None:
            agent_sprite = self._sprite[MazeObject.AGENT]

        while True:
            x = np.random.randint(0, self._size - 1)
            y = np.random.randint(0, self._size - 1)

            if self._data[y][x] == MazeObject.WALL.value or (y, x) in self._red_zone or (y, x) in self._green_zone:
                continue
            else:
                agent = Agent(color, is_hostile, (y, x), agent_sprite)
                break

        self._agents.append(agent)

        if is_hostile:
            self._red_zone.append(agent.get_position())
            self._green_zone.append(0)
        else:
            self._green_zone.append(agent.get_position())
            self._red_zone.append(0)

        return len(self._agents) - 1

    def refresh(self):
        """
        Refresh entire box, only call after each frame is drawn
        """

        self._score_box.refresh()
        self._box.refresh()

    def get_agent_valid_move(self, y, x):
        """
        Return list of valid moves, given agent index

        :param index: index of the agent
        :return: list of valid Actions
        """

        moves = []

        if ((y - 1) >= 0 and
                not (self._data[y - 1][x] == MazeObject.WALL.value)):
            moves.append(Action.UP)
        if ((y + 1) < self._size and
                not (self._data[y + 1][x] == MazeObject.WALL.value)):
            moves.append(Action.DOWN)
        if ((x - 1) >= 0 and
                not (self._data[y][x - 1] == MazeObject.WALL.value)):
            moves.append(Action.LEFT)
        if ((x + 1) < self._size and
                not (self._data[y][x + 1] == MazeObject.WALL.value)):
            moves.append(Action.RIGHT)

        return moves

    def reset(self):
        """
        Reset the maze to its original generation and re-add rewards to their original positions
        """

        # Store the current reward positions
        self._reward_positions = copy.deepcopy(self._reward_positions)

        # Update scoreboard
        self._iteration = self._iteration + 1
        self._update_iteration()
        self._score = 0
        self._update_score()

        # Re-draw initial state
        # self._data = np.copy(self._initial_data)
        self._agents = []
        self._agents = copy.deepcopy(self._initial_agents)
        self._init_draw()

    def get_agent_pos(self):
        for agent in self._agents:
            if not agent.is_hostile():
                return agent.get_position()

    def get_enemy_pos(self):
        for agent in self._agents:
            if agent.is_hostile():
                return agent.get_position()

    
    def get_closest_reward(self, agent_pos):
        if not self._reward_positions:
            return None

        closest_reward = min(self._reward_positions, key=lambda pos: abs(pos[0] - agent_pos[0]) + abs(pos[1] - agent_pos[1]))
        return closest_reward
    
    
    def get_reward_direction(self, reward_pos, agent_pos, enemy_pos):
        a_star = AStarAgent(self._size, agent_pos, reward_pos, enemy_pos)
        path = a_star.find_path(self)
        direction = Action.STAY
        if path and len(path) > 1:
            next_cell = path[1]
            # Determine the direction to move
            delta_y = next_cell[0] - agent_pos[0]
            delta_x = next_cell[1] - agent_pos[1]

            if delta_x == 0 and delta_y == -1:
                direction = Action.UP
            elif delta_x == 0 and delta_y == 1:
                direction = Action.DOWN
            elif delta_x == -1 and delta_y == 0:
                direction = Action.LEFT
            elif delta_x == 1 and delta_y == 0:
                direction = Action.RIGHT

        return direction

    
    def get_enemy_direction(self, enemy_pos, agent_pos, move_probability=0.5, random_move_probability=0.3):
        if random.random() < move_probability:
            valid_moves = self.get_agent_valid_move(enemy_pos[0], enemy_pos[1])

            if random.random() < random_move_probability and valid_moves:
                # Randomly choose a valid direction
                direction = random.choice(valid_moves)
            else:
                # Use AStar to find the path
                a_star = AStar(self._size, enemy_pos, agent_pos)
                path = a_star.find_path(self)
                direction = Action.STAY

                if path and len(path) > 1:
                    next_cell = path[1]
                    # Determine the direction to move
                    delta_y = next_cell[0] - enemy_pos[0]
                    delta_x = next_cell[1] - enemy_pos[1]

                    if delta_x == 0 and delta_y == -1 and Action.UP in valid_moves:
                        direction = Action.UP
                    elif delta_x == 0 and delta_y == 1 and Action.DOWN in valid_moves:
                        direction = Action.DOWN
                    elif delta_x == -1 and delta_y == 0 and Action.LEFT in valid_moves:
                        direction = Action.LEFT
                    elif delta_x == 1 and delta_y == 0 and Action.RIGHT in valid_moves:
                        direction = Action.RIGHT
        else:
            direction = Action.STAY

        return direction

    

    def move_agent(self, index, direction=None):
        """
        Move agent within the maze, given agent index and direction. If direction isn't given,
        agent will randomly choose from the list of valid Actions

        :param index: index of the agent
        :param direction: Actions enum to let the system know where to move the agent (Optional)
        :return: 0 for success, otherwise -1
        """

        # Set agent into an obj
        agent = self._agents[index]

        valid_moves = self.get_agent_valid_move(agent.get_y(), agent.get_x())

        # Random if not given
        if direction is None:
            # Use get_closest_reward to get the closest reward
            closest_reward = self.get_closest_reward(agent.get_position())

            if closest_reward == agent.get_position():
                # Remove the closest reward from the list
                self._reward_positions.remove(closest_reward)
                self._data[closest_reward[0]][closest_reward[1]] = MazeObject.EMPTY.value
                if len(self._reward_positions) == 0:
                    print(f"Agent wins the game after losing {self._iteration} Times!")
                    sys.exit()
            
            # Use get_reward_direction to consider both reward and enemy positions
            direction = self.get_reward_direction(closest_reward, agent.get_position(), self.get_enemy_pos())

        elif direction.value not in valid_moves:
            return -1  # Failure

        # if the agent is an enemy
        if agent.is_hostile():
            direction = self.get_enemy_direction(agent.get_position(), self.get_agent_pos())

        # Set old cell to empty/reward
        char = self._sprite[MazeObject(self._data[agent.get_y()][agent.get_x()])]
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 1, char[0], Color.WHITE)
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 2, char[1], Color.WHITE)

        # Set new cell to agent and change tracker
        agent.set_position(agent.get_y() + self._move[direction][0], agent.get_x() + self._move[direction][1])

        # Data update
        if not agent.is_hostile():
            if self._data[agent.get_y()][agent.get_x()] == MazeObject.REWARD.value:
                self._score = self._score + 1
                self._update_score()
            elif agent.get_position() in self._red_zone:
                self.reset()
                return

            self._data[agent.get_y()][agent.get_x()] = MazeObject.EMPTY.value
            self._green_zone[index] = agent.get_position()
        else:
            if agent.get_position() in self._green_zone:
                self.reset()
                return

            self._red_zone[index] = agent.get_position()

        char = agent.get_sprite()
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 1, char[0], agent.get_color())
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 2, char[1], agent.get_color())

        return 0  # Success

    def play(self):
        for index in range(len(self._agents)):
            self.move_agent(index, None)

