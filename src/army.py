import logging
import random
from ast import literal_eval

import networkx as nx
import numpy as np
import pygame
from matplotlib import pyplot as plt

from conf.settings import ARMY_SIZE
from src.utils import RequirementsNotMetError, draw_text, CoordinateConverter

logger = logging.getLogger('vibinus')


class Armies:
    """
    The armies class contains all information about all the armies present in a game.

    """
    def __init__(self, teams, sectors, color_dict, credit_cost_dict, army_size=ARMY_SIZE, screen=None):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self._army_boxes = []
        self._army_texts = []
        n = 0
        for i, team in enumerate(teams):
            if len(team) > 1:
                for j, _ in enumerate(team[1]):
                    n += 1
        self.truce_time = 900
        self.costs = credit_cost_dict
        self.n_teams = len(teams)
        self.sectors = sectors
        self.team_names = []
        self.vp = np.zeros(self.n_teams)
        self.names = []
        self.paths = []
        self.army_team_id = -1 * np.ones(n, dtype=int)
        self.visible = np.zeros(n, dtype=bool)

        self.battle_points = np.ones(n)
        self.credits = np.zeros(n, dtype=float)
        self.relics = [[] for _ in range(n)]
        self._speed_base = 5 * np.ones(n)  # If you want some armies to move faster than others change this
        self._speed_multiplier = np.ones(n)
        self._speed_multiplier_timeleft = np.zeros(n)
        self.moving = np.zeros(n, dtype=bool)
        self.capturing = np.zeros(n, dtype=bool)
        self.fighting = np.zeros(n, dtype=bool)
        self.rearming = np.zeros(n, dtype=bool)
        self.respawning = np.zeros(n, dtype=bool)
        self.dead = np.zeros(n, dtype=bool)
        self._rearm_target = np.zeros(n, dtype=float)
        self.progress = np.zeros(n)

        c = 0
        for i, team in enumerate(teams):
            self.team_names.append(team[0].lower())
            if len(team) > 1:
                for army in team[1]:
                    self.names.append(army[0].lower())
                    self.paths.append([self.sectors.name_id(army[1].lower())])
                    self.battle_points[c] = army[2]
                    self.credits[c] = army[3]
                    self.army_team_id[c] = i
                    if len(army) == 5:
                        self.visible[c] = army[4]
                    else:
                        self.visible[c] = True
                    c += 1
        self._sources = -1 * np.ones(n, dtype=int)
        self._edges = -1 * np.ones(n, dtype=int)
        self.team_allies = -1 * np.ones(self.n_teams, dtype=int)
        self.team_truce = -1 * np.ones(self.n_teams, dtype=int)
        self.army_allies = -1 * np.ones(n, dtype=int)
        self.army_truce = -1 * np.ones(n, dtype=int)
        self.truce_timer = np.zeros(self.n_teams, dtype=float)
        self._desired_allies = -1 * np.ones(self.n_teams, dtype=int)
        self._ids = np.arange(n)
        self._team_ids = np.arange(self.n_teams)

        self._command_queue = [[] for _ in range(n)]

        self._id_dict = dict(zip(self.names, self._ids))
        self._team_id_dict = dict(zip(self.team_names, self._team_ids))
        G = nx.Graph()
        for i in range(n):
            G.add_node(i)
        self.G = G
        self.positions = np.asarray([self.sectors.pos[source] for source in self.sources])
        self.color_ids = color_dict
        self.modes = ['passive'] * n
        self.auto_takeover_sectors = np.ones(n, dtype=bool)
        self.army_size = army_size
        self.respawn_len = 100 # Time it takes to respawn
        self.draw_initial()
        width, height = screen.get_size()
        self.coordinate_converter = CoordinateConverter(pixel_width=width, pixel_height=height)


    def speed(self, army_id):
        """
        Computes the speed at which an army completes a task (be that moving or capturing or rearming)
        """
        s = self._speed_base[army_id] * self._speed_multiplier[army_id]
        return s

    def status_army(self, army_id):
        """
        Compiles a string message detailing the status of an army. Designed to be returned to a client such that they can gain all relevant information about their army.
        """
        bonus_msg = ''
        progress_msg = f' Action is {self.progress[army_id] * 100:2.2f}% done.'
        credit_msg = f" Credits available: {self.credits[army_id]}"
        m_sectors_owned = self.sectors.army_owner == army_id
        sector_msg = f"Sectors owned: "
        for sector_id in self.sectors.ids[m_sectors_owned]:
            sector_msg += f"{self.sectors.names[sector_id]}, which gives the following bonus: \n"
            sector_msg += f"{self.sectors.sector_bonus[sector_id]} \n"
        if self.moving[army_id]:
            action = 'moving'
            bonus_msg = f" from sector {self.paths_name[army_id][0]} to {self.paths_name[army_id][1]}."
        elif self.capturing[army_id]:
            action = 'capturing'
        elif self.fighting[army_id]:
            action = 'fighting'
        elif self.rearming[army_id]:
            action = 'rearming'
        elif self.respawning[army_id]:
            action = 'respawning'
        else:
            action = 'idle'
            progress_msg = ''
        status = f"{self.names[army_id]} is currently {action}{bonus_msg}.{progress_msg}{credit_msg} \n {sector_msg}"
        return status

    def status_team(self, team_id):
        """
        Compiles a string message detailing the status of a team. Designed to be returned to a client such that they can gain all relevant information about their team.
        """
        # m_armies = self.army_team_id == team_id
        # army_ids = self._ids[m_armies]
        # sectors_owned = self.sectors
        # status = (f"{self.team_names[team_id]} currently control {len(sectors)}, which generate {x} credits and {y} victory points pr minute."
        status = f"The team currently has {self.vp[team_id]} victory points."
        return status

    def status_game(self):
        """
        Compiles information about the game, this is not designed to be called by individual clients since it gives secret information like the VP amount for each team.
        This is designed to be called at the end of a game by the server itself to broadcast the final scoring.
        """
        vp = self.vp
        names = self.team_names
        indices = np.argsort(vp)
        msg = 'Victory points pr team: \n'
        for i, idx in enumerate(reversed(indices)):
            msg += f"{i}) {names[idx]:50}: {vp[idx]:5.2f} \n"
        return msg

    def buy_stratagem(self, army_id):
        """
        Command to buy a stratagem, can only be used by an army currently in combat.
        """
        assert self.armies.fighting[
            army_id], f"Buying stratagem failed. Army {self.names[army_id]} is not currently fighting."
        assert self.credits[army_id] >= self.costs['stratagem']
        self.credits[army_id] -= self.costs['stratagem']
        return f"Army {self.names[army_id]} successfully bought a stratagem."

    def speedup(self, army_id):
        """
        Speeds up an army for the next 600 seconds. This gives a general speedup to that army when it completes various tasks.
        """
        assert self.credits[army_id] >= self.costs['speedup']
        self._speed_multiplier[army_id] = 1.25
        if self._speed_multiplier_timeleft[army_id] < 0:
            self._speed_multiplier_timeleft[army_id] = 600
        else:
            self._speed_multiplier_timeleft[army_id] += 600
        self.credits[army_id] -= self.costs['speedup']
        return

    def award_vp(self, team_id, amount):
        """
        Gives x vp to a team (designed for admins only)
        """
        self.vp[team_id] += amount
        return

    def end_game_bonuses(self):
        """
        This function should provide any end game bonuses/penalties to teams/players
        """
        pass

    def queue_command(self, army_id, fn, args):
        """
        Queues an army command for later execution. queued commands are executed when the army is idle.
        """
        self._command_queue[army_id].append((fn, args))

    def make_steward(self, army_id1, army_id2, sector_id):
        """
        Transfers ownership of sector_id from army_id1 to army_id2
        """
        assert not self.fighting[army_id1], 'Cannot transfer ownership of sector while fighting. '
        assert not self.fighting[army_id2], 'Cannot transfer ownership of sector to someone currently fighting. '
        assert self.army_team_id[army_id1] == self.army_team_id[army_id2], "Ownership of sectors can only be transferred between armies in the same team."
        assert self.sectors.army_owner[sector_id] == army_id1, f'You cannot transfer ownership of sectors you do not own. {self.names[self.sectors.army_owner[sector_id]]} currently owns {self.sectors.names[sector_id]}.'
        self.sectors.army_owner[sector_id] = army_id2
        return


    def transfer_item(self, army_id1, army_id2, item, amount):
        """
        Transfers item from army_id1, to army_id2
        if the item being transferred is credits, then amount is relevant.
        """
        assert not self.fighting[army_id1], 'Item transfer failed. You cannot trade items when fighting.'
        if item == 'credit':
            assert amount > 0, "You cannot transfer negative amount of credits"
            assert self.credits[
                       army_id1] >= amount, f"{self.names[army_id1]} has insufficient credits. Tried to transfer {amount} credits, but had {self.credits[army_id1]} credits available."
            self.credits[army_id1] -= amount
            self.credits[army_id2] += amount
        else:
            assert self.credits[army_id1] >= self.costs['send_item']
            self.relics[army_id1].remove(item)
            self.relics[army_id2].append(item)
            self.credits[army_id1] -= self.costs['send_item']
        return

    def cancel_actions(self, army_id, mode):
        """
        Cancels the actions of an army

        if mode == current
         then just the current action is cancelled.
        if mode == all
         then all actions both current and queued actions are cancelled
        if mode == queue
         then only queued actions are removed
        """
        msg = ''
        if mode in ['current', 'all']:
            if self.capturing[army_id]:
                self.capturing[army_id] = False
                self.progress[army_id] = 0
                loc = self.paths[army_id][0]
                self.sectors.being_captured[loc] = False
                msg += f'Capture of {self.sectors.names[loc]} was cancelled.'
            elif self.rearming[army_id]:
                self.rearming[army_id] = False
                msg += f"Rearming was cancelled, current army battle points = {self.battle_points[army_id]:2.0}. "
        if mode in ['all', 'queue']:
            q = self._command_queue[army_id]
            if len(q) == 0:
                msg += f"queue was already empty."
            else:
                msg += f"Removed {len(q)} orders from queue: \n"
                for i in range(len(q)):
                    msg += f"{q} \n"
        if msg == '':
            msg = 'Nothing to cancel.'
        return msg

    def swap_armies(self, army_id1, army_id2):
        """
        Swap the position of army_id1, and army_id2
        """
        assert self.idle[army_id1] == self.idle[army_id2] == True, "Both armies need to be idle for a swap to happen."
        self.paths[army_id1], self.paths[army_id2] = self.paths[army_id2], self.paths[army_id1]
        self.positions[army_id1], self.positions[army_id2] = self.positions[army_id2], self.positions[army_id1]
        return

    def rearm(self, army_id, desired_amount):
        """
        Starts the rearming of army_id up to the desired amount of battle points.
        """
        assert f"desired battle points {desired_amount} are lower than current battle points {self.battle_points[army_id]}"
        assert self.idle[army_id], f"Army {self.names[army_id]} is not currently idle."
        sector_id = self.paths[army_id][0]
        sector_team_id = self.sectors.team_owner(sector_id)
        team_id = self.army_team_id[army_id]
        assert team_id == sector_team_id or self.team_allies[
            team_id] == sector_team_id, f"Army {self.names[army_id]} is not in a friendly sector."
        self.rearming[army_id] = True
        self._rearm_target[army_id] = desired_amount
        status = f"Rearming {self.names[army_id]} from {self.battle_points[army_id]} bp to {desired_amount} bp."
        return status

    def get_valid_retreats(self, army_id):
        """
        Get the possible retreats available to army_id
        """
        assert self.fighting[
            army_id], f'Failed to get retreat sectors. Army {self.names[army_id]} is not currently fighting.'
        team_id = self.army_team_id[army_id]

        m_nn = list(self.sectors.G.neighbors(self.sources[army_id]))
        m_friendly_sector = self.sectors.army_owner == team_id | self.sectors.army_owner == self.team_allies[team_id]

        m = m_nn * m_friendly_sector
        valid_sector_ids = self.sectors.ids[m]
        remove_sectors = np.zeros(len(valid_sector_ids),
                                  dtype=bool)  # We remove sectors that does not have the required supply
        for i, sector_id in enumerate(valid_sector_ids):
            path = [self.paths[army_id][0], sector_id]
            try:
                self.check_legal_move(army_id, path)
            except:
                remove_sectors[i] = True
        return valid_sector_ids

    def retreat(self, army_id, sector_id):
        """
        Retreats army_id to sector_id
        """
        assert self.fighting[army_id], f'Failed to retreat army. Army {self.names[army_id]} is not currently fighting.'

        if sector_id == self.sectors.death_id:
            self.fighting[army_id] = False
            self.paths[army_id] = [sector_id]
            self.positions[army_id] = self.sectors.pos[sector_id]
        else:
            assert sector_id in self.get_valid_retreats(
                army_id), f"Failed to retreat army {self.names[army_id]} to sector {self.sectors.names[sector_id]}. Sector {self.sectors.names[sector_id]} is not a valid retreat path."
            self.fighting[army_id] = False
            self.move_army(army_id, sector_id)
        if not self.check_for_battle(sector_id):
            m_armies_in_area = self.sources == sector_id
            self.fighting[m_armies_in_area] = False
            self.sectors.battle[sector_id] = False
        return

    def check_for_battle(self, sector_id):
        """
        Check whether a battle is currently happening in a sector
        """
        m_armies_in_area = self.sources == sector_id
        army_factions = self.army_team_id[m_armies_in_area]
        factions = np.unique(army_factions)
        if len(factions) < 2:
            battle = False
        elif len(factions) > 2:
            battle = True
        else:
            if factions[1] == self.team_allies[factions[0]]:
                battle = False
            else:
                battle = True
        return battle

    def set_ally(self, team_id, ally_team_id):
        """
        team_id desires to be an ally with ally_team_id.
        if ally_team_id already desires to be an ally of team_id then an official alliance is declared.
        """
        m_team = self.army_team_id == team_id
        self._desired_allies[team_id] = ally_team_id
        old_ally_team_id = self.team_allies[team_id]

        if old_ally_team_id != -1:  # Check if the old ally also wants to break the alliance
            old_ally_wish_to_break_alliance = self._desired_allies[old_ally_team_id] != team_id
        else:
            old_ally_wish_to_break_alliance = False
        if old_ally_wish_to_break_alliance:
            m_old_ally = self.army_team_id == old_ally_team_id
            self.team_allies[team_id] = -1
            self.team_allies[old_ally_team_id] = -1
            self.army_allies[m_team] = -1
            self.army_allies[m_old_ally] = -1
            self.team_truce[team_id] = old_ally_team_id
            self.team_truce[old_ally_team_id] = team_id
            self.army_truce[m_team] = old_ally_team_id
            self.army_truce[m_old_ally] = team_id
            self.truce_timer[team_id] = self.truce_time
            self.truce_timer[old_ally_team_id] = self.truce_time
            logger.info(
                f"Alliance between {self.team_names[team_id]} and {self.team_names[old_ally_team_id]} has ended by mutual agreement. A truce will be in place for {self.truce_time} in-game seconds.")

        if self._desired_allies[ally_team_id] == team_id:  # Does the others also wish to be allies with you?
            m_ally = self.army_team_id == ally_team_id
            self.team_allies[team_id] = ally_team_id
            self.team_allies[ally_team_id] = team_id
            self.army_allies[m_ally] = team_id
            self.army_allies[m_team] = ally_team_id
            logger.info(
                f"Alliance between {self.team_names[team_id]} and {self.team_names[ally_team_id]} has been made.")
        return

    def break_alliance(self, team_id):
        """
        Breaks any alliance team_id might have.
        """
        ally_team_id = self.team_allies[team_id]
        assert ally_team_id != -1, f"Break alliance failed. Team {self.team_names[team_id]} has no allies."
        self._desired_allies[team_id] = -1
        self._desired_allies[ally_team_id] = -1
        self.team_allies[team_id] = -1
        self.team_allies[ally_team_id] = -1
        logger.info(
            f"Alliance between {self.team_names[team_id]} and {self.team_names[ally_team_id]} has been broken by {self.team_names[team_id]}.")

    @property
    def idle(self):
        """
        Checks which armies are idle
        """
        not_idle = self.moving | self.capturing | self.fighting | self.rearming | self.respawning | self.dead
        return ~not_idle

    @property
    def colors(self):
        """
        Gives the colors of all armies
        """
        colors = [self.color_ids[owner] for owner in self.army_team_id]
        return colors

    @property
    def pos(self):
        """
        Gives the position (x,y) of all armies. This is the position used for the actual drawing.
        Position is returned as a dictionary.
        """
        return dict(zip(self._ids, self.positions))

    @property
    def sources(self):
        """
        Gives the sources of all armies, which is the location they are currently residing. if an army is moving then the source is =-1
        """
        for i, path in enumerate(self.paths):
            if self.moving[i]:
                self._sources[i] = -1
            else:
                self._sources[i] = path[0]
        return self._sources

    @staticmethod
    def calculate_edge(path, reverse=False):
        """
        A quick and dirty way generate a unique id for all directed edges
        Note this will only work if there are less than 100 sectors. If there are more than 100 sectors we should just update this number to an even larger number
        """
        if len(path) > 1:
            if reverse:
                res = 100 * path[1] + path[0]
            else:
                res = 100 * path[0] + path[1]
        else:
            res = -1
        return res

    @property
    def edges(self):
        """
        Calculates the directed edge that all armies are currently moving along if any.
        """
        for i, path in enumerate(self.paths):
            if self.moving[i]:
                self._edges[i] = 100 * path[0] + path[1]
            else:
                self._edges[i] = -1
        return self._edges

    @property
    def paths_name(self):
        """
        Returns the name of the paths rather than the id.
        """
        sources = []
        for path in self.paths:
            source = []
            for p in path:
                source.append(self.sectors.names[p])
            sources.append(source)
        return sources

    @property
    def destinations_name(self):
        dest = []
        for path in self.paths_name:
            if len(path) > 1:
                dest.append(path[1])
            else:
                dest.append(None)
        return dest

    @property
    def destinations(self):
        dest = []
        for path in self.paths:
            if len(path) > 1:
                dest.append(path[1])
            else:
                dest.append(None)
        return dest

    @property
    def distances(self):
        distances = []
        for path in self.paths:
            if len(path) > 1:
                dist = self.sectors.G.edges[path[0], path[1]]['weight']
                distances.append(dist)
            else:
                distances.append(0)
        return distances

    def get_hostiles(self, idx):
        """
        Returns a mask of all armies that are hostile to the army defined by idx
        """
        m_faction = self.army_team_id == self.army_team_id[idx]
        m_allies = self.army_team_id == self.army_allies[idx]
        m_truce = self.army_team_id == self.army_truce[idx]
        m_hostiles = ~ (m_faction + m_allies + m_truce)
        return m_hostiles

    def __len__(self):
        return len(self.names)

    def name_id(self, name):
        try:
            res = self._id_dict[name.lower()]
        except:
            raise ValueError(f"{name} is not a valid army.")
        return res

    def team_name_id(self, name):
        try:
            res = self._team_id_dict[name.lower()]
        except:
            raise ValueError(f"{name} is not a valid team.")
        return res

    def get_max_allowed_armies_in_sector(self, sector_id):
        """
        Finds the maximum allowed number of armies in a sector.
        """
        owner = self.sectors.army_owner[sector_id:sector_id + 1]
        nn = list(self.sectors.G.neighbors(sector_id))
        nn_owners = self.sectors.army_owner[nn]
        all_owners = np.hstack((owner, nn_owners))
        unique, counts = np.unique(all_owners, return_counts=True)
        # n = max(self.sectors.owners)
        armies_allowed = np.zeros(self.n_teams, dtype=int)
        armies_allowed[unique] += counts
        m = self.team_allies[unique] != -1
        armies_allowed[self.team_allies[unique[m]]] += counts[m]
        return armies_allowed

    def respawn(self,army_id, sector_id):
        """
        Respawns an army in sector_id
        if sector_id is None a random valid sector will be chosen
        """
        team_id = self.army_team_id[army_id]
        m_team_sectors = self.sectors.team_owner == team_id
        team_sector_ids = self.sectors.ids[m_team_sectors]
        assert self.respawning[army_id] == False, 'Army is already respawning'

        if sector_id is None:
            sector_id = random.choice(team_sector_ids)
        else:
            assert sector_id in team_sector_ids, "Cannot respawn in sector that does not belong to your team."
            assert self.credits[army_id] >= self.costs['respawn_in_location']
            self.credits[army_id] -= self.costs['respawn_in_location']
        self.respawning[army_id] = True
        self.progress[army_id] = 0
        self.paths[army_id] = [0, sector_id]
        return

    def get_team_armies_in_sector(self, sector_id, team_id):
        """
        Note that this both calculates the armies in the sector and armies currently moving to the sector.
        """
        m_armies_in_area = self.sources == sector_id
        m_armies_moving_to_area = self.destinations == sector_id
        m_armies = m_armies_in_area | m_armies_moving_to_area
        army_teams = self.army_team_id[m_armies]
        m_team = army_teams == team_id
        if self.team_allies[team_id] != -1:
            m_ally = army_teams == self.team_allies[team_id]
        else:
            m_ally = 0
        alliance_armies_in_area = np.sum(m_team) + np.sum(m_ally)
        return alliance_armies_in_area

    def check_legal_move(self, id, path):
        """
        Check whether an army defined by id, is allowed to move along the path given
        """
        team_id = self.army_team_id[id]
        dest = path[1]
        # check supplies is there enough to allow the army to move?
        team_armies_allowed = self.get_max_allowed_armies_in_sector(dest)
        alliance_armies_in_sector = self.get_team_armies_in_sector(dest, team_id)
        if alliance_armies_in_sector >= team_armies_allowed[team_id]:
            raise ValueError(f"Move not allowed due to supply restrictions.")
        # Next we check whether there are anyone coming the other way on the path that is not in the alliance
        edge_rev = self.calculate_edge(path, reverse=True)
        edges = self.edges
        m = edges == edge_rev
        if np.sum(m) > 0:
            owners = set(self.army_team_id[m])
            allowed_owner_ids = set(self.army_team_id[[id]]).union(self.army_allies[[id]]).union(self.army_truce[[id]])
            forbidden_ids = owners.difference(allowed_owner_ids)
            if len(forbidden_ids) > 0:
                raise ValueError(f"Move not allowed due to hostile army moving in opposite direction.")
        return True

    def move_army(self, name, path_name):
        """
        Moves an army along a path
        Note that this function is very old and ugly and should be rewritten.
        The reason why this is so ugly is that it allows the path to be given in many different ways.
        """
        try:
            name = self.names[int(name)]
        except:
            pass

        if isinstance(path_name, str):
            try:
                assert path_name.lower() in self.sectors.names
                path_name = [path_name.lower()]
            except:
                try:
                    results = literal_eval(path_name)
                    path_name_new = []
                    if isinstance(results, list):
                        for result in results:
                            if isinstance(result, int):
                                path_name_new.append(self.sectors.names[result])
                            else:
                                path_name_new.append(result)
                    else:
                        if isinstance(results, int):
                            path_name_new.append(self.sectors.names[results])
                        else:
                            path_name_new.append(results)
                    path_name = path_name_new
                except:
                    raise ValueError(f"sector arguments not understood {path_name}")
        else:
            if isinstance(path_name, int):
                path_name = [self.sectors.names[path_name]]
            else:
                path_name_corrected = []
                for p in path_name:
                    if isinstance(p, int):
                        p = self.sectors.names[p]
                    else:
                        p = p.lower()
                    path_name_corrected.append(p)
                path_name = path_name_corrected

        path_ids = [self.sectors.name_id(p) for p in path_name]
        army_id = self.name_id(name.lower())
        assert ~self.fighting[army_id], f"currently fighting."

        for i, path_id in enumerate(path_ids):
            if i == 0:
                if self.moving[army_id]:
                    assert path_id == self.paths[army_id][1] or path_id == self.paths[army_id][
                        0], f"currently travelling between {self.paths_name[army_id][0]} and {self.paths_name[army_id][1]}. First sector in path should be either of those, but was {path_name[0]}."
                else:
                    assert path_id in self.sectors.G.neighbors(self.sources[
                                                                   army_id]), f"{path_name[i]} is not a neighbouring sector to {self.paths_name[army_id][0]}."
            else:
                assert path_id in self.sectors.G.neighbors(
                    path_ids[i - 1]), f"{path_name[i]} is not a neighbouring sector to {path_name[i - 1]}"

        # Finally we need to check that the edge isn't occupied by a hostile army moving in the other direction
        path_with_origin = [self.paths[army_id][0]] + path_ids
        move_allowed = self.check_legal_move(army_id, path_with_origin)
        if move_allowed:
            if self.moving[army_id] and path_ids[0] != self.paths[army_id][
                1]:  # We flip our current source and destination
                tmp = self.paths[army_id][0]
                self.paths[army_id][0] = self.paths[army_id][1]
                self.paths[army_id][1] = tmp
                self.progress[army_id] = 1 - self.progress[army_id]
            path_with_origin = [self.paths[army_id][0]] + path_ids
            self.paths[army_id] = path_with_origin
            self.moving[army_id] = True
        return

    def check_and_move_multiple_armies_in_same_sector(self,sector_id):
        """
        This function is used to move multiple armies all staying in the same sector. This is merely a visual effect such that all the armies are visible, but will not actually affect the armies in any other way.
        """
        m_armies_in_area = self.sources == sector_id
        if np.sum(m_armies_in_area) > 1:
            # make sure to reposition all armies in m_armies_in_area
            n = np.sum(m_armies_in_area)
            ii = np.arange(n)
            dxy = np.stack([np.cos(ii * 2 * np.pi / n), np.sin(ii * 2 * np.pi / n)], axis=1)
            self.positions[m_armies_in_area] += 0.2 * dxy


    def takeover_sector(self, army_id):
        """
        Army_id captures the sector they are currently in.

        """
        location_id = self.paths[army_id][0]
        army_owner = self.army_team_id[army_id]
        sector_owner = self.sectors.army_owner[location_id]
        m_armies_in_area = self.sources == location_id
        m_faction = self.army_team_id == self.army_team_id[army_id]
        m_allies = self.army_team_id == self.army_allies[army_id]
        m_hostiles = ~ (m_faction + m_allies)
        m_hostiles_in_area = m_hostiles * m_armies_in_area
        if sector_owner == army_owner or sector_owner == self.army_allies[army_id]:  # is the sector owned by a hostile?
            raise RequirementsNotMetError("Sector is already owned by team or allies.")
        elif sector_owner == self.team_truce[army_owner]:
            raise RequirementsNotMetError("Sector is owned by former ally, who you have truce with")
        elif self.sectors.being_captured[location_id]:
            raise RequirementsNotMetError("Sector is currently getting captured.")
        elif np.sum(m_hostiles_in_area):  # There are other armies in the area
            raise RequirementsNotMetError("Hostiles in sector.")
        elif self.moving[army_id]:
            raise RequirementsNotMetError("The army cannot currently be moving when attempting to capture a sector")
        else:
            self.capturing[army_id] = True
            self.sectors.being_captured[location_id] = True
        return

    def time_step(self, dt):
        """
        Advances all armies by dt
        """
        for i in range(self.n_teams):
            if self.truce_timer[i] > 0:
                self.truce_timer[i] -= dt
                if self.truce_timer[i] <= 0:
                    self.team_truce[i] = -1
        for i in range(len(self)):
            if self.moving[i]:  # Is the army moving?
                dest = self.paths[i][1]
                dest_owner = self.sectors.army_owner[dest]
                if dest_owner == self.army_team_id[i] or dest_owner == self.army_allies[i]:
                    speed = self.speed(i)
                else:
                    speed = self.speed(i) * 0.75  # lower speed due to moving into hostile sector
                self.progress[i] += dt * speed / self.distances[i]
                if self.progress[i] >= 1:
                    self.progress[i] = 0
                    self.paths[i].pop(0)
                    loc = self.paths[i][0]
                    logger.info(f"{self.names[i]} has arrived at {self.paths_name[i][0]}")
                    # Check for battle
                    m_armies_in_area = self.sources == loc
                    m_armies_in_area[i] = True # Add the army itself, (it is not auto added since it is still moving)
                    m_hostiles = self.get_hostiles(i)
                    m_battle = m_armies_in_area * m_hostiles
                    battle_in_area = np.sum(m_battle)
                    if battle_in_area:
                        if self.sectors.battle[loc]:
                            logger.info(f'{self.names[i]} has joined the battle in {self.paths_name[i][0]}')
                        else:
                            logger.info(f"A battle has started in {self.paths_name[i][0]}")
                            self.sectors.battle[loc] = True
                            self.fighting[i] = True
                            self.fighting[m_battle] = True
                            self.rearming[m_battle] = False
                            self.progress[m_battle] = 0
                            self.capturing[m_battle] = False
                            self.sectors.being_captured[loc] = False
                    if len(self.paths[i]) > 1:
                        legal_move = self.check_legal_move(i, self.paths[i])
                        if not legal_move:
                            self.paths[i] = [self.paths[i][0]]
                            self.moving[i] = False
                    else:
                        self.moving[i] = False
                    self.check_and_move_multiple_armies_in_same_sector(loc)

            elif self.respawning[i]:
                self.progress[i] += dt * self.speed(i) / self.respawn_len
                if self.progress[i] >= 1:
                    self.progress[i] = 0
                    self.respawning[i] = False
                    self.dead[i] = False
                    self.paths[i].pop(0)
                    loc = self.paths[i][0]
                    logger.info(f"{self.names[i]} has respawned in {self.paths_name[i][0]}")
                    self.positions[i] = self.sectors.pos[loc]
                    self.check_and_move_multiple_armies_in_same_sector(loc)


            elif self.capturing[i]:  # Continue capturing
                loc = self.paths[i][0]
                self.progress[i] += dt * self.speed(i) / self.sectors.battle_points[loc]
                if self.progress[i] >= 1:
                    self.progress[i] = 0
                    self.sectors.army_owner[loc] = self.army_team_id[i]
                    self.sectors.being_captured[loc] = False
                    self.capturing[i] = False
                    logger.info(f"{self.names[i]} has captured {self.paths_name[i][0]}")
                    # We check whether any army in the sector or neighbouring sectors are under-supplied because of this
                    loc_nn = list(self.sectors.G.neighbors(loc))
                    for l in [loc] + loc_nn:
                        team_max_armies = self.get_max_allowed_armies_in_sector(l)
                        for team_id in range(self.n_teams):
                            alliance_armies_in_sector = self.get_team_armies_in_sector(l, team_id)
                            if alliance_armies_in_sector > team_max_armies[team_id]:
                                logger.info(
                                    f"Armies undersupplied. Team: {self.team_names[team_id]} or its allies looses troops.")

            elif self.rearming[i]:
                self.battle_points[i] += dt * self.speed(i)
                if self.battle_points[i] >= self._rearm_target[i]:
                    self.battle_points[i] = self._rearm_target[i]
                    self.rearming[i] = False

            elif self.idle[i]:
                # Do we have any commands in the queue to execute?
                if self._command_queue[i]:
                    command_fn, args = self._command_queue[i].pop(0)
                    logger.debug(f"Army {self.names[i]} is executing queued command: {command_fn}, {args}")
                    try:
                        command_fn(*args)
                    except Exception as e:
                        logger.debug(f"Queued action failed. {e}")
            if self._speed_multiplier_timeleft[i] > 0:
                self._speed_multiplier_timeleft[i] -= dt
                if self._speed_multiplier_timeleft[i] <= 0:
                    self._speed_multiplier[i] = 1

    def draw_initial(self):
        """
        Draws the armies the first time.
        """
        for i in range(len(self)):
            if len(self.paths[i]) > 1 and self.visible[i]:
                s = self.paths[i][0]
                d = self.paths[i][1]
                pos_source = self.sectors.pos[s]
                pos_dest = self.sectors.pos[d]
                self.positions[i] = (pos_dest - pos_source) * self.progress[i] + pos_source
        pos = self.pos
        army_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        for army_id, xy in enumerate(self.positions):
            # self._army_boxes.append(dict(boxstyle="circle", fc="gray", ec=self.color_ids[army_id], lw=2, alpha=0.5))
            # self._army_texts.append(
            #     plt.text(*xy, str(army_id), ha="center", va="center", size=self.army_size, bbox=self._army_boxes[-1]))
            draw_text(army_surface,str(army_id),self.font,False,self.color_ids[army_id]+(125,),x=xy[0],y=xy[1])
        self.screen.blit(army_surface, (0,0))

        # pygame.display.flip()

    def draw(self):
        """
        Updates the drawing of all armies.
        """
        for i in range(len(self)):
            if len(self.paths[i]) > 1 and self.visible[i]:
                s = self.paths[i][0]
                d = self.paths[i][1]
                pos_source = self.sectors.pos[s]
                pos_dest = self.sectors.pos[d]
                self.positions[i] = (pos_dest - pos_source) * self.progress[i] + pos_source
        pos = self.pos
        army_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        for army_id, xy in enumerate(self.positions):
            if self.visible[army_id]:
                xy_pxl = self.coordinate_converter.convert_coords_to_pxl(xy[None,:])

                # draw_text(army_surface, str(army_id), self.font, False, self.color_ids[army_id] + (125,), x=xy[0], y=xy[1])
                draw_text(army_surface, str(army_id), self.font, False, (0,0,0,125), bg=(255,255,255,125), x=xy_pxl[0,0], y=xy_pxl[0,1])
        self.screen.blit(army_surface, (0, 0))
