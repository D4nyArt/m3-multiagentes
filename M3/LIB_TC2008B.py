import pygame, random, glob, math, numpy
from CarImplementation import Car
from Settings import Settings
from Node import Node

from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

textures = []
cars = []
delta = 0
nodes = []

settings = Settings("Settings.yaml")

tam_tablero = settings.DimBoard * 2  # Cambia esto según el tamaño real de tu tablero
num_celdas = 8
tam_celda = tam_tablero / num_celdas  # Tamaño de cada celda en el tablero


def GeneracionDeNodos(nodes):
    node_positions = {}  # Map from (i, j) to node index
    index = 0

    intersection_positions = {
        (3, 2): [(2, 3), (3, 5), (5, 4)],
        (5, 3): [(4, 2), (2, 3), (3, 5)],
        (2, 4): [(3, 5), (5, 4), (4, 2)],
        (4, 5): [(5, 4), (4, 2), (2, 3)],
    }

    # Generate nodes in the cross pattern and store their grid positions
    for i in range(num_celdas):
        for j in range(num_celdas):
            if i in range(3, 5) or j in range(3, 5):
                x_centro = -tam_tablero / 2 + (i + 0.5) * tam_celda
                z_centro = -tam_tablero / 2 + (j + 0.5) * tam_celda
                node = Node(x_centro, z_centro)
                node.setGridPosition(i, j)
                nodes.append(node)
                node_positions[(i, j)] = index
                index += 1

    # Assign 'nextNodes' for each node according to street logic
    for idx, node in enumerate(nodes):
        i, j = node.getGridPosition()

        # For all nodes, including intersections, add possible next nodes in both directions
        # Vertical movement (nodes in columns 3 and 4)
        if i in range(3, 5):
            # Move upwards (decrease j)
            if j > 0:
                next_i = i
                next_j = j - 1
                if (next_i, next_j) in node_positions:
                    next_node_idx = node_positions[(next_i, next_j)]
                    node.addNextNode(nodes[next_node_idx])
            # Move downwards (increase j)
            if j < num_celdas - 1:
                next_i = i
                next_j = j + 1
                if (next_i, next_j) in node_positions:
                    next_node_idx = node_positions[(next_i, next_j)]
                    node.addNextNode(nodes[next_node_idx])

        # Horizontal movement (nodes in rows 3 and 4)
        if j in range(3, 5):
            # Move left (decrease i)
            if i > 0:
                next_i = i - 1
                next_j = j
                if (next_i, next_j) in node_positions:
                    next_node_idx = node_positions[(next_i, next_j)]
                    node.addNextNode(nodes[next_node_idx])
            # Move right (increase i)
            if i < num_celdas - 1:
                next_i = i + 1
                next_j = j
                if (next_i, next_j) in node_positions:
                    next_node_idx = node_positions[(next_i, next_j)]
                    node.addNextNode(nodes[next_node_idx])

        # Intersection nodes: add additional paths if needed
        if (i, j) in intersection_positions:
            # For intersection nodes, add the specified next nodes
            for next_i, next_j in intersection_positions[(i, j)]:
                if (next_i, next_j) in node_positions:
                    next_node_idx = node_positions[(next_i, next_j)]
                    node.addNextNode(nodes[next_node_idx])

    for node in nodes:
        print(f"Node at {node.getGridPosition()} has next nodes:")
        for next_node in node.nextNodes:
            print(f"  -> {next_node.getGridPosition()}")


def Texturas(filepath):
    # Arreglo para el manejo de texturas
    global textures
    textures.append(glGenTextures(1))
    id = len(textures) - 1
    glBindTexture(GL_TEXTURE_2D, textures[id])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    image = pygame.image.load(filepath).convert()
    w, h = image.get_rect().size
    image_data = pygame.image.tostring(image, "RGBA")
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data
    )
    glGenerateMipmap(GL_TEXTURE_2D)


