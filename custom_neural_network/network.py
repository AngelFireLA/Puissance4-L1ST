import math
import random
import time
import cProfile
from custom_neural_network.layer import Layer
import moteur.plateau as plateau
import moteur.partie as partie
import moteur.joueur as joueur

class Network:
    def __init__(self, inputs, outputs, num_hidden_layers, nodes_per_hidden_layer, randomly_connect_nodes=True):
        self.inputs = inputs
        self.outputs = outputs
        self.hidden_layers = [Layer(nodes_per_hidden_layer) for _ in range(num_hidden_layers)]
        self.set_layers()
        if randomly_connect_nodes:
            self.randomly_connect_nodes()
        self.mutate_factor = 0.15
        self.new_layer_factor = 0.01
        self.new_node_factor = 0.05
        self.new_connection_factor = 0.05
        self.remove_connection_factor = 0.05
        self.remove_node_factor = 0.05
        self.age = 0
        self.results = []

    def set_layers(self):
        if self.inputs > 0:
            input_layers = [Layer(self.inputs, no_multiply=True)]
        else:
            input_layers = []
        if self.outputs > 0:
            output_layers = [Layer(self.outputs, no_multiply=True)]
        else:
            output_layers = []
        self.layers = input_layers + self.hidden_layers + output_layers

    def show(self):
        for i, layer in enumerate(self.layers):
            print(f"Layer {i}:")
            print(f"Nodes: {len(layer.nodes)}")
            for j, node in enumerate(layer.nodes):
                print(f"Node {j}: {node.bias}")
                print(f"Nexts: {len(node.connections)}")
                print(f"Nexts multipliers: {[connection[1] for connection in node.connections]}")
            print()

    def randomly_connect_nodes(self):
        for i in range(len(self.layers) - 1):
            for node1 in self.layers[i].nodes:
                amount_of_connections = random.randint(1, len(self.layers[i + 1].nodes)) if len(self.layers[i + 1].nodes) > 1 else 1
                for _ in range(amount_of_connections):
                    node2 = random.choice(self.layers[i + 1].nodes)
                    node1.connect_to(node2)

    def deepcopy(self):
        new_network = Network(0, 0, 0, 0, False)
        new_network.inputs = self.inputs
        new_network.outputs = self.outputs

        node_mappings = []
        for layer in self.layers:
            new_layer = Layer(0)
            mapping = {}
            for node in layer.nodes:
                new_node = node.copy()
                new_layer.nodes.append(new_node)
                mapping[node] = new_node
            node_mappings.append(mapping)
            new_network.layers.append(new_layer)

        for i in range(len(self.layers) - 1):
            for old_node in self.layers[i].nodes:
                new_node = node_mappings[i][old_node]
                for connection in old_node.connections:
                    old_target = connection[0]
                    weight = connection[1]
                    if old_target in node_mappings[i + 1]:
                        new_target = node_mappings[i + 1][old_target]
                        new_node.connections.append([new_target, weight])
                    else:
                        print("Warning: Node in connection not found in next layer's mapping; skipping.")
        return new_network

    def randomly_mutate_network(self, iterations, total_iterations):
        mutation_amount = sigmoid(total_iterations-iterations)+0.1
        for i in range(len(self.layers) - 1):
            layer = self.layers[i]
            for node in layer.nodes:
                if random.random() < self.mutate_factor:
                    node.bias += random.uniform(-mutation_amount, mutation_amount)
                for connection in node.connections:
                    if random.random() < self.mutate_factor:
                        connection[1] += random.uniform(-mutation_amount, mutation_amount)
                if random.random() < self.new_connection_factor:
                    if i < len(self.layers) - 2 and random.random() > self.new_node_factor:
                        self.layers[i+1].add_node()
                        self.layers[i+1].nodes[-1].connect_to(random.choice(self.layers[i+2].nodes))
                        node.connect_to(self.layers[i+1].nodes[-1])
                    else:
                        node.connect_to(random.choice(self.layers[i+1].nodes))
                if len(node.connections) > 1 and random.random() < self.remove_connection_factor:
                    node.connections.remove(random.choice(node.connections))
                if i > 0 and random.random() < self.remove_node_factor:
                    # remove any connections to this node
                    can_remove_node = True
                    previous_layer = self.layers[i-1]
                    for previous_node in previous_layer.nodes:
                        connections_to_remove = []
                        for connection in previous_node.connections:
                            if connection[0] == node:
                                if len(previous_node.connections) == 1:
                                    can_remove_node = False
                                    break
                                else:
                                    connections_to_remove.append(connection)
                        if not can_remove_node:
                            break
                        for connection in connections_to_remove:
                            previous_node.connections.remove(connection)
                    if can_remove_node: layer.nodes.remove(node)

            if random.random() < self.new_node_factor:
                layer.add_node()
                self.randomly_connect_nodes()

    def process_inputs(self, inputs, softmax=False):
        if len(inputs) != self.inputs:
            raise ValueError(f"Expected {self.inputs} inputs, got {len(inputs)}")

        # Compute activations for the input layer (typically no activation function is applied here).
        activations = {}
        for node in self.layers[0].nodes:
            activations[node] = 0
        for i, input_value in enumerate(inputs):
            activations[self.layers[0].nodes[i]] = input_value

        # Process each subsequent layer.
        for i in range(1, len(self.layers)):
            current_layer = self.layers[i]
            # Start with the bias for each node in the current layer.
            for node in current_layer.nodes:
                activations[node] = node.bias
            # Add contributions from the previous layer.
            previous_layer = self.layers[i - 1]
            for prev_node in previous_layer.nodes:
                # For hidden layers, apply relu to the previous layer's summed value.
                # (You might choose not to activate the input layer.)
                prev_activation = activations[prev_node]
                if i != 1:  # If not the first hidden layer (i.e. input layer), apply relu.
                    prev_activation = relu(prev_activation)
                for connection in prev_node.connections:
                    target_node, weight = connection
                    activations[target_node] += prev_activation * weight

        # For the output layer, you can choose whether to apply an activation.
        output_values = [activations[node] for node in self.layers[-1].nodes]

        if not softmax:
            return max(output_values)
        else:
            # Subtract the maximum value for numerical stability.
            max_val = max(output_values)
            exp_values = [math.exp(val - max_val) for val in output_values]
            sum_exp_values = sum(exp_values)
            softmax_values = [val / sum_exp_values for val in exp_values]
            return max(softmax_values), softmax_values.index(max(softmax_values))

