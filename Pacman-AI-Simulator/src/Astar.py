import heapq
from MazeObject import MazeObject
from Action import Action
import time
import random

class AStar:
    def __init__(self, size, start, goal):
        self.maze_size = size  # Update maze_size here
        self.start = start
        self.goal = goal
        self.came_from = {}
        self.g_score = {}
        self.f_score = {}

        # Initialize g_score and f_score based on maze size
        for row in range(size):
            for col in range(size):
                cell = (row, col)
                self.g_score[cell] = float('inf')
                self.f_score[cell] = float('inf')

        self.g_score[start] = 0
        self.f_score[start] = self.heuristic(start)

    def heuristic(self, cell):
        agent_distance = abs(cell[0] - self.goal[0]) + abs(cell[1] - self.goal[1])
        return agent_distance

    def find_path(self, maze):
        open_set = [(0, self.start)]
        # time.sleep(0.1)

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == self.goal:
                return self.reconstruct_path(current)

            for move in maze._move:  # Use the maze object to get valid moves
                neighbor = (current[0] + maze._move[Action(move)][0], current[1] + maze._move[Action(move)][1])

                # Check if neighbor is out of bounds
                if (
                        neighbor[0] < 0 or neighbor[0] >= maze._size or
                        neighbor[1] < 0 or neighbor[1] >= maze._size
                ):
                    continue  # Skip this move

                if maze._data[neighbor[0]][neighbor[1]] == MazeObject.WALL.value:
                    continue

                tentative_g_score = self.g_score[current] + 1

                if tentative_g_score < self.g_score[neighbor]:
                    self.came_from[neighbor] = current
                    self.g_score[neighbor] = tentative_g_score
                    self.f_score[neighbor] = tentative_g_score + self.heuristic(neighbor)

                    heapq.heappush(open_set, (self.f_score[neighbor], neighbor))

        return None

    def reconstruct_path(self, current):
        path = [current]
        while current in self.came_from:
            current = self.came_from[current]
            path.append(current)
        path.reverse()
        return path

