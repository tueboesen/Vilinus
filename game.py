from time import sleep

import numpy as np
from matplotlib import pyplot as plt


class Vibinus:
    def __init__(self,armies, sectors, auth_dict, dt=0.1):
        self.running = False
        self.dt = dt
        self.t = 0.0
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

    def user_id(self,name):
        return self._id_dict[name]

    def parse_command(self, user_id, command_str, execute_command=True):
        """
        We evaluate that the command exist and is allowed to be called by the user.
        Furthermore we evaluate that the command has the required amount of arguments and that those arguments are potentially valid (sector names are spelled correctly ect.)
        """
        args = command_str.split(" ")
        command = args.pop(0)

        access_level = self.access_level[user_id]
        if command == 'move':
            if access_level in [0,1]: #user iser admin or team
                assert len(args) == 2
                army_name_or_id = args.pop(0)
                try:
                    army_id = int(army_name_or_id)
                    army_name = self.armies.names[army_id]
                except:
                    army_name = army_name_or_id
                    army_id = self.armies.name_id(army_name)
            else:
                army_id = self.army_id[user_id]
                army_name = self.armies.names[army_id]
                assert len(args) == 1
                args = args[0]
            try:
                sector_id = int(args)
                sector_name = self.sectors.names[sector_id]
            except:
                sector_id = self.sectors.name_id(args)
                sector_name = args
            command_fn = self.armies.move_army
            command_args = (army_name, [sector_name])
        elif command == 'takeover':
            if army_id is not None:
                army_name = self.armies.names[army_id]
                assert len(args) == 0
            else:
                assert len(args) == 1
                army_name_or_id = args.pop(0)
                try:
                    army_id = int(army_name_or_id)
                    army_name = self.armies.names[army_id]
                except:
                    army_name = army_name_or_id
                    army_id = self.armies.name_id(army_name)
            command_fn = self.armies.takeover_sector
            command_args = (army_name,)
        else:
            raise NotImplementedError("command not queueable")

        if execute_command:
            status = command_fn(*command_args)
            return status
        else:
            self.armies.queue_command(army_id, command_fn, command_args)
            return 'command queued'


    #
    # def user_logon(self,username,password):
    #     if username in self.auth:
    #         password_server = self.auth[username][0]
    #         assert password_server == password, "Password incorrect."
    #     else:
    #         raise f"{username} is not a valid username"
    #     user_id = self.user_id(username)
    #     user_mode = self.access_level[user_id]
    #     if user_mode == 0:
    #         self.admin_prompt(user_id)
    #     elif user_mode == 1:
    #         self.team_command(user_id)
    #     elif user_mode == 2:
    #         self.captain_prompt(user_id)
    #     elif user_mode == 3:
    #         self.private_prompt(user_id)
    #     else:
    #         raise "user_mode not recognized"

    def captain_prompt(self, user_id):
        army_id = self.army_id[user_id]
        team_id = self.team[user_id]
        army_name = self.armies.names[army_id]
        while True:
            inp = input(f"Logged in as: {self.usernames[user_id]} - enter command")
            args = inp.split(" ")
            command = args.pop(0)
            try:
                if command.lower() == "move":
                    self.armies.move_army(army_name, args[0])
                elif command.lower() == "capture":
                    self.armies.takeover_sector(army_name)
                elif command.lower() == "ally":
                    ally_team_id = self.armies.team_name_id(args[0])
                    self.armies.set_ally(team_id,ally_team_id)
                else:
                    print(f"command: {command.lower()} not recognized.")
            except Exception as e:
                print(f"Action failed. {e}")


    def private_prompt(self, user_id):
        army_id = self.army_id[user_id]
        army_name = self.armies.names[army_id]
        while True:
            inp = input(f"Logged in as: {self.usernames[user_id]} - enter command")
            args = inp.split(" ")
            command = args.pop(0)
            try:
                if command.lower() == "move":
                    self.armies.move_army(army_name, args[0])
                elif command.lower() == "capture":
                    self.armies.takeover_sector(army_name)
                elif command.lower() == "queue" or command.lower() == "q":
                    army_id, command_fn, command_args = self.parse_command(user_id, args, army_id)
                    self.armies.queue_command(army_id, command_fn, command_args)
                elif command.lower() == 'exit':
                    break
                else:
                    print(f"command: {command.lower()} not recognized.")
            except Exception as e:
                print(f"Action failed. {e}")

    def admin_prompt(self, user_id):
        while True:
            inp = input(f"Logged in as: {self.usernames[user_id]} - enter command")
            args = inp.split(" ")
            command = args.pop(0)
            if command.lower() == 'start':
                self.running = True
            elif command.lower() == 'pause':
                self.running = False
            elif command.lower() == "move":
                try:
                    assert len(args) > 1, f'admin move command needs two arguments: (army) (location). You provided: {args}'
                    self.armies.move_army(args[0], args[1])
                except Exception as e:
                    print(f"Action failed. {e}")
            else:
                print(f"command: {command.lower()} not recognized.")

    def run_game(self):
        dt = self.dt
        self.running = True
        while True:
            sleep(dt)
            while self.running:
                sleep(dt)
                self.t += dt
                self.armies.time_step(dt)
                self.draw_game()
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
        plt.cla()
        self.sectors.draw()
        self.armies.draw()
        ax = plt.gca()
        plt.title(f"time = {self.t:4.1f}s")
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        # plt.show()
        plt.pause(0.01)






