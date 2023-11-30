import threading

import matplotlib
# import plotly.graph_objects as go

from src.army import Armies
from conf.authentication import auth_dict
from conf.teams import teams
from conf.world import zones, roads
from src.game import Vibinus
from src.sectors import Sectors
from src.server import VibinusServer, run_server_async

global game_running

matplotlib.use('TkAgg')

if __name__ == '__main__':
    zones = zones
    roads = roads
    sectors = Sectors(zones,edges=roads)
    armies = Armies(teams,sectors)
    dt = 0.1
    file_checkpoint = 'data/vibinus_gamestate.pkl'
    game = Vibinus(sectors=sectors,armies=armies,auth_dict=auth_dict,dt=dt,file=file_checkpoint)

    # game = game.load(file_checkpoint) # Uncomment this if you want to start from the previous saved state
    server = VibinusServer(game)

    x_server = threading.Thread(target=game.run_game)
    x_game = threading.Thread(target=run_server_async,args=((server,)))

    x_game.start()
    x_server.start()

























