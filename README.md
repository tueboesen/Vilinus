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

	

# Dev log

## Autosave
We need to make some kind of autosave feature, so that the game state is saved every n seconds. This is to prevent the game from being lost if the server crashes.
Before it was just pickling down the game state, but this does not work with pygame, so we should just pickle down the things that needs to be saved and then recreate the game state when loading the game.
Also we should add rotations to the autosave feature such that it does not directly overwrite the last autosave file, but instead rotates between a few files. This is to prevent the autosave from being corrupted if the server crashes while saving.

## Things are not very pretty and the code could use another refactoring.
After I switched to pygame quite a few things are not as pretty as they could be.
- The ui logic should be separated from the game logic
- The coordinate to pixel converter should be loaded only once and not for both army and sector, and it should also work for just a single coordinate pair
- The world should perhaps have roads or other items on it as well?
- We should probably move more things to settings files, and also use argparser for the server and client.