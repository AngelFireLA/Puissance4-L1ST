from custom_neural_network.node import Node

class Layer:
    def __init__(self, num_nodes, no_multiply=False):
        if no_multiply:
            self.nodes = [Node(0) for _ in range(num_nodes)]
        else:
            self.nodes = [Node() for _ in range(num_nodes)]

    def add_node(self):
        self.nodes.append(Node())

    def copy(self, original_next_layer=None, new_next_layer=None):
        # Create a new layer and a mapping from old nodes to new nodes.
        new_layer = Layer(0)  # Start with an empty layer.
        mapping = {}
        for node in self.nodes:
            new_node = node.copy()
            new_layer.nodes.append(new_node)
            mapping[node] = new_node

        if original_next_layer and new_next_layer:
            for node in self.nodes:
                new_node = mapping[node]
                for connection in node.connections:
                    original_target = connection[0]
                    weight = connection[1]
                    # Use the mapping from original_next_layer to new_next_layer.
                    try:
                        index = original_next_layer.nodes.index(original_target)
                    except ValueError:
                        # Handle the case where the node is not found.
                        print("Warning: Node not found in original_next_layer; skipping connection.")
                        continue
                    new_target = new_next_layer.nodes[index]
                    new_node.connections.append([new_target, weight])
        return new_layer

