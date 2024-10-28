import numpy as np


class InsufficientAccessError(Exception):
    pass

class RequirementsNotMetError(Exception):
    pass

class CoordinateConverter:
    def __init__(self, coord_x_min=0, coord_x_max=10, coord_y_min=0, coord_y_max=10, pixel_width=800, pixel_height=600):
        self.coord_x_range = coord_x_max - coord_x_min
        self.coord_y_range = coord_y_max - coord_y_min
        self.pxl_x_range = pixel_width
        self.pxl_y_range = pixel_height

    def convert_coords_to_pxl(self, coords):
        """
        Coordinates have their minimum value in the lower left corner, whereas pixels have their minimum value in the upper left corner.

        Takes a set of coordinates and converts them to pixel values.
        coords should have shape (n,2) where n is the number of coordinates.

        """
        x = np.round(coords[:,0] * self.pxl_x_range / self.coord_x_range)
        y = np.round((self.coord_y_range - coords[:,1]) * self.pxl_y_range / self.coord_y_range)
        output_coords = np.array([x,y]).T
        return output_coords

    def convert_pxl_to_coords(self, pxl):
        x = pxl[:,0] * self.coord_x_range / self.pxl_x_range
        y = self.coord_y_range - pxl[:,1] * self.coord_y_range / self.pxl_y_range
        output_coords = np.array([x, y]).T
        return output_coords


