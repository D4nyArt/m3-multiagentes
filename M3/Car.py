import math, numpy
from Settings import Settings
from pygame.locals import *
from Cubo import Cubo
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy
import math
import random
from OpenGL.GL import *

settings = Settings("Settings.yaml")


tam_tablero = settings.DimBoard * 2  # Cambia esto según el tamaño real de tu tablero
num_celdas = 8
tam_celda = tam_tablero / num_celdas  # Tamaño de cada celda en el tablero

# Crear la lista de nodos en el centro de cada celda dentro de la intersección
nodos = []

for i in range(num_celdas):
    for j in range(num_celdas):
        # Agregar nodos solo dentro de la intersección en forma de cruz
        if i in range(3, 5) or j in range(3, 5):
            # Calcular las coordenadas del centro de la celda
            x_centro = -tam_tablero / 2 + (i + 0.5) * tam_celda
            z_centro = -tam_tablero / 2 + (j + 0.5) * tam_celda
            nodos.append([x_centro, 0, z_centro])  # Altura (Y) es 0


class Car:
    def __init__(self, dim, vel, textures, idx, position, currentNode, searchStyle):
        self.dim = dim
        self.idx = idx
        self.Position = position  # Agent's current position
        self.Direction = numpy.zeros(3)
        self.angle = 0
        self.vel = vel
        self.textures = textures
        self.searchStyle = searchStyle  # 0: vertical path, 1: horizontal path

        # Control variables for platform movement
        self.platformHeight = -1.5
        self.platformUp = False
        self.platformDown = False

        # Control variable for collisions
        self.radiusCol = 5

        # Grid configuration
        self.grid_size = 8
        self.grid = numpy.array(
            [
                [-1, -1, -1, 0, 0, -1, -1, -1],
                [-1, -1, -1, 0, 0, -1, -1, -1],
                [-1, -1, -1, 0, 0, -1, -1, -1],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [-1, -1, -1, 0, 0, -1, -1, -1],
                [-1, -1, -1, 0, 0, -1, -1, -1],
                [-1, -1, -1, 0, 0, -1, -1, -1],
            ]
        )

        # Create mapping between node indices and grid positions
        self.node_to_grid = {}
        self.grid_to_node = {}

        node_idx = 0
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.grid[i][j] == 0:
                    self.node_to_grid[node_idx] = (i, j)
                    self.grid_to_node[(i, j)] = node_idx
                    node_idx += 1

        # Define the vertical path through column 4
        self.vertical_path_nodes = []
        for i in range(self.grid_size):
            if self.grid[i][4] == 0:
                node = self.grid_to_node[(i, 4)]
                self.vertical_path_nodes.append(node)
        self.vertical_path_nodes.sort()
        self.path_index_vertical = 0  # Starting index in the vertical path

        # Define the horizontal path through row 4
        self.horizontal_path_nodes = []
        for j in range(self.grid_size):
            if self.grid[4][j] == 0:
                node = self.grid_to_node[(4, j)]
                self.horizontal_path_nodes.append(node)
        self.horizontal_path_nodes.sort()
        self.path_index_horizontal = 0  # Starting index in the horizontal path

        # Set currentNode and nextNode
        self.currentNode = currentNode
        self.nextNode = self.currentNode

        # Initialize agent's position at the starting node
        self.Position = self.get_node_position(self.currentNode).copy()

    def get_node_coordinates(self, node_index):
        """Convert node index to grid coordinates"""
        return self.node_to_grid.get(node_index)

    def get_node_from_coordinates(self, row, col):
        """Convert grid coordinates to node index"""
        return self.grid_to_node.get((row, col))

    def get_node_position(self, node_index):
        """Get the world position of a node"""
        # Calculate position based on grid coordinates
        row, col = self.get_node_coordinates(node_index)
        tam_tablero = self.dim * 2
        tam_celda = tam_tablero / self.grid_size
        x_centro = -tam_tablero / 2 + (col + 0.5) * tam_celda
        z_centro = -tam_tablero / 2 + (row + 0.5) * tam_celda
        return numpy.array([x_centro, 0, z_centro])

    def RetrieveNextNodeVertical(self, NodoActual):
        """Follow the predefined vertical path, teleporting back to the start after the last node."""
        self.path_index_vertical += 1
        if self.path_index_vertical >= len(self.vertical_path_nodes):
            # Teleport back to the starting node
            self.Position = self.get_node_position(self.vertical_path_nodes[0]).copy()
            self.currentNode = self.vertical_path_nodes[0]
            self.path_index_vertical = 1  # Set to the next node
            return self.vertical_path_nodes[self.path_index_vertical]
        else:
            return self.vertical_path_nodes[self.path_index_vertical]

    def RetrieveNextNodeHorizontal(self, NodoActual):
        """Follow the predefined horizontal path, teleporting back to the start after the last node."""
        self.path_index_horizontal += 1
        if self.path_index_horizontal >= len(self.horizontal_path_nodes):
            # Teleport back to the starting node
            self.Position = self.get_node_position(self.horizontal_path_nodes[0]).copy()
            self.currentNode = self.horizontal_path_nodes[0]
            self.path_index_horizontal = 1  # Set to the next node
            return self.horizontal_path_nodes[self.path_index_horizontal]
        else:
            return self.horizontal_path_nodes[self.path_index_horizontal]

    def ComputeDirection(self, Posicion, NodoSiguiente):
        """Compute direction and distance to the next node"""
        node_position = self.get_node_position(NodoSiguiente)
        Direccion = node_position - Posicion
        Distancia = numpy.linalg.norm(Direccion)
        if Distancia != 0:
            Direccion /= Distancia
        else:
            Direccion = numpy.zeros(3)
        return Direccion, Distancia

    def update(self, delta):
        """Update the agent's position and state"""
        # Compute direction and distance to the current target node
        Direccion, Distancia = self.ComputeDirection(self.Position, self.nextNode)

        # Check if the agent has reached the target node
        if Distancia < 1:
            self.currentNode = self.nextNode
            if self.searchStyle == 0:
                self.nextNode = self.RetrieveNextNodeVertical(
                    self.currentNode
                )  # Follow vertical path
            elif self.searchStyle == 1:
                self.nextNode = self.RetrieveNextNodeHorizontal(
                    self.currentNode
                )  # Follow horizontal path

        # Compute direction again after potential teleportation
        Direccion, Distancia = self.ComputeDirection(self.Position, self.nextNode)

        # Update position
        self.Position += Direccion * self.vel * delta
        self.Direction = Direccion

        # Update angle based on direction
        if self.Direction[0] != 0:
            self.angle = math.acos(self.Direction[0]) * 180 / math.pi
            if self.Direction[2] > 0:
                self.angle = 360 - self.angle
        else:
            self.angle = 0

    def draw(self):
        glPushMatrix()
        glTranslatef(self.Position[0], self.Position[1], self.Position[2])
        glRotatef(self.angle, 0, 1, 0)
        glScaled(5, 5, 5)
        glColor3f(1.0, 1.0, 1.0)
        # front face
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.textures[2])
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3d(1, 1, 1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(1, 1, -1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(1, -1, -1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(1, -1, 1)

        # 2nd face
        glTexCoord2f(0.0, 0.0)
        glVertex3d(-2, 1, 1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(1, 1, 1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(1, -1, 1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(-2, -1, 1)

        # 3rd face
        glTexCoord2f(0.0, 0.0)
        glVertex3d(-2, 1, -1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(-2, 1, 1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(-2, -1, 1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(-2, -1, -1)

        # 4th face
        glTexCoord2f(0.0, 0.0)
        glVertex3d(1, 1, -1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(-2, 1, -1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(-2, -1, -1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(1, -1, -1)

        # top
        glTexCoord2f(0.0, 0.0)
        glVertex3d(1, 1, 1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(-2, 1, 1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(-2, 1, -1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(1, 1, -1)
        glEnd()

        # Head

        glPushMatrix()
        glTranslatef(0, 1.5, 0)
        glScaled(0.8, 0.8, 0.8)
        glColor3f(1.0, 1.0, 1.0)
        head = Cubo(self.textures, 0)
        head.draw()
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

        # Wheels
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.textures[1])
        glPushMatrix()
        glTranslatef(-1.2, -1, 1)
        glScaled(0.3, 0.3, 0.3)
        glColor3f(1.0, 1.0, 1.0)
        wheel = Cubo(self.textures, 0)
        wheel.draw()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.5, -1, 1)
        glScaled(0.3, 0.3, 0.3)
        wheel = Cubo(self.textures, 0)
        wheel.draw()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.5, -1, -1)
        glScaled(0.3, 0.3, 0.3)
        wheel = Cubo(self.textures, 0)
        wheel.draw()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(-1.2, -1, -1)
        glScaled(0.3, 0.3, 0.3)
        wheel = Cubo(self.textures, 0)
        wheel.draw()
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

        # Car
        glPushMatrix()
        glColor3f(0.0, 0.0, 0.0)
        glTranslatef(0, self.platformHeight, 0)  # Up and down
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3d(1, 1, 1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(1, 1, -1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(3, 1, -1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(3, 1, 1)
        glEnd()
        glPopMatrix()
        glPopMatrix()

    def drawTrash(self):
        glPushMatrix()
        glTranslatef(2, (self.platformHeight + 1.5), 0)
        glScaled(0.5, 0.5, 0.5)
        glColor3f(1.0, 1.0, 1.0)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.textures[3])

        glBegin(GL_QUADS)

        # Front face
        glTexCoord2f(0.0, 0.0)
        glVertex3d(1, 1, 1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(-1, 1, 1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(-1, -1, 1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(1, -1, 1)

        # Back face
        glTexCoord2f(0.0, 0.0)
        glVertex3d(-1, 1, -1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(1, 1, -1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(1, -1, -1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(-1, -1, -1)

        # Left face
        glTexCoord2f(0.0, 0.0)
        glVertex3d(-1, 1, 1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(-1, 1, -1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(-1, -1, -1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(-1, -1, 1)

        # Right face
        glTexCoord2f(0.0, 0.0)
        glVertex3d(1, 1, -1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(1, 1, 1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(1, -1, 1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(1, -1, -1)

        # Top face
        glTexCoord2f(0.0, 0.0)
        glVertex3d(-1, 1, 1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(1, 1, 1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(1, 1, -1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(-1, 1, -1)

        # Bottom face
        glTexCoord2f(0.0, 0.0)
        glVertex3d(-1, -1, 1)
        glTexCoord2f(1.0, 0.0)
        glVertex3d(1, -1, 1)
        glTexCoord2f(1.0, 1.0)
        glVertex3d(1, -1, -1)
        glTexCoord2f(0.0, 1.0)
        glVertex3d(-1, -1, -1)

        glEnd()
        glDisable(GL_TEXTURE_2D)

        glPopMatrix()
