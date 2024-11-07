class Node:
    def __init__(self):
        self.nextNode = []
        self.isIntersection = False
        self.receivesIntersection = False

    def setNextNode(self, nextNode):
        self.nextNode = nextNode

    def getNextNode(self):
        return self.nextNode

    def setIsIntersection(self, isIntersection: bool):
        self.isIntersection = isIntersection

    def getIsIntersection(self):
        return self.isIntersection

    def setReceivesIntersection(self, receivesIntersection: bool):
        self.receivesIntersection = receivesIntersection

    def getReceivesIntersection(self):
        return self.receivesIntersection
