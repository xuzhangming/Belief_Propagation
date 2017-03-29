import copy
import itertools
import operator

class belief(object):
    def __init__(self, graph):
        self.graph = graph

    def run(self):
        stop = 1e-10
        graph_converge = 100
        factor_converge = 100
        self.graph.graph_nodes = self.graph.graph_nodes[::-1]
        self.graph.factor_nodes = self.graph.factor_nodes[::-1]
        while graph_converge > stop and factor_converge > stop:
            graph_converge = self.graph.graph_node_messages()
            factor_converge = self.graph.factor_node_messages()
        return graph


class graph(object):
    def __init__(self, model):
        self.bayes_nodes = model.nodes.values()
        self.graph_nodes = []
        self.factor_nodes = []
        self.nodes = {}


    def create_graph(self):
        # Use the bayesian nodes to create the nodes for the
        # sum of product network. In this first step the graph nodes
        # are created and in the next step the factor nodes will be
        # created.
        for node in self.bayes_nodes:
            gnode = graph_node(node)
            self.graph_nodes.append(graph_node(node))
            self.nodes[node.name] = gnode

        # Now creating the factor nodes for the graph.
        for node in self.bayes_nodes:
            connects = [self.nodes[node.name]] + [self.nodes[p.name] for p in node.parents]
            name = tuple([key.name for key in connects])
            fn = factor_node(name, node, connects, self.graph_nodes)
            self.factor_nodes.append(fn)
            self.nodes[fn.name] = fn


    def graph_node_messages(self):
        converge = 0
        for node in self.factor_nodes:
            converge += node.to_receive()
        for node in self.factor_nodes:
            converge += node.to_send()

        return converge


    def factor_node_messages(self):
        converge = 0
        for node in self.graph_nodes:
            converge += node.to_receive()
        for node in self.graph_nodes:
            node.propagate()
            converge += node.to_send()
        return converge


class loopy_node(object):
    def __init__(self):
        pass

    def to_receive(self):
        converge = 0
        for node in self.connects:
            if self.incoming_mes[node.name] is not None:
                changed, value = self.incoming_mes[node.name].has_changed(node.outgoing_mes[self.name])
                if changed and value != -1:
                    self.incoming_mes[node.name] = node.outgoing_mes[self.name]
                    converge += value
            else:
                self.incoming_mes[node.name] = node.outgoing_mes[self.name]
                converge += 1
        return converge

    def to_send(self):
        converge = 0
        for node in self.connects:
            message = self.create_message(node)
            if self.outgoing_mes[node.name] is not None:
                changed, value = self.outgoing_mes[node.name].has_changed(message)
                if changed and value != -1:
                    self.outgoing_mes[node.name] = message
                    converge += value
            else:
                self.outgoing_mes[node.name] = message
                converge += 1

        return converge



class graph_node(loopy_node):
    def __init__(self, node):
        self.name = node.name
        self.connects = []
        self.card = node.card
        self.values = node.values
        self.potential = potential(self, node)
        self.incoming_mes = {}
        self.outgoing_mes = {}

    def propagate(self):
        potent = self.incoming_mes[self.connects[0].name]
        for i in range(1, len(self.connects)):
            potent = potent.prod(self.incoming_mes[self.connects[i].name])

        for node in potent.nodes:
            if node == self:
                pass
            else:
                potents = potent.sum_out(node)
        self.potential = potent
        self.potential.get_prob()

    def create_message(self, node):
        # Get the probabilities of the factor.
        message = None
        for i in range(len(self.connects)):
            if self.connects[i] == node:
                pass
            else:
                if message is None:
                    message = self.incoming_mes[self.connects[i].name]
                else:
                    message_ = self.incoming_mes[self.connects[i].name]
                    if message_ is not None:
                        message = message.prod(message_)
        if message is None:
            message = potential(self, self)
            message.nodes.append(self)
        message.get_prob()
        return message

