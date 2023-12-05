import logging
import pickle
import random
from time import sleep

import numpy as np
from matplotlib import pyplot as plt

from src.utils import InsufficientAccessError

logger = logging.getLogger('vibinus')

class Vibinus:
    def __init__(self,armies, sectors, auth_dict, file, dt=0.1):
        self.filename = file
        self.running = False
        self.dt = dt
        self.autosave_every_n_seconds = 3
        self.t = 0.0
        self._t_last_save = 0.0
        self.armies = armies
        self.sectors = sectors
        self.auth = auth_dict
        n = len(auth_dict)
        self.usernames = []
        self.passwords = []
        self.access_level = -1 * np.ones(n, dtype=int)
        self.team = -1 * np.ones(n,dtype=int)
        self.army_id = -1 * np.ones(n,dtype=int)
        for i, (user, info) in enumerate(auth_dict.items()):
            self.usernames.append(user)
            self.passwords.append(info[0])
            self.access_level[i] = info[1]
            self.team[i] = info[2]
            self.army_id[i] = info[3]
        self.ids = np.arange(n)
        self._id_dict = dict(zip(self.usernames,self.ids))

    def save(self):
        with open(self.filename, 'wb') as outp:
            pickle.dump(self, outp, pickle.HIGHEST_PROTOCOL)
        logger.debug(f"saved state to {self.filename}")

    @staticmethod
    def load(filename):
        with open(filename, 'rb') as inp:
            game = pickle.load(inp)
        return game

    def user_id(self,name):
        return self._id_dict[name]

    def get_name_and_id(self,name_or_id,mode):
        try:
            id = int(name_or_id)
            if mode == 'team':
                name = self.armies.team_names[id]
            elif mode == 'army':
                name = self.armies.names[id]
            elif mode == 'sector':
                name = self.sectors.names[id]
            else:
                raise NotImplementedError(f"{mode} not implemented")
        except:
            name = name_or_id
            if mode == 'team':
                id = self.armies.team_name_id(name)
            elif mode == 'army':
                id = self.armies.name_id(name)
            elif mode == 'sector':
                id = self.sectors.name_id(name)
            else:
                raise NotImplementedError(f"{mode} not implemented")
        return name, id

    def parse_command(self, user_id, args, execute_command=True):
        """
        We evaluate that the command exist and is allowed to be called by the user.
        Furthermore we evaluate that the command has the required amount of arguments and that those arguments are potentially valid (sector names are spelled correctly ect.)
        """
        command = args.pop(0)

        access_level = self.access_level[user_id]
        if command == 'move':
            if access_level in [0,1]: #user is admin or team
                assert len(args) == 2
                army_name_or_id = args.pop(0)
                army_name, army_id = self.get_name_and_id(army_name_or_id,'army')
            else:
                army_id = self.army_id[user_id]
                army_name = self.armies.names[army_id]
                assert len(args) == 1, f"{command} command expected 1 argument, {len(args)} were given."
                args = args[0]
            sector_name, sector_id = self.get_name_and_id(args,'sector')
            command_fn = self.armies.move_army
            command_args = (army_name, [sector_name])
        elif command == 'capture':
            if access_level in [2,3]: # army_id is fixed
                army_id = self.army_id[user_id]
                army_name = self.armies.names[army_id]
                assert len(args) == 0, f"{command} command expected 0 argument, {len(args)} were given."
            else:
                assert len(args) == 1, f"{command} command expected 1 argument, {len(args)} were given."
                army_name, army_id = self.get_name_and_id(args[0],'army')
            command_fn = self.armies.takeover_sector
            command_args = (army_id,)
        elif command == 'ally':
            if access_level in [0]: # Admin
                assert len(args) == 2, f"{command} command expected 2 argument, {len(args)} were given."
                team_1_name, team_1_id = self.get_name_and_id(args.pop(0),'team')
                team_2_name, team_2_id = self.get_name_and_id(args.pop(0),'team')
            elif access_level in [1,2]: # Team, Captain
                assert len(args) == 1, f"{command} command expected 1 argument, {len(args)} were given."
                team_1_id = self.team[user_id]
                team_2_name, team_2_id = self.get_name_and_id(args[0], 'team')
            else:
                raise InsufficientAccessError("Nop")
            command_fn = self.armies.set_ally
            command_args = (team_1_id, team_2_id)
        elif command == 'break_alliance':
            if access_level in [0]:
                assert len(args) == 2, f"{command} command expected 2 argument, {len(args)} were given."
                team_1_name, team_id = self.get_name_and_id(args.pop(0),'team')
            elif access_level in [1,2]: # Team, Captain
                assert len(args) == 1, f"{command} command expected 1 argument, {len(args)} were given."
                team_id = self.team[user_id]
            else:
                raise InsufficientAccessError("Nop")
            command_fn = self.armies.break_alliance
            command_args = (team_id,)
        elif command == 'queue' or command == 'q':
            status = self.parse_command(user_id, args, execute_command=False)
        elif command == 'pause':
            if access_level in [0]: #Admin
                self.running = False
            else:
                raise InsufficientAccessError("Nop")
        elif command == 'start':
            if access_level in [0]: #Admin
                self.running = True
            else:
                raise InsufficientAccessError("Nop")
        elif command == 'rearm':
            if access_level in [0,1]:
                assert len(args) == 2, f"{command} command expected 2 argument, {len(args)} were given."
                army = args.pop(0)
                amount = args.pop(0)
                army_name, army_id = self.get_name_and_id(army,'army')
                if access_level in [1]:
                    assert self.armies.army_team_id[army_id] == self.team[user_id]
            else:
                assert len(args) == 1, f"{command} command expected 1 argument, {len(args)} were given."
                army_id = self.army_id[user_id]
                amount = args.pop(0)
            command_fn = self.armies.rearm
            command_args = (army_id, amount)
        elif command == 'give':
            if access_level in [0, 1]:
                assert len(args) >= 3, f"{command} command expected 3 argument, {len(args)} were given."
                army_1_name, army_1_id = self.get_name_and_id(args.pop(0), 'army')
                if access_level in [1]:
                    assert self.armies.army_team_id[army_1_id] == self.team[user_id]
            else:
                assert len(args) >= 2, f"{command} command expected 2 argument, {len(args)} were given."
                army_1_id = self.army_id[user_id]
            army_2_name, army_2_id = self.get_name_and_id(args.pop(0), 'army')
            item = args.pop(0)
            if len(args) >= 1:
                amount = args.pop(0)
                assert amount > 0, "You cannot transfer negative amount of credits"
            else:
                amount = 1
            if item == 'credit':
                assert self.armies.credits[army_1_id] >= amount, "You cannot give more credits than you own"
            else:
                amount = 1
                assert item in self.armies.relics[army_1_id], "You cannot give a relic you do not own"
            command_fn = self.armies.transfer_item
            command_args = (army_1_id,army_2_id,item,amount)
        elif command == 'swap':
            if access_level in [0, 1, 2]:
                assert len(args) == 2, f"{command} command expected 2 argument, {len(args)} were given."
                army_1_name, army_1_id = self.get_name_and_id(args.pop(0), 'army')
                army_2_name, army_2_id = self.get_name_and_id(args.pop(0), 'army')
                if access_level in [1, 2]:
                    assert self.armies.army_team_id[army_1_id] == self.team[user_id]
                    assert self.armies.army_team_id[army_2_id] == self.team[user_id]
            else:
                raise InsufficientAccessError("Nop")
            command_fn = self.armies.swap_armies
            command_args = (army_1_id,army_2_id)
        elif command == 'retreat':
            if access_level in [0,1]:
                army_name, army_id = self.get_name_and_id(args.pop(0), 'army')
                if access_level in [1]:
                    assert self.armies.army_team_id[army_id] == self.team[user_id]
            else:
                army_id = self.army_id[user_id]
            valid_sector_ids = self.armies.get_valid_retreats(army_id)
            if len(args) == 1:
                sector_name, sector_id = self.get_name_and_id(args.pop(0), 'sector')
                assert sector_id in valid_sector_ids, f"Cannot retreat to {sector_name}."
            else:
                if len(valid_sector_ids) > 0:
                    sector_id = random.choice(valid_sector_ids)
                else:
                    sector_id = self.sectors.death_id
            command_fn = self.armies.retreat
            command_args = (army_id,sector_id)
        elif command == "buy_stratagem":
            if access_level in [0,1]:
                army_name, army_id = self.get_name_and_id(args.pop(0), 'army')
                if access_level in [1]:
                    assert self.armies.army_team_id[army_id] == self.team[user_id]
            else:
                army_id = self.army_id[user_id]
            assert self.armies.fighting[army_id], f"Army {self.armies.names[army_id]} is not currently fighting."
            command_fn = self.armies.buy_stratagem
            command_args = (army_id)
        elif command == 'status': # army/team, id/name
            mode = args.pop(0)
            assert mode in ['army', 'team']
            assert len(args) == 1, f"{command} command expected 1 argument, {len(args)} were given."
            name, id = self.get_name_and_id(args.pop(0),mode)
            if access_level in [1,2,3]:
                if mode == 'army':
                    assert self.armies.army_team_id[id] == self.team[user_id]
                    command_fn = self.armies.status_army
                else:
                    assert id == self.team[user_id]
                    command_fn = self.armies.status_team
            command_args = (id,)
        elif command == 'speedup':
            if access_level in [0,1]:
                army_name, army_id = self.get_name_and_id(args.pop(0), 'army')
                if access_level in [1]:
                    assert self.armies.army_team_id[army_id] == self.team[user_id]
            else:
                army_id = self.army_id[user_id]
            command_fn = self.armies.speedup
            command_args = (army_id,)
        elif command == 'award_vp' or command == 'vp':
            if access_level in [0]:
                assert len(args) == 2, f"{command} command expected 2 argument, {len(args)} were given."
            else:
                raise InsufficientAccessError("Nop")
            team_name, team_id = self.get_name_and_id(args.pop(0), 'team')
            amount = float(args.pop(0))

            command_fn = self.armies.award_vp
            command_args = (team_id, amount)

        else:
            raise NotImplementedError(f"{command}")

        if execute_command:
            status = command_fn(*command_args)
            return status
        else:
            self.armies.queue_command(army_id, command_fn, command_args)
            return f'Queued command: {command} {army_id} {command_args}'

    def run_game(self):
        logger.info("Starting game...")
        dt = self.dt
        self.draw_game()
        self.running = True
        while True:
            sleep(dt)
            while self.running:
                sleep(dt)
                self.t += dt
                self.armies.time_step(dt)
                self.sectors.time_step(dt)
                self.update_game()
                if (self.t - self._t_last_save) > self.autosave_every_n_seconds:
                    self.save()
                    self._t_last_save = self.t
                #
                # plt.clf()
                # sectors.draw()
                # armies.draw()
                # ax = plt.gca()
                # ax.margins(0.08)
                # plt.axis("off")
                # plt.tight_layout()
                # # plt.show()
                # plt.pause(0.01)
                # if (round(t, 2) % 1 == 0):
                #     print(f"{t:2.2f}")

    def draw_game(self):
        # plt.cla()
        self.sectors.draw()
        self.armies.draw()
        ax = plt.gca()
        plt.title(f"time = {self.t:4.1f}s")
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        # plt.show()
        plt.pause(0.01)

    def update_game(self):
        self.armies.draw()
        # ax = plt.gca()
        plt.title(f"time = {self.t:4.1f}s")
        # ax.margins(0.08)
        # plt.axis("off")
        # plt.tight_layout()
        # plt.show()
        plt.pause(0.01)





