import threading

import matplotlib
from matplotlib import pyplot as plt
import logging
from src.army import Armies
from conf.authentication import auth_dict
from src.game import Vibinus
from src.log import setup_logger
from src.sectors import Sectors
from src.server import VibinusServer, run_server_async
from conf.map.small_world import zones, roads, teams
from conf.settings import COLORS, COSTS

# from conf.world_middle_earth import zones, roads, teams

global game_running

matplotlib.use('TkAgg')
plt.figure(figsize=(16, 16), dpi=80)
# plt.ion()

# matplotlib.use('mkTkinter')

if __name__ == '__main__':
    setup_logger()

    # image_path = None
    image_path = 'conf/map/small_world.jpg'

    sectors = Sectors(zones, edges=roads, image_path=image_path, color_dict=COLORS)
    armies = Armies(teams, sectors, color_dict=COLORS, credit_cost_dict=COSTS)
    sectors.armies = armies
    armies.set_ally(0,3)
    armies.set_ally(3,0)

    armies.move_army('gandalf',2)
    file_checkpoint = 'data/vibinus_gamestate.pkl'
    game = Vibinus(sectors=sectors,armies=armies,auth_dict=auth_dict,file=file_checkpoint)

    # game = game.load(file_checkpoint) # Uncomment this if you want to start from the previous saved state
    server = VibinusServer(game)

    # x_game = threading.Thread(target=game.run_game)
    x_server = threading.Thread(target=run_server_async,args=((server,)))

    x_server.start()
    game.run_game()
    # x_game.start()

























