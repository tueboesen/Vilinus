import numpy as np
import pygame


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

def draw_text(_window: pygame.Surface, text: str, font: pygame.font.Font, aa: bool, fg: str ,
              x: int | float, y: int | float, centered_x: bool=False, centered_y: bool=False, bg: str = None) -> None:
    """
    Function to draw text on window

    :param _window: window to draw text on (pygame.Surface)
    :param text: text to draw on window (str)
    :param font: font to render the text with (pygame.font.Font)
    :param aa: use antialiasing (bool)
    :param fg: foreground color (str)
    :param bg: background color (str)
    :param x: x coordinate of window to draw text on (int | float)
    :param y: y coordinate of window to draw text on (int | float)
    :param centered_x: center in the x-axis (bool)
    :param centered_y: center in the y-axis (bool)
    :return: None
    """

    text = font.render(text, aa, fg, bg)
    text_position = x, y

    if centered_x or centered_y:
        text_position = text.get_rect()
    if centered_x:
        text_position.y += y
        text_position.centerx = _window.get_rect().centerx
    if centered_y:
        text_position.x += x
        text_position.centery = _window.get_rect().centery

    _window.blit(text, text_position)
