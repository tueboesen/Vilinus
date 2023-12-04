import numpy as np
import matplotlib.pyplot as plt

zones = [('Europe', 0, 1.0, (7.5,6),[(6,5),(9,5),(9,8),(6.7,8.5)]),
           ('Africa', 0, 1.0, (5.5,4),[]),
           ("Australia", 1, 1.0, (8.1,2.8),[]),
           ("S_America", 2, 1.0,(3,3),[]),
           ("N_America", 2, 1.0, (2,6),[]),
           ("North", 3, 1.0, (4,8),[])
]

roads = [('Europe', 'Africa',15,(5.7,4.8)),
('Europe', 'Australia',25,(7.8,3.8)),
('Europe', 'North',35,(4.2,7)),
('Africa', 'Australia',45,(6.7,3)),
('Africa', 'S_America',35,(4.2,3.6)),
('S_America', 'N_America',5,(2.8,4.2)),
('N_America', 'North',10,(2.8,7.0)),
         ]

teams = [['Good', [('Gandalf', 'Europe', 1.0)]]]
teams += [['Evil', [('Grond', 'North', 1.0)]]]
teams += [['Others']]
teams += [["Neutral"]]


if __name__ == '__main__':
    image_name = 'world.jpg'

    img = plt.imread(image_name)

    xs = []
    ys = []

    for _, (x,y),polygon in zones:
        xs.append(x)
        ys.append(y)
        xps = []
        yps = []
        if polygon:
            for xp,yp in polygon:
                xps.append(xp)
                yps.append(yp)
            xps = np.asarray(xps)
            yps = np.asarray(yps)
            plt.fill(xps, yps, 'r', alpha=0.3)

    xs = np.asarray(xs)
    ys = np.asarray(ys)

    plt.scatter(xs,ys,zorder=1)

    x_roads = []
    y_roads = []
    for z1,z2,dist,(x,y) in roads:
        x_roads.append(x)
        y_roads.append(y)
    x_roads = np.asarray(x_roads)
    y_roads = np.asarray(y_roads)

    plt.scatter(x_roads,y_roads,zorder=2,c='r')


    plt.imshow(img, zorder=0, extent=[0.0, 10.0, 0.0, 10.0])
    plt.grid(True)
    plt.show()


