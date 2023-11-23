import networkx as nx
import numpy as np


class Sectors:
    def __init__(self,names,owners, values,edges):
        self.names = [name.lower() for name in names]
        self.ids = np.arange(len(names))
        self.owners = owners
        self.values = values
        self.edges = edges

        n = len(self.ids)
        assert n == len(owners)
        assert n == len(values)
        assert len(names) == len(set(names))

        G = nx.Graph()
        for name in self.names:
            G.add_node(name)

        for (source, dest, weight) in edges:
            G.add_edge(source.lower(), dest.lower(), weight=weight)
        self.G = G
        pos = nx.spring_layout(G, seed=7, k=10)  # positions for all nodes - seed for reproducibility
        self.pos = pos
        pos_shift = {}
        for key,val in self.pos.items():
            pos_shift[key] = val + [0,0.2]
        self.pos_shift = pos_shift
        self.color_ids = {0: 'blue', 1: 'red', 2:'green', 3:'orange'}

    def node_colors(self):
        colors = [self.color_ids[owner] for owner in self.owners]
        return colors


    def find_shortest_path(self,source,destination):
        """
        Calculates the shortest path between two nodes
        We do not account for different travel times for different factions for now.
        """
        G = self.G
        paths = nx.shortest_path(G,source.lower(),destination.lower())
        # TODO check that weights are used
        # distances = [G.edges[source,paths[0]]['weight']]
        distances = []
        npaths = len(paths)
        for i in range(1,npaths):
            distances.append(G.edges[paths[i-1],paths[i]]['weight'])
        return paths, distances

    def time_step(self):
        pass

    def draw(self):
        # nodes

        nx.draw_networkx_nodes(self.G, self.pos, node_size=3000, node_color=self.node_colors())

        # node labels
        nx.draw_networkx_labels(self.G, self.pos_shift, font_size=20, font_family="sans-serif")
        # edge weight labels
        edge_labels = nx.get_edge_attributes(self.G, "weight")
        nx.draw_networkx_edges(self.G, self.pos, width=6)
        nx.draw_networkx_edge_labels(self.G, self.pos, edge_labels)
