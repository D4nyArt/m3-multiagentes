import time

class TrafficLight:
    def __init__(self, greenA, greenB):
        self.greenA = greenA
        self.greenB = greenB
        self.last_toggle = time.time()

    def update(self):
        current_time = time.time()
        if current_time - self.last_toggle >= 10:
            self.greenA = not self.greenA
            self.greenB = not self.greenB
            self.last_toggle = current_time

    def showState(self):
        print(f"greenA: {self.greenA}, greenB: {self.greenB}")