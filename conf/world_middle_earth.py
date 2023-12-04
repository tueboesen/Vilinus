"""
Here we define the world the game takes place in.

zones are defined in a list, where each element is a tuple designating a zone. A zone tuple contains:
('name of zone', team_id, value, (x_coord of capital, y_coord of capita), [boundary polygon of zone])

The boundary polygon gives the edges of the polygon of the zone and should be a list of (x,y) coordinates.


roads connect different zones and are specified as a list of tuples ('zone1','zone2',length_of_road,(x_loc of road, y_loc of road))
roads are unidirectional, meaning that travel is possible in both directions.

"""

zones = [('Death', 3, 0.0, (), []),
         ('Mordor', 0, 1.0, (), []),
         ('Gondor', 1, 1.0,(),[]),
         ('Shire', 0, 1.0,(),[]),
         ('Rohan', 1, 1.0, (), []),
         ('Rivendell', 2, 1.0, (), []),
         ('Tirith', 2, 1.0, (),[]),
        ]

roads = [('Mordor', 'Gondor', 0.6,()),
                ('Shire', 'Rohan', 0.2,()),
                ('Gondor', 'Tirith', 0.1,()),
                ('Rohan', 'Shire', 0.7,()),
                ('Rivendell', 'Shire', 0.9,()),
                ('Gondor', 'Rohan', 0.3,()), ]

"""
Each team is added as a list to a list

teams += [['Others', [('Hobbits', 'Shire', 1.0)]]]
means that the team with name "Others" is added to the game,
this faction has 1 army called Hobbits, which is located in the shire, and has an army value of 1.0 (army value currently does not do anything)

teams += [['Evil', [('Grond', 'Mordor', 1.0), ('Orcs', 'Tirith', 1.0)]]]
The Evil faction on the other hand has two armies: Grond starts in Mordor, while Orcs starts in Tirith

teams += [["Neutral"]]
Finally the neural faction does not have any armies, but they are still included and can control various sectors in the game.
"""

teams = [['Good', [('Gandalf', 'Rivendell', 1.0)]]]
teams += [['Evil', [('Grond', 'Mordor', 1.0), ('Orcs', 'Tirith', 1.0)]]]
teams += [['Others', [('Hobbits', 'Shire', 1.0)]]]
teams += [["Neutral"]]
