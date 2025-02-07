import random

class Node:
    def __init__(self, bias=None):
        self.bias = bias if bias is not None else random.uniform(-1, 1)
        self.connections = []

    def connect_to(self, node, multiplier=None):
        #check if the node isn't already connected
        for connection in self.connections:
            if connection[0] == node:
                return
        if multiplier is None:
            multiplier = random.random() * random.choice([-1, 1])
        self.connections.append([node, multiplier])

    def copy(self):
        return Node(self.bias)

