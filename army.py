import networkx as nx
import numpy as np


class Armies:
    def __init__(self,names,owners,values,locations,sectors):
        self.sectors = sectors
        self.names = [name.lower() for name in names]
        n = len(names)
        self.ids = np.arange(n)
        self.owners = np.asarray(owners)
        self.values = np.asarray(values)
        self.speeds = 0.1*np.ones(n) # If you want some armies to move faster than others change this
        self.paths = [[self.sectors.name_id(location.lower())] for location in locations]
        # self.paths = [[location.lower()] for location in locations]# the full path starting from where we are to where we are going, if we are not moving then it only has our current location
        self.moving = np.zeros(n,dtype=bool)
        self.capturing = np.zeros(n,dtype=bool)
        self.progress = np.zeros(n)

        self._id_dict = dict(zip(self.names,self.ids))
        G = nx.Graph()
        for name in self.names:
            G.add_node(name)
        self.G = G
        self.positions = [self.sectors.pos[source] for source in self.sources]
        self.color_ids = {0: 'blue', 1: 'red', 2: 'green', 3: 'orange'}
        self.allies = [[] for _ in range(n)]
        self.modes = ['passive']*n
        self.auto_takeover_sectors = np.ones(n,dtype=bool)


    @property
    def colors(self):
        colors = [self.color_ids[owner] for owner in self.owners]
        return colors


    @property
    def pos(self):
        return dict(zip(self.ids,self.positions))

    @property
    def sources_name(self):
        sources = [path[0] for path in self.paths_name]
        return sources

    @property
    def sources(self):
        sources = [path[0] for path in self.paths]
        return sources

    @property
    def paths_name(self):
        sources = []
        for path in self.paths:
            source = []
            for p in path:
                source.append(self.sectors.names[p])
            sources.append(source)
        return sources


    @property
    def destinations_name(self):
        dest = []
        for path in self.paths_name:
            if len(path) > 1:
                dest.append(path[1])
            else:
                dest.append(None)
        return dest

    @property
    def distances(self):
        distances = []
        for path in self.paths:
            if len(path)>1:
                dist = self.sectors.G.edges[path[0],path[1]]['weight']
                distances.append(dist)
            else:
                distances.append(0)
        return distances



    def __len__(self):
        return len(self.names)

    def name_id(self,name):
        return self._id_dict[name]

    def check_legal_move(self,id,path):
        move_allowed = True
        source = path[0]
        dest = path[1]
        if dest in self.sources_name:
            source_ids = np.where(np.asarray(self.sources_name) == dest)[0]
        else:
            source_ids = []
        if source in self.destinations_name:
            dest_ids = np.where(np.asarray(self.destinations_name) == source)[0]
        else:
            dest_ids = []
        posible_ids = list(set(source_ids).intersection(dest_ids))
        if posible_ids:
            owners_others = set(self.owners[posible_ids])
            allowed_owner_ids = set(self.owners[[id]]).union(self.allies[id])
            forbidden_ids = owners_others.difference(allowed_owner_ids)
            if len(forbidden_ids) > 0:
                move_allowed = False
                # raise ValueError(f"move not allowed since hostile army is moving on the desired path.")
        return move_allowed

    def move_army(self, name, path_name):
        if isinstance(path_name, str):
            path_name = [path_name.lower()]
        else:
            path_name = [p.lower() for p in path_name]
        path_ids = [self.sectors.name_id(p) for p in path_name]
        army_id = self.name_id(name.lower())
        for i,path_id in enumerate(path_ids):
            if i == 0:
                if self.moving[army_id]:
                    assert path_id == self.paths[army_id][1] or path_id == self.paths[army_id][0], f"Currently travelling from {self.paths[army_id][0]} to {self.paths[army_id][1]}, first sector in paths should be either of those, but was {loc}."
                else:
                    assert path_id in self.sectors.G.neighbors(self.sources[army_id]), f"{path_id} is not a neighbouring sector to {self.sources_name[army_id]}"
            else:
                assert path_id in self.sectors.G.neighbors(path_ids[i - 1]), f"{path_id} is not a neighbouring sector to {path_ids[i - 1]}"

        # Finally we need to check that the edge isn't occupied by a hostile army moving in the other direction
        path_with_origin = [self.paths[army_id][0]] + path_ids
        move_allowed = self.check_legal_move(army_id, path_with_origin)
        if move_allowed:
            if self.moving[army_id] and path_name[0] != self.paths[army_id][1]: #We flip our current source and destination
                tmp = self.paths[army_id][0]
                self.paths[army_id][0] = self.paths[army_id][1]
                self.paths[army_id][1] = tmp
                self.progress[army_id] = 1 - self.progress[army_id]
            path_with_origin = [self.paths[army_id][0]] + path_ids
            self.paths[army_id] = path_with_origin
            self.moving[army_id] = True
        return
    def takeover_sector(self,name):
        takeover_starting = True
        error_message = ""
        id = self.name_id(name.lower())
        location = self.paths[id][0]
        location_id = self.sectors.name_id(location)
        army_owner = self.owners[id]
        sector_owner = self.sectors.owners[location_id]
        if sector_owner == army_owner or sector_owner in self.allies[id]: #is the sector owned by a hostile?
            takeover_starting = False
            error_message = "Sector is owned by team or allies"
        elif self.sectors.being_captured[location_id]:
            takeover_starting = False
            error_message = "Sector is currently getting captured"
        else:
            # are any hostiles in the area?
            sources = self.sources_name
            ids_loc = np.where(sources == location)[0]
            ids_mov = np.where(self.moving == False)[0]
            factions = set(self.owners(ids_mov)).union(self.owners(ids_loc))
            ids_hostile = np.where()





    def time_step(self,dt=0.01):
        for i in range(len(self)):
            if len(self.paths[i]) > 1: #Is the army moving?
                dest = self.paths[i][1]
                dest_owner = self.sectors.owners[dest]
                if dest_owner == self.owners[i] or dest_owner in self.allies[i]:
                    speed = self.speeds[i]
                else:
                    speed = self.speeds[i] * 0.75  # lower speed due to moving into hostile sector
                self.progress[i] += dt * speed / self.distances[i]
                if self.progress[i] >= 1:
                    self.progress[i] = 0
                    self.paths[i].pop(0)
                    print(f"{self.names[i]} has arrived at {self.paths[i][0]}")
                    if len(self.paths[i]) > 1:
                        legal_move = self.check_legal_move(i,self.paths[i])
                        if not legal_move:
                            self.paths[i] = [self.paths[i][0]]
                            self.moving[i] = False
                    else:
                        self.moving[i] = False
            else:
                location_id = self.paths[i][0]

               # if self.sectors.owners[location_id]


    def draw(self):
        for i in range(len(self)):
            if len(self.paths[i]) > 1:
                s = self.sources_name[i]
                d = self.paths[i][1]
                pos_source = self.sectors.pos[s]
                pos_dest = self.sectors.pos[d]
                self.positions[i] = (pos_dest - pos_source) * self.progress[i] + pos_source

        nx.draw_networkx_nodes(self.G, self.pos, node_color=self.colors, edgecolors='black')
        nx.draw_networkx_labels(self.G, self.pos, font_size=10, font_family="sans-serif")
