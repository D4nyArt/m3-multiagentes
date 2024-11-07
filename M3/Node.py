class Node:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.grid_postition = None
        self.nextNodes = []

    def setCoodinates(self, x, z):
        self.x = x
        self.z = z

    def setGridPosition(self, x, z):
        self.grid_postition = (x, z)

    def getGridPosition(self):
        return self.grid_postition

    def getCoordinates(self):
        return self.x, self.z

    def addNextNode(self, nextNode):
        self.nextNodes.append(nextNode)

    def getNextNode(self):
        return self.nextNodes

    def setIsIntersection(self, isIntersection: bool):
        self.isIntersection = isIntersection

    def getIsIntersection(self):
        return self.isIntersection

    def setReceivesIntersection(self, receivesIntersection: bool):
        self.receivesIntersection = receivesIntersection

    def getReceivesIntersection(self):
        return self.receivesIntersection
