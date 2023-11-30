import asyncio
from copy import copy
from time import sleep
import time
import threading

import matplotlib
import numpy as np
# import plotly.graph_objects as go

import networkx as nx

from army import Armies
from conf.authentication import auth_dict
from conf.teams import teams
from conf.world import zones, roads
from game import Vibinus
from sectors import Sectors
from server import VibinusServer, run_server_async

global game_running


import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
import networkx as nx


if __name__ == '__main__':
    zones = zones
    roads = roads
    sectors = Sectors(zones,edges=roads)
    armies = Armies(teams,sectors)
    armies.set_ally(0,2)
    armies.set_ally(2,0)
    armies.set_ally(3,1)
    try:
        armies.move_army('Hobbits','rivendell')
    except Exception as e:
        print(f"{e}")

    # armies.queue_command(1,'move gondor')
    # armies.move_army(0,2)
    # armies.move_army(0,[2,3])
    # armies.move_army(0,'[2,3]')




    dt = 0.1
    game = Vibinus(sectors=sectors,armies=armies,auth_dict=auth_dict,dt=dt)
    server = VibinusServer(game)
    # x_private = threading.Thread(target=game.user_logon, args=('private',auth_dict['private'][0]))
    # x_admin = threading.Thread(target=game.user_logon, args=('admin',auth_dict['admin'][0]))
    x_server = threading.Thread(target=game.run_game)
    x_game = threading.Thread(target=run_server_async,args=((server,)))

    x_game.start()
    x_server.start()

























