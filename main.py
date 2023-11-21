from copy import copy
from time import sleep

import numpy as np
# import plotly.graph_objects as go

import networkx as nx
global game_running


import matplotlib.pyplot as plt
import networkx as nx

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

        return

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
        nx.draw_networkx_nodes(self.G, self.pos, node_color=army_color, edgecolors='black')
        nx.draw_networkx_labels(self.G, self.pos, font_size=10, font_family="sans-serif")


node_names = ['Mordor','Gondor','Shire','Rohan','Rivendell','Minas Tirith']
node_color = ['red','blue','green','blue','green','orange']
node_owner = [0,1,2,1,1,3]
node_value = [1.0,1.0,1.0,1.0,1.0,1.0]
edge_weights = [('Mordor','Gondor',0.6),
('Shire','Rohan',0.2),
('Gondor','Minas Tirith',0.1),
('Rohan','Shire',0.7),
('Rivendell','Shire',0.9),
('Gondor','Rohan',0.3),]

army_names = ['Grond','Gandalf','Orcs','Hobbits']
army_owners = [0,1,0,1]
army_values = [1.0,1.0,1.0,1.0]
army_locations = ['Mordor','Rivendell','Rohan','Shire']


army_color = ['red','green','red','green']

sectors = Sectors(node_names,node_owner,node_value,edges=edge_weights)
armies = Armies(army_names, army_owners, army_values, army_locations,sectors)


path, distances = sectors.find_shortest_path('Mordor','Rivendell')

dt = 0.1
game_running = True
armies.move_army('Hobbits','Mordor')
# armies.time_step(dt)
# armies.time_step(dt)
# armies.move_army('Hobbits','Shire')
# armies.time_step(dt)
# armies.time_step(dt)
# armies.time_step(dt)


# while True:
#     armies.time_step(dt)

import time
import threading

#
# def time_step(sectors,armies):
#     armies

def wait_for_input(prompt='Enter command'):
    global game_running, game_ended
    game_ended = False
    while True:
        inp = input(prompt)
        args = inp.split(" ")
        command = args.pop(0)
        if command.lower() == 'start':
            game_running = True
        elif command.lower() == 'stop':
            game_ended = True
        elif command.lower() == 'pause':
            game_running = False
        elif command.lower() == "move":
            try:
                armies.move_army(args[0], args[1])
            except:
                print(f"cannot move army {args[0]} to sector {args[1]}")
        else:
            print(f"command: {command.lower()} not recognized.")


def run_game():
    global game_running
    t = 0
    while True:
        sleep(dt)
        if game_running:
            t += dt
            armies.time_step(dt)
            plt.clf()
            sectors.draw()
            armies.draw()
            ax = plt.gca()
            ax.margins(0.08)
            plt.axis("off")
            plt.tight_layout()
            # plt.show()
            plt.pause(0.01)
            if (round(t,2) % 1 == 0):
                print(f"{t:2.2f}, {armies.destinations}, {armies.time_to_destinations}")


x = threading.Thread(target=wait_for_input, args=())
x2 = threading.Thread(target=run_game)

x2.start()
x.start()

x.join()


# while True:
#
#     sleep(0.01)
#
































# edges
# nx.draw_networkx_edges(
#     G, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
# )



