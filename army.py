import networkx as nx
import numpy as np


class Armies:
    def __init__(self,names,owners,values,locations,sectors):
        self.names = [name.lower() for name in names]
        n = len(names)
        self.ids = np.arange(n)
        self.owners = owners
        self.values = values
        self.speeds = 0.1*np.ones(n) # If you want some armies to move faster than others change this
        self.sources =  [location.lower() for location in locations]
        self.destinations = [None]*n
        self.distances = [None]*n
        self.time_to_destinations = [None]*n
        self.paths = [None] * n
        self.moving = [False] * n
        self.travel_ratio = [0.0] * n

        self._id_dict = dict(zip(self.names,self.ids))
        self.sectors = sectors
        G = nx.Graph()
        for name in self.names:
            G.add_node(name)
        self.G = G
        self.positions = [self.sectors.pos[source] for source in self.sources]
        self.color_ids = {0: 'blue', 1: 'red', 2: 'green', 3: 'orange'}


    @property
    def colors(self):
        colors = [self.color_ids[owner] for owner in self.owners]
        return colors


    @property
    def pos(self):
        return dict(zip(self.names,self.positions))


    def __len__(self):
        return len(self.names)

    def name_id(self,name):
        return self._id_dict[name]


    def move_army(self, name, destination):
        id = self.name_id(name.lower())
        assert destination.lower() in self.sectors.names, "Destination is not valid"
        # destination_old = copy(self.destinations[id])
        self.destinations[id] = destination.lower()
        path1, distances1 = self.sectors.find_shortest_path(source=self.sources[id],destination=destination)
        travel_distance_remaining1 = np.sum(distances1)

        if self.moving[id]:
            travel_distance_remaining1 = travel_distance_remaining1 + self.travel_ratio[id] * self.distances[id][0]
            path2, distances2 = self.sectors.find_shortest_path(source=self.paths[id][1],destination=destination)
            distances1.insert(0,self.distances[id][0])
            path1.insert(0,self.paths[id][1])
            travel_distance_remaining2 = np.sum(distances2) + (1 - self.travel_ratio[id]) * self.distances[id][0]
            distances2.insert(0,self.distances[id][0])
            path2.insert(0,self.paths[id][0])
        else:
            travel_distance_remaining2 = 99999

        if travel_distance_remaining1 < travel_distance_remaining2:
            self.paths[id] = path1
            self.distances[id] = distances1
            if self.moving[id]:
                self.travel_ratio[id] = 1 - self.travel_ratio[id]
                self.sources[id] = self.paths[id][0]
        else:
            self.paths[id] = path2
            self.distances[id] = distances2

        # self.time_to_destinations[id] = [dist / self.speeds[id] for dist in distances]
        self.moving[id] = True
        return
    def time_step(self,dt=0.01):
        for i in range(len(self)):
            if self.destinations[i] is not None:
                self.travel_ratio[i] += dt * self.speeds[i] / self.distances[i][0]
                # self.time_to_destinations[i][0] -= dt
                s = self.sources[i]
                d = self.paths[i][1]
                pos_source = self.sectors.pos[s]
                pos_dest = self.sectors.pos[d]
                self.positions[i] = (pos_dest - pos_source) * self.travel_ratio[i] + pos_source
                if self.travel_ratio[i] >= 1:
                    self.travel_ratio[i] = 0
                    self.paths[i].pop(0)
                    self.sources[i] = self.paths[i][0]
                    print(f"{self.names[i]} has arrived at {self.paths[i][0]}")
                    if len(self.paths[i]) == 1:
                        self.destinations[i] = None
                        self.moving[i] = False


    def draw(self):
        nx.draw_networkx_nodes(self.G, self.pos, node_color=self.colors, edgecolors='black')
        nx.draw_networkx_labels(self.G, self.pos, font_size=10, font_family="sans-serif")