class factor_node(loopy_node):
    def __init__(self, name, node, connects, graph_nodes):
        self.name = name
        self.connects = []
        self.incoming_mes = {}
        self.outgoing_mes = {}
        for connect in connects:
            idx = self.find_node(connect, graph_nodes)
            graph_nodes[idx].connects.append(self)
            graph_nodes[idx].incoming_mes[self.name] = None
            graph_nodes[idx].outgoing_mes[self.name] = None
            self.connects.append(graph_nodes[idx])
            self.incoming_mes[graph_nodes[idx].name] = None
            self.outgoing_mes[graph_nodes[idx].name] = None
        self.potential = potential(self, node)


    def find_node(self, connect, graph_nodes):
        for i in range(len(graph_nodes)):
            if graph_nodes[i].name == connect.name:
                return i

    def create_message(self, node):
        # Get the probabilities of the factor.
        message = self.potential
        for connect in self.connects:
            if connect == node:
                pass
            else:
                curr_message = self.incoming_mes[connect.name]
                if curr_message is not None:
                    message = message.prod(curr_message)

        for connect in self.connects:
            if connect == node:
                pass
            else:
                message = message.sum_out(connect)
        message.get_prob()
        return message


class potential(object):
    def __init__(self, calling_node=None, node=None, use_nodes=None, potent=None):
        self.table = {}

        if use_nodes is not None:
            self.nodes = use_nodes
            all_values = []
            for node in use_nodes:
                all_values.append(node.values)
            states = []
            for element in itertools.product(*all_values):
                states.append(element)
            for state in states:
                self.table[state] = 0

        if potent is not None:
            self.table = potent

        # Initialize the graph nodes to uniform distribution.
        elif type(calling_node) is graph_node:
            init_value = 1/float(node.card)
            for value in node.values:
                self.table[(value, )] = init_value
            self.nodes = [node]
        elif type(calling_node) is factor_node:
            self.nodes = calling_node.connects
            for row_cnt in range(len(node.cpt_row_states)):
                for val_cnt in range(len(node.values)):
                    curr_entry = copy.copy(node.cpt_row_states[row_cnt])
                    curr_entry.insert(0, node.values[val_cnt])
                    if len(node.cpt_row_states) == 1:
                        curr_entry.pop()
                    self.table[tuple(curr_entry)] = node.cpt_row_vals[row_cnt][val_cnt]

    def prod(self, potent):
        use_nodes = self.nodes
        potent_table = potential(use_nodes=use_nodes)

        for pair in potent_table.table:
            vals = []
            for node in potent_table.nodes:
                vals.append((node, pair))
            states = []
            for var, state in vals:
                if var in self.nodes:
                    states.append(state[0])
            states_ = []
            for var, state in vals:
                if var in potent.nodes:
                    states_.append(state[use_nodes.index(var)])

            potent_table.table[pair] = self.table[pair] * potent.table[(states_[-1],)]
        return potent_table

    def has_changed(self, message):
        if len(self.nodes) != len(message.nodes):
            return True, -1
        for i in range(len(self.nodes)):
            if self.nodes[i] != message.nodes[i]:
                return True, -1

        converge = 0
        for key in self.table:
            converge += abs(self.table[key] - message.table[key])

        if converge > 0:
            return True, converge
        else:
            return False, 0

    def sum_out(self, node):
        curr_nodes = copy.copy(self.nodes)
        loc = curr_nodes.index(node)
        new_nodes = [n for n in curr_nodes if n.name != node.name]
        potent = potential(use_nodes=new_nodes)
        for pair in self.table:
            new_pair = list(pair)
            new_pair.pop(loc)
            new_pair = tuple(new_pair)
            try:
                potent.table[new_pair] += self.table[pair]
            except:
                pass
        return potent

    def get_prob(self):
        total = 0.
        for group in self.table:
            total += self.table[group]
        for group in self.table:
            self.table[group] /= total


class bayes_model(object):
    def __init__(self):
        self.nodes = {}


class bayes_node(object):
    def __init__(self, name):
        self.name = name
        self.cpt_row_states = []
        self.cpt_row_vals = []
        self.card = 0
        self.values = []
        self.parents = []
        self.num_parents = 0
        self.children = []
        self.num_children = 0