def Init(Options):
    global textures, basuras, cars
    screen = pygame.display.set_mode(
        (settings.screen_width, settings.screen_height), DOUBLEBUF | OPENGL
    )
    pygame.display.set_caption("M3")

    GeneracionDeNodos(nodes)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(
        settings.FOVY,
        settings.screen_width / settings.screen_height,
        settings.ZNEAR,
        settings.ZFAR,
    )

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(
        settings.EYE_X,
        settings.EYE_Y,
        settings.EYE_Z,
        settings.CENTER_X,
        settings.CENTER_Y,
        settings.CENTER_Z,
        settings.UP_X,
        settings.UP_Y,
        settings.UP_Z,
    )
    glClearColor(0, 0, 0, 0)
    glEnable(GL_DEPTH_TEST)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    for File in glob.glob(settings.Materials + "*.*"):
        Texturas(File)

    # Posiciones inicales de los montacargas
    colsDim = 3
    rowLifts = Options.cars
    Positions = numpy.zeros((rowLifts, colsDim))

    currentNodeIndex = 0
    CurrentNode = nodes[currentNodeIndex]

    for i, p in enumerate(Positions):
        if i == 0:
            cars.append(Car(settings.DimBoard, 2, textures, i, p, CurrentNode))
        else:
            random_node_index = random.randint(0, len(nodes) - 1)
            random_node = nodes[random_node_index]
            cars.append(Car(settings.DimBoard, 2, textures, i, p, random_node))


def planoText():
    # Tamaño del tablero y de cada celda
    tam_tablero = settings.DimBoard * 2  # Dimensión completa del tablero
    tam_celda = tam_tablero / 8  # Tamaño de cada celda en el tablero

    # Iniciar dibujo de los cuadrados
    glBegin(GL_QUADS)

    # Recorrer filas y columnas de la intersección
    for i in range(8):
        for j in range(8):
            # Pintar solo celdas en los caminos centrales de la intersección tipo cruz
            if i in range(3, 5) or j in range(3, 5):
                # Alternar colores para el efecto de tablero de ajedrez
                if (i + j) % 2 == 0:
                    glColor3f(1.0, 1.0, 1.0)  # Color blanco
                else:
                    glColor3f(0.0, 0.0, 0.0)  # Color negro

                # Calcular las coordenadas de la celda
                x_inicio = -settings.DimBoard + i * tam_celda
                z_inicio = -settings.DimBoard + j * tam_celda
                x_fin = x_inicio + tam_celda
                z_fin = z_inicio + tam_celda

                # Dibujar la celda como un cuadrado
                glTexCoord2f(0.0, 1.0)
                glVertex3f(x_inicio, 0, z_inicio)
                glTexCoord2f(1.0, 1.0)
                glVertex3f(x_fin, 0, z_inicio)
                glTexCoord2f(1.0, 0.0)
                glVertex3f(x_fin, 0, z_fin)
                glTexCoord2f(0.0, 0.0)
                glVertex3f(x_inicio, 0, z_fin)

    glEnd()


