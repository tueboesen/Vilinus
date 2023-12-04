import threading

import matplotlib

from src.army import Armies
from conf.authentication import auth_dict
from src.game import Vibinus
from src.sectors import Sectors
from src.server import VibinusServer, run_server_async
from conf.map.small_world import zones, roads, teams
from conf.settings import COLORS
# from conf.world_middle_earth import zones, roads, teams

global game_running

matplotlib.use('TkAgg')
# plt.ion()

# matplotlib.use('mkTkinter')

if __name__ == '__main__':
    # image_path = None
    image_path = 'conf/map/small_world.jpg'

    sectors = Sectors(zones, edges=roads, image_path=image_path, color_dict=COLORS)
    armies = Armies(teams,sectors, color_dict=COLORS)
    armies.move_army('gandalf',2)
    dt = 0.1
    file_checkpoint = 'data/vibinus_gamestate.pkl'
    game = Vibinus(sectors=sectors,armies=armies,auth_dict=auth_dict,dt=dt,file=file_checkpoint)

    # game = game.load(file_checkpoint) # Uncomment this if you want to start from the previous saved state
    server = VibinusServer(game)

    # x_game = threading.Thread(target=game.run_game)
    x_server = threading.Thread(target=run_server_async,args=((server,)))

    x_server.start()
    game.run_game()
    # x_game.start()

























