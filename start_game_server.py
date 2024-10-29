import threading

import logging
from src.army import Armies
from conf.authentication import auth_dict
from src.game import Vibinus
from src.log import setup_logger
from src.sectors import Sectors
from src.server import VibinusServer, run_server_async
from conf.map.small_world import zones, roads, teams
from conf.settings import COLORS, COSTS, COLORS_RGB
import pygame
# from conf.world_middle_earth import zones, roads, teams

global game_running

if __name__ == '__main__':
    draw_game = True
    width = 0
    height = 600
    setup_logger()
    pygame.init()


    # image_path = None
    image_path = 'conf/map/small_world_small.jpg'
    img = pygame.image.load(image_path)
    if width <= 0 or height <= 0:
        width = img.get_width()
        height = img.get_height()
    screen = pygame.display.set_mode((width, height))

    pygame.display.set_caption('Vibinus')
    pygame.display.flip()


    sectors = Sectors(zones, edges=roads, image_path=image_path, color_dict=COLORS_RGB, screen=screen)
    armies = Armies(teams, sectors, color_dict=COLORS_RGB, credit_cost_dict=COSTS, screen=screen)
    sectors.armies = armies
    armies.set_ally(0,3)
    armies.set_ally(3,0)

    armies.move_army('gandalf',6)
    file_checkpoint = 'data/vibinus_gamestate.pkl'
    game = Vibinus(sectors=sectors,armies=armies,auth_dict=auth_dict,file=file_checkpoint, draw=draw_game)

    # game = game.load(file_checkpoint) # Uncomment this if you want to start from the previous saved state
    server = VibinusServer(game)

    # x_game = threading.Thread(target=game.run_game)
    x_server = threading.Thread(target=run_server_async,args=((server,)))

    x_server.start()
    game.run_game()
    # x_game.start()

