def relu(x):
    return max(0, x)

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def vectorize_board(board: plateau.Plateau):
    vector = []
    for col in range(board.colonnes):
        # Get the list of tokens in the current column.
        column_tokens = board.grille[col]
        # Fill the column with its tokens; empty slots are represented by "."
        full_column = column_tokens + ["." for _ in range(board.lignes - board.hauteurs_colonnes[col])]
        # Convert each cell as needed
        vector.extend([0 if cell == "." else 1 if cell == "X" else -1 for cell in full_column])
    return vector

def evalutate(ntwrk: Network):
    partie_test = partie.Partie()
    partie_en_cours = True
    fit = 0
    joueur1 = joueur.Joueur("Joueur 1", "X")
    joueur2 = joueur.Joueur("Joueur 2", "O")
    partie_test.ajouter_joueur(joueur1)
    partie_test.ajouter_joueur(joueur2)
    i = 0
    while partie_en_cours:
        i += 1
        if partie_test.tour_joueur == 1:
            inputs = vectorize_board(partie_test.plateau)
            output = ntwrk.process_inputs(inputs, softmax=True)[1]
            colonne = output
        else:
            colonne = random.choice(list(partie_test.plateau.colonnes_jouables))
        if partie_test.jouer(colonne, partie_test.tour_joueur) is True:
            if partie_test.plateau.est_nul():
                fit = 0
                break
            if partie_test.plateau.est_victoire(colonne):
                fit = 1 if partie_test.tour_joueur == 1 else -1
                break
            if partie_test.tour_joueur == 1:
                partie_test.tour_joueur = 2
            else:
                partie_test.tour_joueur = 1
        else:
            fit = -1 if partie_test.tour_joueur == 1 else 1
            break
    return fit

profiler = cProfile.Profile()
profiler.enable()
test_inputs = [0]
networks = []
all_networks = []
for i in range(100):
    network = Network(42, 7, 10, random.randint(1, 1))
    fitness = evalutate(network)
    networks.append((network, fitness))
    all_networks.append(network)
    # sort them by how close they are to 50
networks.sort(key=lambda x: x[1])

iterations = 1000
averages = []
for i in range(iterations):
    remaining_networks = networks[:]
    networks = []
    for network, score in remaining_networks:
        # network.randomly_mutate_network(i, iterations)
        fitness = evalutate(network)
        networks.append((network, fitness))
        if network.age > 4: all_networks.append(network)
        if fitness > 0: network.age += 1
        network.results.append(fitness)

    networks.sort(key=lambda x: x[1], reverse=True)
    #average score where score is abs(x[1] - sum(test_inputs) / len(test_inputs))
    average_score = sum([x[1] for x in networks]) / len(networks)
    averages.append(average_score)
    print(i, networks[0][1], networks[0][0].age, average_score)
    networks = networks[:50]
    new_networks = []

    for network, _ in networks:

        start_time = time.time()
        new_network = network.deepcopy()
        new_network.randomly_mutate_network(i, iterations)
        new_networks.append((new_network, 0))
    if i != iterations-1 :
        networks += new_networks
    if i%10 == 0:
        print("average score:", sum(averages) / len(averages))
        averages = []
profiler.disable()

def average_score(network):
    return sum([result for result in network.results]) / len(network.results)

# get the network with the lowest average result score
all_networks.sort(key=lambda x: average_score(x))

#show network average results and network age
print("Best network loss:", average_score(networks[0][0]), networks[0][0].age)
print(networks[0][0].results)
# test the network on different inputs
for i in range(10):
    test_inputs = [random.randint(-100, 100) for _ in range(1)]
    print(test_inputs, sum(test_inputs)**2, networks[0][0].process_inputs(test_inputs))

#old networks are networks older than tenth of the iterations :
old_networks = [network for network in all_networks if network.age > 4]
# get the old network with the lowest average result score

#show network average results and network age
print("best old network results :", average_score(old_networks[0]), old_networks[0].age)
print(old_networks[0].results)

# test the network on different inputs
for i in range(10):
    test_inputs = [random.randint(-100, 100) for _ in range(1)]
    print(test_inputs, sum(test_inputs)**2, old_networks[0].process_inputs(test_inputs))


