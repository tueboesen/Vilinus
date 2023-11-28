import networkx as nx
import numpy as np


class Sectors:
    def __init__(self,names,owners, values,edges):
        for name in names:
            assert ' ' not in name, f"{name} has a space character in it. Node names need to be a single word"
        self.names = [name.lower() for name in names]
        self.ids = np.arange(len(names))
        self.owners = owners
        self.values = values
        self.edges = edges
        self._id_dict = dict(zip(self.names,self.ids))

        n = len(self.ids)
        self.battle = np.zeros(n,dtype=bool)
        assert n == len(owners)
        assert n == len(values)
        assert len(names) == len(set(names))

        G = nx.Graph()
        for sector_id in self.ids:
            G.add_node(sector_id)

        for (source, dest, weight) in edges:
            source_id = self.name_id(source)
            dest_id = self.name_id(dest)
            G.add_edge(source_id, dest_id, weight=weight)
        self.G = G
        pos = nx.spring_layout(G, seed=7, k=10)  # positions for all nodes - seed for reproducibility
        self.pos = pos
        pos_shift = {}
        for key,val in self.pos.items():
            pos_shift[key] = val + [0,0.2]
        self.pos_shift = pos_shift
        self.color_ids = {0: 'blue', 1: 'red', 2:'green', 3:'orange', 4:'grey', 5:'purple'}
        self.being_captured = np.zeros(n,dtype=bool)



    def name_id(self,name):
        try:
            res = self._id_dict[name.lower()]
        except:
            raise ValueError(f"{name} is not a valid sector.")
        return res


    def node_colors(self):
        colors = [self.color_ids[owner] for owner in self.owners]
        return colors


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
