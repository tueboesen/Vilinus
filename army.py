from ast import literal_eval

import networkx as nx
import numpy as np


class Armies:
    def __init__(self,teams,sectors):
        n = 0
        for i, team in enumerate(teams):
            for j,_ in enumerate(team[1]):
                n += 1
        n_teams = len(teams)
        self.sectors = sectors
        self.team_names = []
        self.names = []
        self.paths = []
        self.values = np.ones(n)
        self.team_id = -1 * np.ones(n)

        c = 0
        for i, team in enumerate(teams):
            self.team_names.append(team[0].lower())
            for army in team[1]:
                self.names.append(army[0].lower())
                self.paths.append([self.sectors.name_id(army[1].lower())])
                self.values[c] = army[2]
                self.team_id[c] = i
                c += 1
        self._sources = -1 * np.ones(n,dtype=int)
        self._edges = -1 * np.ones(n,dtype=int)
        self.allies = -1 * np.ones(n,dtype=int)
        self._desired_allies = -1 * np.ones(n,dtype=int)
        self.ids = np.arange(n)
        self.speeds = 0.1*np.ones(n) # If you want some armies to move faster than others change this
        self.capture_speeds = 0.1 * np.ones(n)
        # self.paths = [[location.lower()] for location in locations]# the full path starting from where we are to where we are going, if we are not moving then it only has our current location
        self.moving = np.zeros(n,dtype=bool)
        self.capturing = np.zeros(n,dtype=bool)
        self.fighting = np.zeros(n,dtype=bool)
        self.progress = np.zeros(n)

        self._id_dict = dict(zip(self.names,self.ids))
        G = nx.Graph()
        for i in range(n):
            G.add_node(i)
        self.G = G
        self.positions = [self.sectors.pos[source] for source in self.sources]
        self.color_ids = {0: 'blue', 1: 'red', 2: 'green', 3: 'orange'}
        self.modes = ['passive']*n
        self.auto_takeover_sectors = np.ones(n,dtype=bool)

    def set_ally(self, army_id, ally_army_id):
        team_id = self.team_id[army_id]
        m_team = self.team_id == team_id

        ally_id = self.team_id[ally_army_id]
        self._desired_allies[m_team] = ally_id
        if self._desired_allies[ally_army_id] == team_id: #Does the others also wish to be allies with you?
            m_ally = self.team_id == ally_id
            self.allies[m_ally] = team_id
            self.allies[m_team] = ally_id




    @property
    def colors(self):
        colors = [self.color_ids[owner] for owner in self.team_id]
        return colors


    @property
    def pos(self):
        return dict(zip(self.ids,self.positions))

    # @property
    # def sources_name(self):
    #     sources = [path[0] for path in self.paths_name]
    #     return sources

    @property
    def sources(self):
        for i,path in enumerate(self.paths):
            if self.moving[i]:
                self._sources[i] = -1
            else:
                self._sources[i] = path[0]
        return self._sources

    def calculate_edge(self,path, reverse=False):
        if len(path) > 1:
            if reverse:
                res = 100 * path[1] + path[0]
            else:
                res = 100 * path[0] + path[1]
        else:
            res = -1
        return res

    @property
    def edges(self):
        for i,path in  enumerate(self.paths):
            if self.moving[i]:
                self._edges[i] = 100*path[0] + path[1]
            else:
                self._edges[i] = -1
        return self._edges


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

    def get_hostiles(self,idx):
        m_faction = self.team_id == self.team_id[idx]
        m_allies = self.team_id == self.allies[idx]
        m_hostiles = ~ (m_faction + m_allies)
        return m_hostiles


    def __len__(self):
        return len(self.names)

    def name_id(self,name):
        try:
            res = self._id_dict[name.lower()]
        except:
            raise ValueError(f"{name} is not a valid army.")
        return res

    def check_legal_move(self,id,path):
        move_allowed = True
        edge_rev = self.calculate_edge(path,reverse=True)
        edges = self.edges
        m = edges == edge_rev
        if np.sum(m) > 0:
            owners = set(self.team_id[m])
            allowed_owner_ids = set(self.team_id[[id]]).union(self.allies[[id]])
            forbidden_ids = owners.difference(allowed_owner_ids)
            if len(forbidden_ids) > 0:
                move_allowed = False
        return move_allowed

    def move_army(self, name, path_name):
        try:
            name = self.names[int(name)]
        except:
            pass

        if isinstance(path_name, str):
            try:
                assert path_name.lower() in self.sectors.names
                path_name = [path_name.lower()]
            except:
                try:
                    results = literal_eval(path_name)
                    path_name_new = []
                    if isinstance(results, list):
                        for result in results:
                            if isinstance(result, int):
                                path_name_new.append(self.sectors.names[result])
                            else:
                                path_name_new.append(result)
                    else:
                        if isinstance(results, int):
                            path_name_new.append(self.sectors.names[results])
                        else:
                            path_name_new.append(results)
                    path_name = path_name_new
                except:
                    raise ValueError(f"sector arguments not understood {path_name}")
        else:
            if isinstance(path_name, int):
                path_name = [self.sectors.names[path_name]]
            else:
                path_name_corrected = []
                for p in path_name:
                    if isinstance(p, int):
                        p = self.sectors.names[p]
                    else:
                        p = p.lower()
                    path_name_corrected.append(p)
                path_name = path_name_corrected

        path_ids = [self.sectors.name_id(p) for p in path_name]
        army_id = self.name_id(name.lower())
        assert ~self.fighting[army_id], f"currently fighting."

        for i,path_id in enumerate(path_ids):
            if i == 0:
                if self.moving[army_id]:
                    assert path_id == self.paths[army_id][1] or path_id == self.paths[army_id][0], f"currently travelling between {self.paths_name[army_id][0]} and {self.paths_name[army_id][1]}. First sector in path should be either of those, but was {path_name[0]}."
                else:
                    assert path_id in self.sectors.G.neighbors(self.sources[army_id]), f"{path_name[i]} is not a neighbouring sector to {self.paths_name[army_id][0]}."
            else:
                assert path_id in self.sectors.G.neighbors(path_ids[i - 1]), f"{path_name[i]} is not a neighbouring sector to {path_name[i - 1]}"

        # Finally we need to check that the edge isn't occupied by a hostile army moving in the other direction
        path_with_origin = [self.paths[army_id][0]] + path_ids
        move_allowed = self.check_legal_move(army_id, path_with_origin)
        if move_allowed:
            if self.moving[army_id] and path_ids[0] != self.paths[army_id][1]: #We flip our current source and destination
                tmp = self.paths[army_id][0]
                self.paths[army_id][0] = self.paths[army_id][1]
                self.paths[army_id][1] = tmp
                self.progress[army_id] = 1 - self.progress[army_id]
            path_with_origin = [self.paths[army_id][0]] + path_ids
            self.paths[army_id] = path_with_origin
            self.moving[army_id] = True
        return
    def takeover_sector(self,name):
        id = self.name_id(name.lower())
        location_id = self.paths[id][0]
        army_owner = self.team_id[id]
        sector_owner = self.sectors.owners[location_id]
        m_armies_in_area = self.sources == location_id
        m_faction = self.team_id == self.team_id[id]
        m_allies = self.team_id == self.allies[id]
        m_hostiles = ~ (m_faction + m_allies)
        m_hostiles_in_area = m_hostiles * m_armies_in_area
        if sector_owner == army_owner or sector_owner == self.allies[id]: #is the sector owned by a hostile?
            raise "Sector is already owned by team or allies."
        elif self.sectors.being_captured[location_id]:
            raise "Sector is currently getting captured."
        elif np.sum(m_hostiles_in_area): # There are other armies in the area
            raise "Hostiles in sector."
        else:
            self.capturing[id] = True
            self.sectors.being_captured[location_id] = True
        return





    def time_step(self,dt=0.01):
        for i in range(len(self)):
            if len(self.paths[i]) > 1: #Is the army moving?
                dest = self.paths[i][1]
                dest_owner = self.sectors.owners[dest]
                if dest_owner == self.team_id[i] or dest_owner == self.allies[i]:
                    speed = self.speeds[i]
                else:
                    speed = self.speeds[i] * 0.75  # lower speed due to moving into hostile sector
                self.progress[i] += dt * speed / self.distances[i]
                if self.progress[i] >= 1:
                    self.progress[i] = 0
                    self.paths[i].pop(0)
                    loc = self.paths[i][0]
                    print(f"{self.names[i]} has arrived at {self.paths_name[i][0]}")
                    # Check for battle
                    m_armies_in_area = self.sources == loc
                    m_hostiles = self.get_hostiles(i)
                    m_battle = m_armies_in_area * m_hostiles
                    battle_in_area = np.sum(m_battle)
                    if battle_in_area:
                        if self.sectors.battle[loc]:
                            print(f'{self.names[i]} has joined the battle in {self.paths_name[i][0]}')
                        else:
                            print(f"A battle has started in {self.paths_name[i][0]}")
                            self.sectors.battle[loc] = True
                            self.fighting[i] = True
                            self.fighting[m_battle] = True


                    if len(self.paths[i]) > 1:
                        legal_move = self.check_legal_move(i,self.paths[i])
                        if not legal_move:
                            self.paths[i] = [self.paths[i][0]]
                            self.moving[i] = False
                    else:
                        self.moving[i] = False
            elif self.capturing[i]: # Continue capturing
                loc = self.paths[i][0]
                self.progress[i] += dt * self.capture_speeds[i] / self.sectors.values[loc]
                if self.progress[i] >= 1:
                    self.progress[i] = 0
                    self.sectors.owners[loc] = self.team_id[i]
                    self.sectors.being_captured[i] = False
                    self.capturing[i] = False
                    print(f"{self.names[i]} has captured {self.paths_name[i][0]}")




    def draw(self):
        for i in range(len(self)):
            if len(self.paths[i]) > 1:
                s = self.paths[i][0]
                d = self.paths[i][1]
                pos_source = self.sectors.pos[s]
                pos_dest = self.sectors.pos[d]
                self.positions[i] = (pos_dest - pos_source) * self.progress[i] + pos_source

        nx.draw_networkx_nodes(self.G, self.pos, node_color=self.colors, edgecolors='black')
        nx.draw_networkx_labels(self.G, self.pos, font_size=10, font_family="sans-serif")
