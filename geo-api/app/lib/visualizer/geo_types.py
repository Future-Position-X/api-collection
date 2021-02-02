# type: ignore
class Coords:
    def __init__(self, lng, lat):
        self.lng = lng
        self.lat = lat


class Bounds:
    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y


class Size:
    def __init__(self, width, height):
        self.width = width
        self.height = height
