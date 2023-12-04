import networkx as nx
import numpy as np
import os.path

from matplotlib import pyplot as plt


class Sectors:
    def __init__(self, sectors, edges, color_dict, image_path=None,death_id=0):
        self.sword_icon = plt.imread('icons/battle.png')
        self.capture_icon = plt.imread('icons/capture.png')
        if image_path:
            self.image = plt.imread(image_path)
        else:
            self.image = None
        n = len(sectors)
        self.names = []
        owners = []
        values = []
        xys = []
        self.xps = []
        self.yps = []
        self.death_id = death_id
        self.polygons_given = np.zeros(n,dtype=bool)
        for i, (name, owner, value, xy, polygon) in enumerate(sectors):
            assert ' ' not in name, f"{name} has a space character in it. Node names need to be a single word"
            self.names.append(name.lower())
            owners.append(owner)
            values.append(value)
            if image_path:
                xys.append(np.asarray(xy))
            if polygon:
                xpsi = []
                ypsi = []
                self.polygons_given[i] = True
                for xp,yp in polygon:
                    xpsi.append(xp)
                    ypsi.append(yp)
                xpsi = np.asarray(xpsi)
                ypsi = np.asarray(ypsi)
                self.xps.append(xpsi)
                self.yps.append(ypsi)
            else:
                self.xps.append([])
                self.yps.append([])




        self.ids = np.arange(len(self.names))
        self.owners = np.asarray(owners)
        self.values = np.asarray(values)
        self.edges = edges
        self._id_dict = dict(zip(self.names,self.ids))
        self.color_ids = color_dict

        n = len(self.ids)
        self.battle = np.zeros(n,dtype=bool)
        assert n == len(owners)
        assert n == len(values)
        assert len(self.names) == len(set(self.names))

        G = nx.Graph()
        for sector_id in self.ids:
            G.add_node(sector_id)

        self.road_pos = []
        self.road_len = []
        for (source, dest, weight,xy) in edges:
            source_id = self.name_id(source)
            dest_id = self.name_id(dest)
            G.add_edge(source_id, dest_id, weight=weight)
            if image_path:
                self.road_pos.append(xy)
                self.road_len.append(weight)


        self.G = G
        if image_path:
            self.pos = dict(zip(self.ids,xys))
        else:
            pos = nx.spring_layout(G, seed=7, k=10)  # positions for all nodes - seed for reproducibility
            self.pos = pos
        pos_shift = {}
        for key,val in self.pos.items():
            pos_shift[key] = val + [0,0.2]
        self.pos_shift = pos_shift
        self.being_captured = np.zeros(n,dtype=bool)

    def __len__(self):
        return len(self.ids)

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
        if self.image is not None:
            for i, polygon in enumerate(self.polygons_given):
                if polygon:
                    plt.fill(self.xps[i], self.yps[i], self.color_ids[self.owners[i]], alpha=0.3)
                    self.being_captured[i] = True
                if self.battle[i]:
                    icon = self.sword_icon
                elif self.being_captured[i]:
                    icon = self.capture_icon
                else:
                    icon = None
                if icon is not None:
                    x,y = self.pos[i]
                    dx = 0.7
                    dy = 0.7
                    extent = [x-dx, x+dx, y-dy, y+dy]
                    plt.imshow(icon, zorder=1, extent=extent, alpha=0.8)

            for road,distance in zip(self.road_pos,self.road_len):
                # plt.scatter(*road,zorder=2,c='black',alpha=0.3,s=30)
                # plt.annotate(str(distance), xy=road)
                bbox_props = dict(boxstyle="circle", fc="gray", ec="black", lw=2, alpha=0.5)
                t = plt.text(*road, str(distance), ha="center", va="center",size=10, bbox=bbox_props)
            plt.imshow(self.image, zorder=0, extent=[0.0, 10.0, 0.0, 10.0])
        else:
            nx.draw_networkx_nodes(self.G, self.pos, node_size=3000, node_color=self.node_colors())
            # node labels
            nx.draw_networkx_labels(self.G, self.pos_shift, font_size=20, font_family="sans-serif")
            # edge weight labels
            edge_labels = nx.get_edge_attributes(self.G, "weight")
            nx.draw_networkx_edges(self.G, self.pos, width=6)
            nx.draw_networkx_edge_labels(self.G, self.pos, edge_labels)
