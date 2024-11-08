import pygame, random, glob, math, numpy
from CarImplementation import Car
from Settings import Settings
from Node import Node

from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from Trafficlight import TrafficLight

textures = []
cars = []
delta = 0
nodes = []

settings = Settings("Settings.yaml")

tam_tablero = settings.DimBoard * 2  # Cambia esto según el tamaño real de tu tablero
num_celdas = 8
tam_celda = tam_tablero / num_celdas  # Tamaño de cada celda en el tablero


def GeneracionDeNodos():
    nodes = []
    node_positions = {}  # Map from (i, j) to node index in nodes list
    index = 0
    num_celdas = 8  # Grid size
    tam_tablero = settings.DimBoard * 2
    tam_celda = tam_tablero / num_celdas

    # Generate all nodes and store them in the nodes list
    for i in range(num_celdas):
        for j in range(num_celdas):
            x_centro = -tam_tablero / 2 + (j + 0.5) * tam_celda
            z_centro = -tam_tablero / 2 + (i + 0.5) * tam_celda
            node = Node(x_centro, z_centro)
            node.setGridPosition(i, j)
            nodes.append(node)
            node_positions[(i, j)] = index
            index += 1

    # Define the intersection nodes (only these nodes can have multiple nextNodes)
    intersection_nodes = [19, 29, 34, 44]

    for idx in intersection_nodes:
        if 0 <= idx < len(nodes):
            nodes[idx].setIsIntersection(True)

    # Define the node mappings as per your specified mapping
    node_mappings = {
        60: [52],
        52: [44],
        44: [37, 20, 26],  # Intersection node (44)
        37: [38],
        38: [39],
        31: [30],
        30: [29],
        29: [20, 26, 43],  # Intersection node (29)
        20: [12],
        12: [4],
        3: [11],
        11: [19],
        19: [26, 43, 37],  # Intersection node (19)
        26: [25],
        25: [24],
        32: [33],
        33: [34],
        34: [43, 37, 20],  # Intersection node (34)
        43: [51],
        51: [59],
        # Include other nodes if necessary
    }

    # Assign nextNodes to nodes
    for node_index, next_node_indices in node_mappings.items():
        current_node = nodes[node_index]
        if len(next_node_indices) > 1:
            # Ensure only intersection nodes have multiple nextNodes
            if node_index not in intersection_nodes:
                print(
                    f"Warning: Node {node_index} is not an intersection node but has multiple nextNodes."
                )
        else:
            # Non-intersection nodes should have only one nextNode
            if node_index in intersection_nodes:
                print(f"Note: Intersection Node {node_index} has only one nextNode.")
        # Assign the nextNodes
        for next_node_index in next_node_indices:
            next_node = nodes[next_node_index]
            current_node.addNextNode(next_node)

    # Optional: Verify that no non-intersection node has multiple nextNodes
    for i, node in enumerate(nodes):
        if len(node.nextNodes) > 1 and i not in intersection_nodes:
            print(
                f"Error: Node {i} has multiple nextNodes but is not an intersection node."
            )

    return nodes, node_mappings


def print_node_mappings(nodes):
    for i, node in enumerate(nodes):
        if node.nextNodes:
            next_node_indices = [nodes.index(n) for n in node.nextNodes]
            print(f"Node {i} -> Next Nodes: {next_node_indices}")


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
    global textures, trafficlight, cars
    screen = pygame.display.set_mode(
        (settings.screen_width, settings.screen_height), DOUBLEBUF | OPENGL
    )
    pygame.display.set_caption("M3")

    nodes, node_mappings = GeneracionDeNodos()
    starting_node_indices_A = [31, 32]
    starting_node_indices_B = [3, 60]

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

    trafficlight = TrafficLight(True, False)

    lane_A_cars = int(Options.cars * 0.6)  # 50% more than lane B
    lane_B_cars = Options.cars - lane_A_cars

    for i in range(lane_A_cars):
        # Assign starting nodes to cars in a round-robin fashion
        currentNodeIndex = starting_node_indices_A[i % len(starting_node_indices_A)]
        currentNode = nodes[currentNodeIndex]
        cars.append(Car(settings.DimBoard, 2, textures, i, currentNode, currentNode, 'A', trafficlight))

    for i in range(lane_B_cars):
        # Assign starting nodes to cars in a round-robin fashion
        currentNodeIndex = starting_node_indices_B[i % len(starting_node_indices_A)]
        currentNode = nodes[currentNodeIndex]
        cars.append(Car(settings.DimBoard, 2, textures, i, currentNode, currentNode, 'B', trafficlight))


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
    global cars, delta, trafficlight
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    trafficlight.update()

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
