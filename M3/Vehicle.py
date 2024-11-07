import pygame, random, math, numpy, yaml
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


class Vehicle:
    def __init__(self, road, position, direction, turning_left=False):
        self.road = road  # 'A' or 'B'
        self.position = position  # [x, y, z]
        self.direction = direction  # [dx, dy, dz]
        self.turning_left = turning_left
        self.waiting = False
        self.speed = 2.0
        self.size = 4.0  # Size of vehicle for visualization

    def update(self, delta, traffic_light):
        if not self.waiting:
            # Check if vehicle needs to stop at red light
            if self.road == 'B' and not traffic_light.is_green():
                distance_to_intersection = math.sqrt(
                    self.position[0]**2 + self.position[2]**2
                )
                if distance_to_intersection < 10:  # Stop before intersection
                    self.waiting = True
                    return

            # Update position
            self.position[0] += self.direction[0] * self.speed * delta
            self.position[2] += self.direction[2] * self.speed * delta

            # Handle turning left if needed
            if self.turning_left:
                # Implement turning logic when reaching intersection
                pass

    def draw(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        
        # Rotate based on direction
        angle = math.degrees(math.atan2(self.direction[2], self.direction[0]))
        glRotatef(angle, 0, 1, 0)
        
        # Draw vehicle as a colored cuboid
        if self.road == 'A':
            glColor3f(1.0, 0.0, 0.0)  # Red for road A
        else:
            glColor3f(0.0, 0.0, 1.0)  # Blue for road B
            
        glScalef(self.size, self.size/2, self.size/2)
        glutSolidCube(1.0)
        glPopMatrix()

class TrafficLight:
    def __init__(self, t_seconds=30, n_vehicles=5):
        self.green_for_B = False
        self.timer = 0
        self.t_seconds = t_seconds
        self.n_vehicles = n_vehicles
        self.vehicles_crossed_A = 0
        
    def update(self, delta):
        self.timer += delta
        if self.green_for_B:
            if self.timer >= self.t_seconds:
                self.green_for_B = False
                self.timer = 0
                self.vehicles_crossed_A = 0
        else:
            if (self.vehicles_crossed_A >= self.n_vehicles or 
                self.timer >= self.t_seconds * 1.5):  # 50% more time for road A
                self.green_for_B = True
                self.timer = 0
                
    def is_green(self):
        return self.green_for_B
        
    def draw(self):
        # Draw traffic light poles and signals
        glPushMatrix()
        glColor3f(0.5, 0.5, 0.5)  # Gray for pole
        
        # Draw poles at intersection corners
        for x, z in [(10, 10), (-10, 10), (10, -10), (-10, -10)]:
            glPushMatrix()
            glTranslatef(x, 0, z)
            glScalef(0.5, 10, 0.5)
            glutSolidCube(1.0)
            
            # Draw signal lights
            glPushMatrix()
            glTranslatef(0, 1, 0)
            if self.green_for_B:
                glColor3f(0.0, 1.0, 0.0)  # Green
            else:
                glColor3f(1.0, 0.0, 0.0)  # Red
            glutSolidSphere(0.5, 10, 10)
            glPopMatrix()
            
            glPopMatrix()
        
        glPopMatrix()

class IntersectionSimulation:
    def __init__(self, board_size=100):
        self.board_size = board_size
        self.vehicles = []
        self.traffic_light = TrafficLight()
        self.spawn_timer = 0
        self.spawn_rate_A = 1.0  # Vehicles per second for road A
        self.spawn_rate_B = 0.67  # 50% less traffic than road A
        
    def spawn_vehicle(self, road):
        # Randomly decide if vehicle will turn left (20% chance)
        turning_left = random.random() < 0.2
        
        if road == 'A':
            # Spawn on road A (East-West)
            x = -self.board_size if random.random() < 0.5 else self.board_size
            z = 0
            direction = [-1 if x > 0 else 1, 0, 0]
        else:
            # Spawn on road B (North-South)
            x = 0
            z = -self.board_size if random.random() < 0.5 else self.board_size
            direction = [0, 0, -1 if z > 0 else 1]
            
        vehicle = Vehicle(road, [x, 0, z], direction, turning_left)
        self.vehicles.append(vehicle)
        
    def update(self, delta):
        # Update traffic light
        self.traffic_light.update(delta)
        
        # Update spawn timer and spawn new vehicles
        self.spawn_timer += delta
        if self.spawn_timer >= 1.0:  # Check every second
            if random.random() < self.spawn_rate_A:
                self.spawn_vehicle('A')
            if random.random() < self.spawn_rate_B:
                self.spawn_vehicle('B')
            self.spawn_timer = 0
            
        # Update vehicles
        for vehicle in self.vehicles[:]:
            vehicle.update(delta, self.traffic_light)
            
            # Remove vehicles that have left the board
            if (abs(vehicle.position[0]) > self.board_size + 10 or 
                abs(vehicle.position[2]) > self.board_size + 10):
                if vehicle.road == 'A':
                    self.traffic_light.vehicles_crossed_A += 1
                self.vehicles.remove(vehicle)
                
    def draw(self):
        # Draw roads
        glColor3f(0.3, 0.3, 0.3)  # Gray for roads
        
        # Draw East-West road (A)
        glBegin(GL_QUADS)
        glVertex3f(-self.board_size, 0, -10)
        glVertex3f(self.board_size, 0, -10)
        glVertex3f(self.board_size, 0, 10)
        glVertex3f(-self.board_size, 0, 10)
        glEnd()
        
        # Draw North-South road (B)
        glBegin(GL_QUADS)
        glVertex3f(-10, 0, -self.board_size)
        glVertex3f(10, 0, -self.board_size)
        glVertex3f(10, 0, self.board_size)
        glVertex3f(-10, 0, self.board_size)
        glEnd()
        
        # Draw traffic light
        self.traffic_light.draw()
        
        # Draw vehicles
        for vehicle in self.vehicles:
            vehicle.draw()
