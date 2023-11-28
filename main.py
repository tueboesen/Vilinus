from copy import copy
from time import sleep
import time
import threading

import matplotlib
import numpy as np
# import plotly.graph_objects as go

import networkx as nx

from army import Armies
from game import Vibinus
from sectors import Sectors

global game_running


import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
import networkx as nx


if __name__ == '__main__':

    node_names = ['Mordor','Gondor','Shire','Rohan','Rivendell','Tirith']
    node_color = ['red','blue','green','blue','green','orange']
    node_owner = [0,1,2,1,4,3]
    node_value = [1.0,1.0,1.0,1.0,1.0,1.0]
    edge_weights = [('Mordor','Gondor',0.6),
    ('Shire','Rohan',0.2),
    ('Gondor','Tirith',0.1),
    ('Rohan','Shire',0.7),
    ('Rivendell','Shire',0.9),
    ('Gondor','Rohan',0.3),]

    teams = [['Good',[('Gandalf','Rivendell',1.0)]]]
    teams += [['Evil',[('Grond','Mordor',1.0), ('Orcs','Tirith',1.0)]]]
    teams += [['Others',[('Hobbits','Shire',1.0)]]]


    auth_dict = {'admin': ("hemmeligt", 0, -1, -1),
                 'team': ("gandalfisgreat", 1, 0, -1),
                 'captain': ("password", 2, 1, 1),
                 'private': ("123", 3, 2, 3)
                 }



    sectors = Sectors(node_names,node_owner,node_value,edges=edge_weights)
    armies = Armies(teams,sectors)
    armies.move_army('Hobbits','rivendell')
    armies.move_army(0,2)
    armies.move_army(0,[2,3])
    armies.move_army(0,'[2,3]')


    dt = 0.1
    game = Vibinus(sectors=sectors,armies=armies,auth_dict=auth_dict,dt=dt)

    # game.user_logon('admin',auth_dict['admin'][0])



    x_private = threading.Thread(target=game.user_logon, args=('private',auth_dict['private'][0]))
    x_admin = threading.Thread(target=game.user_logon, args=('admin',auth_dict['admin'][0]))
    x2 = threading.Thread(target=game.run_game)

    x2.start()
    # x_private.start()
    x_admin.start()

    # x_private.join()


    # # path, distances = sectors.find_shortest_path('Mordor','Rivendell')
    #
    # game_running = True
    # armies.move_army('Hobbits','rivendell')
    # armies.time_step(dt)
    # armies.move_army('Gandalf','shire')
    # armies.takeover_sector('Gandalf')
    # for i in range(1000):
    #     armies.time_step(dt)
    # try:
    #     armies.move_army('Hobbits',['Shire','Rohan','Gondor'])
    # except Exception as e:
    #     print(f"Action failed. {e}")
    #
    # armies.move_army('Hobbits','Shire')
    # armies.time_step(dt)
    # armies.time_step(dt)
    # armies.time_step(dt)




