def display():
    global cars, delta
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Se dibuja cars
    for obj in cars:
        obj.draw()
        obj.update(delta)

    # Se dibuja el plano gris
    planoText()
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex3d(-settings.DimBoard, 0, -settings.DimBoard)
    glVertex3d(-settings.DimBoard, 0, -settings.DimBoard)
    glVertex3d(settings.DimBoard, 0, -settings.DimBoard)
    glVertex3d(settings.DimBoard, 0, -settings.DimBoard)
    glEnd()

    # Draw the walls bounding the plane
    wall_height = 30.0  # Adjust the wall height as needed

    glColor3f(0.7, 0.5, 1.0)  # Lila claro

    # Draw the left(S) wall(S)
    glBegin(GL_QUADS)
    glVertex3d(-settings.DimBoard / 8 * 2, 0, (-settings.DimBoard) + 50)
    glVertex3d(-settings.DimBoard / 8 * 2, 0, -settings.DimBoard / 8 * 2)
    glVertex3d(-settings.DimBoard / 8 * 2, wall_height, -settings.DimBoard / 8 * 2)
    glVertex3d(-settings.DimBoard / 8 * 2, wall_height, (-settings.DimBoard) + 50)
    glEnd()

    glBegin(GL_QUADS)
    glVertex3d(-settings.DimBoard / 8 * 2, 0, (settings.DimBoard) - 50)
    glVertex3d(-settings.DimBoard / 8 * 2, 0, settings.DimBoard / 8 * 2)
    glVertex3d(-settings.DimBoard / 8 * 2, wall_height, settings.DimBoard / 8 * 2)
    glVertex3d(-settings.DimBoard / 8 * 2, wall_height, (settings.DimBoard) - 50)
    glEnd()

    # Draw the right walls
    glBegin(GL_QUADS)
    glVertex3d(settings.DimBoard / 8 * 2, 0, (-settings.DimBoard) + 50)
    glVertex3d(settings.DimBoard / 8 * 2, 0, -settings.DimBoard / 8 * 2)
    glVertex3d(settings.DimBoard / 8 * 2, wall_height, -settings.DimBoard / 8 * 2)
    glVertex3d(settings.DimBoard / 8 * 2, wall_height, (-settings.DimBoard) + 50)
    glEnd()

    glBegin(GL_QUADS)
    glVertex3d(settings.DimBoard / 8 * 2, 0, (settings.DimBoard) - 50)
    glVertex3d(settings.DimBoard / 8 * 2, 0, settings.DimBoard / 8 * 2)
    glVertex3d(settings.DimBoard / 8 * 2, wall_height, settings.DimBoard / 8 * 2)
    glVertex3d(settings.DimBoard / 8 * 2, wall_height, (settings.DimBoard) - 50)
    glEnd()

    # Draw the back walls
    glBegin(GL_QUADS)
    glVertex3d((-settings.DimBoard) + 50, 0, settings.DimBoard / 8 * 2)
    glVertex3d(-settings.DimBoard / 8 * 2, 0, settings.DimBoard / 8 * 2)
    glVertex3d(-settings.DimBoard / 8 * 2, wall_height, settings.DimBoard / 8 * 2)
    glVertex3d((-settings.DimBoard) + 50, wall_height, settings.DimBoard / 8 * 2)
    glEnd()

    glBegin(GL_QUADS)
    glVertex3d((settings.DimBoard) - 50, 0, settings.DimBoard / 8 * 2)
    glVertex3d(settings.DimBoard / 8 * 2, 0, settings.DimBoard / 8 * 2)
    glVertex3d(settings.DimBoard / 8 * 2, wall_height, settings.DimBoard / 8 * 2)
    glVertex3d((settings.DimBoard) - 50, wall_height, settings.DimBoard / 8 * 2)
    glEnd()

    # Draw the front walls
    glBegin(GL_QUADS)
    glVertex3d(-settings.DimBoard / 8 * 2, 0, -settings.DimBoard / 8 * 2)
    glVertex3d((-settings.DimBoard) + 50, 0, -settings.DimBoard / 8 * 2)
    glVertex3d((-settings.DimBoard) + 50, wall_height, -settings.DimBoard / 8 * 2)
    glVertex3d(-settings.DimBoard / 8 * 2, wall_height, -settings.DimBoard / 8 * 2)
    glEnd()

    glBegin(GL_QUADS)
    glVertex3d(settings.DimBoard / 8 * 2, 0, -settings.DimBoard / 8 * 2)
    glVertex3d((settings.DimBoard) - 50, 0, -settings.DimBoard / 8 * 2)
    glVertex3d((settings.DimBoard) - 50, wall_height, -settings.DimBoard / 8 * 2)
    glVertex3d(settings.DimBoard / 8 * 2, wall_height, -settings.DimBoard / 8 * 2)
    glEnd()


def lookAt(theta):
    glLoadIdentity()
    rad = theta * math.pi / 180
    newX = settings.EYE_X * math.cos(rad) + settings.EYE_Z * math.sin(rad)
    newZ = -settings.EYE_X * math.sin(rad) + settings.EYE_Z * math.cos(rad)
    gluLookAt(
        newX,
        settings.EYE_Y,
        newZ,
        settings.CENTER_X,
        settings.CENTER_Y,
        settings.CENTER_Z,
        settings.UP_X,
        settings.UP_Y,
        settings.UP_Z,
    )


def Simulacion(Options):
    # Variables para el control del observador
    global delta
    theta = Options.theta
    radius = Options.radious
    delta = Options.Delta
    Init(Options)
    while True:
        keys = pygame.key.get_pressed()  # Checking pressed keys
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.type == pygame.QUIT:
                    pygame.quit()
                    return
        if keys[pygame.K_RIGHT]:
            if theta > 359.0:
                theta = 0
            else:
                theta += 1.0
        lookAt(theta)
        if keys[pygame.K_LEFT]:
            if theta < 1.0:
                theta = 360.0
            else:
                theta -= 1.0
        lookAt(theta)
        display()
        display()
        pygame.display.flip()
        pygame.time.wait(10)

    #
