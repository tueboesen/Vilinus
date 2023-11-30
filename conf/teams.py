"""
Here we have different teams

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
