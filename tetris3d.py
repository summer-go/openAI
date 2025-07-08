import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random

# Board dimensions
BOARD_WIDTH = 4
BOARD_HEIGHT = 10
BOARD_DEPTH = 4

CUBE_SIZE = 1

# Define tetromino shapes as lists of (x, y, z)
TETROMINOES = {
    'I': [(0,0,0), (1,0,0), (2,0,0), (3,0,0)],
    'L': [(0,0,0), (0,1,0), (0,2,0), (1,2,0)],
    'J': [(1,0,0), (1,1,0), (1,2,0), (0,2,0)],
    'O': [(0,0,0), (1,0,0), (0,1,0), (1,1,0)],
    'S': [(1,0,0), (2,0,0), (0,1,0), (1,1,0)],
    'T': [(0,0,0), (1,0,0), (2,0,0), (1,1,0)],
    'Z': [(0,0,0), (1,0,0), (1,1,0), (2,1,0)],
}

class Piece:
    def __init__(self, shape):
        self.shape = shape
        self.blocks = [list(p) for p in TETROMINOES[shape]]
        self.position = [BOARD_WIDTH // 2, BOARD_HEIGHT - 1, BOARD_DEPTH // 2]

    def rotate_x(self):
        for b in self.blocks:
            b[1], b[2] = b[2], -b[1]

    def rotate_y(self):
        for b in self.blocks:
            b[0], b[2] = b[2], -b[0]

    def rotate_z(self):
        for b in self.blocks:
            b[0], b[1] = -b[1], b[0]

    def get_cells(self):
        return [(b[0] + self.position[0],
                 b[1] + self.position[1],
                 b[2] + self.position[2])
                for b in self.blocks]

class Board:
    def __init__(self):
        self.grid = [[[0 for _ in range(BOARD_DEPTH)] for _ in range(BOARD_WIDTH)]
                     for _ in range(BOARD_HEIGHT)]

    def inside(self, x, y, z):
        return 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT and 0 <= z < BOARD_DEPTH

    def collision(self, cells):
        for x, y, z in cells:
            if not self.inside(x, y, z) or self.grid[y][x][z]:
                return True
        return False

    def lock_piece(self, piece):
        for x, y, z in piece.get_cells():
            if self.inside(x, y, z):
                self.grid[y][x][z] = 1

    def clear_layers(self):
        new_grid = [layer for layer in self.grid if not all(all(row) for row in layer)]
        cleared = BOARD_HEIGHT - len(new_grid)
        for _ in range(cleared):
            new_grid.append([[0]*BOARD_DEPTH for _ in range(BOARD_WIDTH)])
        self.grid = new_grid

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600), DOUBLEBUF|OPENGL)
        gluPerspective(45, (800/600), 0.1, 50.0)
        glTranslatef(-BOARD_WIDTH/2, -BOARD_HEIGHT/2, -20)
        self.board = Board()
        self.current = Piece(random.choice(list(TETROMINOES.keys())))
        self.drop_time = 0

    def draw_cube(self, x, y, z, color=(1,1,1)):
        glPushMatrix()
        glTranslatef(x, y, z)
        glBegin(GL_QUADS)
        glColor3fv(color)
        # front
        glVertex3f(0,0,0)
        glVertex3f(1,0,0)
        glVertex3f(1,1,0)
        glVertex3f(0,1,0)
        # back
        glVertex3f(0,0,1)
        glVertex3f(1,0,1)
        glVertex3f(1,1,1)
        glVertex3f(0,1,1)
        # left
        glVertex3f(0,0,0)
        glVertex3f(0,1,0)
        glVertex3f(0,1,1)
        glVertex3f(0,0,1)
        # right
        glVertex3f(1,0,0)
        glVertex3f(1,1,0)
        glVertex3f(1,1,1)
        glVertex3f(1,0,1)
        # top
        glVertex3f(0,1,0)
        glVertex3f(1,1,0)
        glVertex3f(1,1,1)
        glVertex3f(0,1,1)
        # bottom
        glVertex3f(0,0,0)
        glVertex3f(1,0,0)
        glVertex3f(1,0,1)
        glVertex3f(0,0,1)
        glEnd()
        glPopMatrix()

    def draw_board(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        for y, layer in enumerate(self.board.grid):
            for x, row in enumerate(layer):
                for z, cell in enumerate(row):
                    if cell:
                        self.draw_cube(x, y, z, color=(0.5,0.5,0.5))
        for x, y, z in self.current.get_cells():
            self.draw_cube(x, y, z, color=(1,0,0))
        pygame.display.flip()

    def move(self, dx, dy, dz):
        self.current.position[0] += dx
        self.current.position[1] += dy
        self.current.position[2] += dz
        if self.board.collision(self.current.get_cells()):
            self.current.position[0] -= dx
            self.current.position[1] -= dy
            self.current.position[2] -= dz
            return False
        return True

    def rotate(self, axis):
        if axis == 'x':
            self.current.rotate_x()
        elif axis == 'y':
            self.current.rotate_y()
        else:
            self.current.rotate_z()
        if self.board.collision(self.current.get_cells()):
            # undo rotation
            if axis == 'x':
                for _ in range(3):
                    self.current.rotate_x()
            elif axis == 'y':
                for _ in range(3):
                    self.current.rotate_y()
            else:
                for _ in range(3):
                    self.current.rotate_z()

    def drop_piece(self):
        if not self.move(0, -1, 0):
            self.board.lock_piece(self.current)
            self.board.clear_layers()
            self.current = Piece(random.choice(list(TETROMINOES.keys())))
            if self.board.collision(self.current.get_cells()):
                return False
        return True

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_LEFT:
                        self.move(-1, 0, 0)
                    elif event.key == K_RIGHT:
                        self.move(1, 0, 0)
                    elif event.key == K_UP:
                        self.rotate('z')
                    elif event.key == K_DOWN:
                        self.rotate('x')
                    elif event.key == K_a:
                        self.rotate('y')
                    elif event.key == K_SPACE:
                        while self.move(0, -1, 0):
                            pass
                        self.drop_piece()

            if pygame.time.get_ticks() - self.drop_time > 500:
                if not self.drop_piece():
                    running = False
                self.drop_time = pygame.time.get_ticks()
            self.draw_board()
            clock.tick(60)
        pygame.quit()

if __name__ == '__main__':
    Game().run()
