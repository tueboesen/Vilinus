import inspect
import logging
import pickle
import random
import time
from time import sleep

import numpy as np
from matplotlib import pyplot as plt

from src.utils import InsufficientAccessError, RequirementsNotMetError

logger = logging.getLogger('vibinus')

class Vibinus:
    def __init__(self,armies, sectors, auth_dict, file, draw=False):
        self._time0 = None
        self._time0 = None
        self.draw = draw
        self.filename = file
        self.running = False
        self.end_game = False
        self.delta = 0.1
        self.autosave_every_n_seconds = 10
        self.t = 0.0
        self._t0 = None
        self._tbonus = 0.0
        self._t_last_save = 0.0
        self.time_game_end = 999999
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
        self.non_queueable_commands = ['help', 'list', 'pause', 'start','status', 'award_vp', 'ally', 'break_alliance', 'buy_stratagem', 'cancel', 'end_game','swap', 'retreat', 'speedup', 'respawn']
        self.queueable_commands = ['move', 'capture', 'rearm', 'give']

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
        """
        Given the username it returns the users id
        """
        return self._id_dict[name]

    def _get_name_and_id(self, name_or_id, mode):
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

    def parse_move(self,user_id, args):
        """
        moves an army to a sector.

        Examples:
        As user or captain: 'move sector_name_or_id'
        As team or admin: 'move army_name_or_id sector_name_or_id'
        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1]:  # user is admin or team
            assert len(args) == 2
            army_name_or_id = args.pop(0)
            army_name, army_id = self._get_name_and_id(army_name_or_id, 'army')
        else:
            army_id = self.army_id[user_id]
            army_name = self.armies.names[army_id]
            assert len(args) == 1, f"command expected 1 argument, {len(args)} were given."
            args = args[0]
        sector_name, sector_id = self._get_name_and_id(args, 'sector')
        command_fn = self.armies.move_army
        command_args = (army_name, [sector_name])
        return army_id, command_fn, command_args

    def parse_help(self, user_id, args):
        """
        The help command should be followed by the command you wish to know more about.
        'help move'

        To see available commands, type: 'list'
        """
        if len(args) == 0:
            fn = self.parse_help
        else:
            try:
                fn = getattr(self, f"parse_{args[0]}")
                msg = fn.__doc__
            except:
                msg = f"{args[0]} command not recognized. see 'list' for available commands"
        if len(args) > 0 and args[0] == 'queue':
            msg += f'The following commands are queueable: \n \t \t \t {", ".join(self.queueable_commands)}'
        return msg

    def parse_list(self, user_id, args):
        """
        Lists all commands available for the user.
        """
        res = inspect.getmembers(self, predicate=inspect.ismethod)
        available_commands = []
        for name, fn in res:
            if name.startswith('parse_'):
                try:
                    fn(user_id,args)
                    available_commands.append(name[6:])
                except InsufficientAccessError as e:
                    pass
                except Exception as e:
                    available_commands.append(name[6:])
        msg = f'Available commands for {self.usernames[user_id]}: \n'
        for command in sorted(available_commands):
            msg += f"{command} \n"
        return msg

    def parse_capture(self, user_id, args):
        """
        starts to capture the sector the army is currently in.
        """
        access_level = self.access_level[user_id]
        if access_level in [2, 3]:  # army_id is fixed
            army_id = self.army_id[user_id]
            army_name = self.armies.names[army_id]
            assert len(args) == 0, f"command expected 0 argument, {len(args)} were given."
        else:
            assert len(args) == 1, f"command expected 1 argument, {len(args)} were given."
            army_name, army_id = self._get_name_and_id(args[0], 'army')
        command_fn = self.armies.takeover_sector
        command_args = (army_id,)
        return army_id, command_fn, command_args

    def parse_ally(self,user_id, args):
        """
        Docstring for ally
        """
        access_level = self.access_level[user_id]
        if access_level in [0]:  # Admin
            assert len(args) == 2, f"command expected 2 argument, {len(args)} were given."
            team_1_name, team_1_id = self._get_name_and_id(args.pop(0), 'team')
            team_2_name, team_2_id = self._get_name_and_id(args.pop(0), 'team')
        elif access_level in [1, 2]:  # Team, Captain
            assert len(args) == 1, f"command expected 1 argument, {len(args)} were given."
            team_1_id = self.team[user_id]
            team_2_name, team_2_id = self._get_name_and_id(args[0], 'team')
        else:
            raise InsufficientAccessError("Nop")
        command_fn = self.armies.set_ally
        command_args = (team_1_id, team_2_id)
        status = command_fn(*command_args)
        return status

    def parse_break_alliance(self,user_id, args):
        """
        Docstring for break_alliance
        """
        access_level = self.access_level[user_id]
        if access_level in [0]:
            assert len(args) == 2, f"command expected 2 argument, {len(args)} were given."
            team_1_name, team_id = self._get_name_and_id(args.pop(0), 'team')
        elif access_level in [1, 2]:  # Team, Captain
            assert len(args) == 1, f"command expected 1 argument, {len(args)} were given."
            team_id = self.team[user_id]
        else:
            raise InsufficientAccessError("Nop")
        command_fn = self.armies.break_alliance
        command_args = (team_id,)
        status = command_fn(*command_args)
        return status

    def parse_rearm(self,user_id, args):
        """
        Rearms your army.
        'rearm desired_battlepoints'
        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1]:
            assert len(args) == 2, f"command expected 2 argument, {len(args)} were given."
            army = args.pop(0)
            amount = args.pop(0)
            army_name, army_id = self._get_name_and_id(army, 'army')
            if access_level in [1]:
                assert self.armies.army_team_id[army_id] == self.team[user_id]
        else:
            assert len(args) == 1, f"command expected 1 argument, {len(args)} were given."
            army_id = self.army_id[user_id]
            amount = args.pop(0)
        command_fn = self.armies.rearm
        command_args = (army_id, amount)
        return army_id, command_fn, command_args

    def parse_make_steward(self, user_id, args):
        """
        Makes a teammate the steward of a sector you own

        'make_steward army_name_or_id sector_name_or_id'
        item can be either 'credit' or the name of a relic
        amount is only needed for credits

        For admin/team:
        'make_steward army1 army2 sector_name_or_id'
        where army1 is the donator, and army2 the receiver
        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1]:
            assert len(args) >= 3, f"command expected 3 argument, {len(args)} were given."
            army_1_name, army_1_id = self._get_name_and_id(args.pop(0), 'army')
            if access_level in [1]:
                assert self.armies.army_team_id[army_1_id] == self.team[user_id]
        else:
            assert len(args) >= 2, f"command expected 2 argument, {len(args)} were given."
            army_1_id = self.army_id[user_id]
        army_2_name, army_2_id = self._get_name_and_id(args.pop(0), 'army')
        sector_name, sector_id = self._get_name_and_id(args.pop(0), 'sector')
        command_fn = self.armies.make_steward
        command_args = (army_1_id, army_2_id, sector_id)
        return army_1_id, command_fn, command_args

    def parse_give(self, user_id, args):
        """
        Gives relic or credits to another army

        'give army_name_or_id item amount'
        item can be either 'credit' or the name of a relic
        amount is only needed for credits

        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1]:
            assert len(args) >= 3, f"command expected 3 argument, {len(args)} were given."
            army_1_name, army_1_id = self._get_name_and_id(args.pop(0), 'army')
            if access_level in [1]:
                assert self.armies.army_team_id[army_1_id] == self.team[user_id]
        else:
            assert len(args) >= 2, f"command expected 2 argument, {len(args)} were given."
            army_1_id = self.army_id[user_id]
        army_2_name, army_2_id = self._get_name_and_id(args.pop(0), 'army')
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
        command_args = (army_1_id, army_2_id, item, amount)
        return army_1_id, command_fn, command_args

    def parse_swap(self,user_id, args):
        """
        Swaps the location of two team armies.
        Note that both armies needs to be currently idle.

        'swap army1_name_or_id army2_name_or_id'
        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1, 2]:
            assert len(args) == 2, f"command expected 2 argument, {len(args)} were given."
            army_1_name, army_1_id = self._get_name_and_id(args.pop(0), 'army')
            army_2_name, army_2_id = self._get_name_and_id(args.pop(0), 'army')
            if access_level in [1, 2]:
                assert self.armies.army_team_id[army_1_id] == self.team[user_id]
                assert self.armies.army_team_id[army_2_id] == self.team[user_id]
        else:
            raise InsufficientAccessError("Nop")
        command_fn = self.armies.swap_armies
        command_args = (army_1_id, army_2_id)
        status = command_fn(*command_args)
        return status

    def parse_respawn(self, user_id, args):
        """
        Respawns in a random team area. This command can only be used if you are dead.
        The respawn location can be specified, but this costs x credits.

        'respawn' - respawns in a random team territory
        'respawn sector_name_or_id' respawns in the specified team territory

        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1]:
            assert len(args) >= 1, f"command expected at least 1 argument, {len(args)} were given."
            army_1_name, army_1_id = self._get_name_and_id(args.pop(0), 'army')
            if access_level in [1]:
                assert self.armies.army_team_id[army_1_id] == self.team[user_id]
        else:
            army_1_id = self.army_id[user_id]
        if len(args) > 0:
            sector_name, sector_id = self._get_name_and_id(args.pop(0), 'sector')
        else:
            sector_id = None
        command_fn = self.armies.respawn
        command_args = (army_1_id, sector_id)
        status = command_fn(*command_args)
        return status

    def parse_retreat(self,user_id, args):
        """
        Retreats your army during a battle.
        If location is provided the army will retreat to that location,
        if no location is provided the team will retreat to a random available sector.
        If no sector is available for retreat the team is destroyed.

        'retreat sector_name_or_id'
        'retreat'
        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1]:
            army_name, army_id = self._get_name_and_id(args.pop(0), 'army')
            if access_level in [1]:
                assert self.armies.army_team_id[army_id] == self.team[user_id]
        else:
            army_id = self.army_id[user_id]
        valid_sector_ids = self.armies.get_valid_retreats(army_id)
        if len(args) == 1:
            sector_name, sector_id = self._get_name_and_id(args.pop(0), 'sector')
            assert sector_id in valid_sector_ids, f"Cannot retreat to {sector_name}."
        else:
            if len(valid_sector_ids) > 0:
                sector_id = random.choice(valid_sector_ids)
            else:
                sector_id = self.sectors.death_id
        command_fn = self.armies.retreat
        command_args = (army_id, sector_id)
        status = command_fn(*command_args)
        return status

    def parse_buy_stratagem(self,user_id, args):
        """
        buys a stratagem for your army during a battle.
        'buy_stratagem'
        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1]:
            army_name, army_id = self._get_name_and_id(args.pop(0), 'army')
            if access_level in [1]:
                assert self.armies.army_team_id[army_id] == self.team[user_id]
        else:
            army_id = self.army_id[user_id]
        assert self.armies.fighting[army_id], f"Army {self.armies.names[army_id]} is not currently fighting."
        command_fn = self.armies.buy_stratagem
        command_args = (army_id)
        status = command_fn(*command_args)
        return status

    def parse_cancel(self, user_id, args):
        """
        stops actions that are stoppable, current action and/or queued actions depending on keywords.

        'cancel' = 'cancel all' - stops all actions, both current and planned.
        'cancel queue' - empties the queue
        'cancel current' - stops whatever action you are currently doing if cancelable (fighting isn't cancelable for instance)

        Note that a move action currently being fulfilled is not cancelable, since you can't just wait between zones.
        For move actions you can replace you current move action with another move action.

        For admins/teams the command takes the shape:
        'cancel army_name_or_id queue'
        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1]:
            assert len(args) >= 1, f"command expected at least 1 argument, {len(args)} were given."
            army_name, army_id = self._get_name_and_id(args.pop(0), 'army')
            if access_level in [1]:
                assert self.armies.army_team_id[army_id] == self.team[user_id]
        else:
            army_id = self.army_id[user_id]
        if len(args) == 0 or args[0] == 'all':
            command_args = (army_id,'all')
        elif args[0] == 'queue':
            command_args = (army_id,'queue')
        elif args[0] == 'current':
            command_args = (army_id,'current')
        else:
            raise ValueError(f"cancel keyword: {args[0]},  not recognized. ")
        command_fn = self.armies.cancel_actions
        status = command_fn(*command_args)
        return status


    def parse_status(self, user_id, args):
        """
        Provides the status of your army or of your team

        'status team'
        'status army'

        For admins the command is:
        'status team team_name_or_id'
        'status army army_name_or_id'
        """
        access_level = self.access_level[user_id]
        assert len(args) > 0, f'command expected at least 1 argument, {len(args)} were given.'
        mode = args.pop(0)
        assert mode in ['army', 'team']
        if mode == 'army':
            command_fn = self.armies.status_army
            if access_level in [0, 1]:
                assert len(args) == 1, f"logged in as {self.usernames[user_id]}, command expected 2 argument, {len(args)+1} were given."
                name, id = self._get_name_and_id(args.pop(0), mode)
                if access_level in [1]:
                    assert self.armies.army_team_id[id] == self.team[user_id]
            else:
                id = self.army_id[user_id]
        else:
            command_fn = self.armies.status_team
            if access_level in [0]:
                assert len(args) == 1, f"logged in as {self.usernames[user_id]}, command expected 2 argument, {len(args)+1} were given."
                name, id = self._get_name_and_id(args.pop(0), mode)
            else:
                id = self.team[user_id]
        command_args = (id,)
        status = command_fn(*command_args)
        return status

    def parse_speedup(self,user_id, args):
        """
        Speeds up the army.
        This command needs to be finetuned and figured out how it should be used exactly.
        """
        access_level = self.access_level[user_id]
        if access_level in [0, 1]:
            army_name, army_id = self._get_name_and_id(args.pop(0), 'army')
            if access_level in [1]:
                assert self.armies.army_team_id[army_id] == self.team[user_id]
        else:
            army_id = self.army_id[user_id]
        command_fn = self.armies.speedup
        command_args = (army_id,)
        status = command_fn(*command_args)
        return status
    def parse_award_vp(self,user_id, args):
        """
        Adds x victory points (vp) to a team
        'award_vp team_name_or_id amount'
        """
        access_level = self.access_level[user_id]
        if access_level in [0]:
            assert len(args) == 2, f"command expected 2 argument, {len(args)} were given."
        else:
            raise InsufficientAccessError("Nop")
        team_name, team_id = self._get_name_and_id(args.pop(0), 'team')
        amount = float(args.pop(0))

        command_fn = self.armies.award_vp
        command_args = (team_id, amount)
        status = command_fn(*command_args)
        return status

    def parse_pause(self,user_id, args):
        """
        Pauses the game
        """
        access_level = self.access_level[user_id]
        if access_level in [0]:  # Admin
            if self.running:
                self.running = False
                self._tbonus = self.t
                logger.info("Game pause")
                return 'game paused'
            else:
                return 'game already paused'
        else:
            raise InsufficientAccessError("Nop")

    def parse_start(self,user_id, args):
        """
        Starts the game
        """
        access_level = self.access_level[user_id]
        if access_level in [0]:  # Admin
            if self.running:
                return 'game already running'
            else:
                self.running = True
                self._time0 = time.time()
                logger.info("Game started")
                return 'game started'
        else:
            raise InsufficientAccessError("Nop")

    def parse_end_game(self,user_id, args):
        """
        Ends the game, now or at specified time.

        'end_game' - ends the game now
        'end_game 1000' - ends the game once the clock reaches t=1000
        """
        access_level = self.access_level[user_id]
        if access_level in [0]:  # Admin
            if len(args) > 0:
                self.time_game_end = args[0]
            else:
                self.running = False
                self.end_game = True
                logger.info("Game ended.")
                return 'Ending game.'
        else:
            raise InsufficientAccessError("Nop")


    def parse_queue(self, user_id, args):
        """
        Queues a command, such that it will be executed once the army is next idle.
        """
        pass

    def command_selector(self, user_id, args, execute_command=True):
        """
        We evaluate that the command exist and is allowed to be called by the user.
        Furthermore, we evaluate that the command has the required amount of arguments and that those arguments are potentially valid (sector names are spelled correctly ect.)
        """
        command = args.pop(0)

        access_level = self.access_level[user_id]
        if command in self.non_queueable_commands: # Non-queueable commands
            if not execute_command:
                raise RequirementsNotMetError(f"{command} is not queueable.")
            fn = getattr(self,f"parse_{command}")
            msg = fn(user_id,args)
            return msg
        elif command == 'queue' or command == 'q': # Queue command
            status = self.command_selector(user_id, args, execute_command=False)
            return status
        elif command in self.queueable_commands: # Queueable commands
            fn = getattr(self,f"parse_{command}")
            army_id, command_fn, command_args = fn(user_id,args)
        else:
            raise NotImplementedError(f"{command}")
        if execute_command:
            status = command_fn(*command_args)
            return status
        else:
            self.armies.queue_command(army_id, command_fn, command_args)
            return f'Queued command: {command} {army_id} {command_args}'

    def run_game(self):
        """
        Runs the actual game
        """
        logger.info("Starting game...")
        self._time0 = time.time()
        delta = self.delta
        if self.draw:
            self.draw_game()
        self.running = True
        while True:
            sleep(delta)
            while self.running:
                sleep(delta)
                t_old = self.t
                self.t = time.time() - self._time0 + self._tbonus
                dt = self.t - t_old
                self.armies.time_step(dt)
                self.sectors.time_step(dt)
                if self.draw:
                    self.draw_game_updates()
                if (self.t - self._t_last_save) > self.autosave_every_n_seconds:
                    self.save()
                    self._t_last_save = self.t
                if self.t >= self.time_game_end:
                    self.running = False
                    self.end_game = True
                    logger.info("Game ended.")
            if self.end_game:
                self.armies.end_game_bonuses()
                logger.info(self.armies.status_game())
                break

    def draw_game(self):
        """
        Draws the game the first time around
        """
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

    def draw_game_updates(self):
        """
        Updates the drawing of the game
        """
        self.armies.draw()
        # ax = plt.gca()
        plt.title(f"time = {self.t:4.0f}s")
        # ax.margins(0.08)
        # plt.axis("off")
        # plt.tight_layout()
        # plt.show()
        plt.pause(0.01)





