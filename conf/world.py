"""
Here we define the world the game takes place in.

zones are defined in a dictionary where the name of the zone is the key,
and to each key is attached a tuple which specifies the faction the sector belongs to, as well as the value of the sector

roads connect different zones and are specified as a list of tuples ('zone1','zone2',length_of_road)
roads are unidirectional, meaning that travel is possible in both directions.

"""

zones = {'Mordor': (0, 1.0),
           'Gondor': (1, 1.0),
           'Shire': (2, 1.0),
           'Rohan': (1, 1.0),
           'Rivendell': (3, 1.0),
           'Tirith': (3, 1.0),
           }

roads = [('Mordor', 'Gondor', 0.6),
                ('Shire', 'Rohan', 0.2),
                ('Gondor', 'Tirith', 0.1),
                ('Rohan', 'Shire', 0.7),
                ('Rivendell', 'Shire', 0.9),
                ('Gondor', 'Rohan', 0.3), ]
