# Vibinus
Narative warhammer campaign simulation software

## Quick start

### Starting the server
start_game_server.py starts a game server, which is required in order to join with clients.
when running start_game_server.py it will print out the ip address and port of the server, which are needed for the clients to connect.

Note that the server auto saves the game state to a checkpoint file in /data/ every n seconds (10 by default).
If you start a new server this checkpoint will be overwritten unless you specify a new file

The server will generate the game based on the files in \conf\
world.py provides the different sectors available in the world and the roads connecting them and their length
teams.py provides the different teams/factions in the game as well as the individual armies belonging to each team.
authentication.py provides the different login usernames/passwords and their access level. 

### Joining as a client (player)

Join using the start_game_client.py file

	
