from copy import copy
from time import sleep

import numpy as np
# import plotly.graph_objects as go

import networkx as nx

from army import Armies
from sectors import Sectors

global game_running


import matplotlib.pyplot as plt
import networkx as nx


if __name__ == '__main__':

    node_names = ['Mordor','Gondor','Shire','Rohan','Rivendell','Minas Tirith']
    node_color = ['red','blue','green','blue','green','orange']
    node_owner = [0,1,2,1,4,3]
    node_value = [1.0,1.0,1.0,1.0,1.0,1.0]
    edge_weights = [('Mordor','Gondor',0.6),
    ('Shire','Rohan',0.2),
    ('Gondor','Minas Tirith',0.1),
    ('Rohan','Shire',0.7),
    ('Rivendell','Shire',0.9),
    ('Gondor','Rohan',0.3),]

    army_names = ['Grond','Gandalf','Orcs','Hobbits']
    army_owners = [0,1,0,2]
    army_values = [1.0,1.0,1.0,1.0]
    army_locations = ['Mordor','Rivendell','Rohan','Shire']



    sectors = Sectors(node_names,node_owner,node_value,edges=edge_weights)
    armies = Armies(army_names, army_owners, army_values, army_locations,sectors)


    # path, distances = sectors.find_shortest_path('Mordor','Rivendell')

    dt = 0.1
    game_running = True
    armies.move_army('Hobbits','rivendell')
    armies.time_step(dt)
    armies.takeover_sector('Gandalf')
    armies.move_army('Gandalf','shire')
    armies.time_step(dt)
    armies.move_army('Hobbits',['Rohan','Gondor'])
    armies.move_army('Hobbits','Shire')
    armies.time_step(dt)
    armies.time_step(dt)
    armies.time_step(dt)


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
                    print(f"{t:2.2f}")


    x = threading.Thread(target=wait_for_input, args=())
    x2 = threading.Thread(target=run_game)

    x2.start()
    x.start()

    x.join()


    # while True:
    #
    #     sleep(0.01)
    #





























