"""

This file provides a dictionary with the different users that the game server will recognize.

each user is a new entry in the dictionary.

access levels go from 0 to 3
    0 - is admin, and should have all commands available to them, including starting, pausing the game.
    1 - is team level account, and might not be implemented, but the idea is that this could be one account to control the entire teams armies
    2 - is a team captain, this account has access to control 1 single army, but also have some additional commands available, like the ability to form alliances, and swap armies
    3 - is a standard user account, this is the account most people should have, and it will give access to controlling a single army.


For instance:
auth_dict = {'dummy_username': ("123", 3, 2, 3)}
is an authetication dictionary with only one user in it.
    the username is 'dummy_username'
    the password is '123'
    the user has access level 3
    the user belongs to team 2
    the user is in control of army 3

Another example is:
auth_dict = {'god': ("hemmeligt", 0, -1, -1)}
the user god has access level 0 (admin), he does not belong to any team and does not control any particular army. (but can control all of them)

"""

auth_dict = {'admin': ("hemmeligt", 0, -1, -1),
             'team': ("gandalfisgreat", 1, 0, -1),
             'captain': ("password", 2, 1, 1),
             'private': ("123", 3, 2, 3)
             }
