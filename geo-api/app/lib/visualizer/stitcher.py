# type: ignore
import io
import math
import os

import requests
from PIL import Image

from .geo_types import Coords, Size


class ImageTile:
    def __init__(self):
        self.row = 0
        self.column = 0
        self.width = 0
        self.height = 0
        self.next = None


MAPBOX_WIDTH_LIMIT = 1280
MAPBOX_HEIGHT_LIMIT = 1280
ORIGIN_SHIFT = 2 * math.pi * 6378137 / 2.0
TILE_SIZE = 256


def stitch_mapbox_images(full_image, width, height, center, zoom, map_id):
    current = create_tile_list(width, height)
    merc_center = coords_to_meters(center)
    mpp = meters_per_pixel(center.lat, zoom)

    # top left corner of the full image, in meters
    tlcx = merc_center.lng - mpp * (width * 0.51)
    tlcy = merc_center.lat + mpp * (height * 0.51)

    offset_x = 0
    offset_y = 0
    offset_x_meters = 0
    offset_y_meters = 0

    while current is not None:
        offset_x_meters = mpp * (offset_x * 1.02)
        offset_y_meters = mpp * (offset_y * 1.02)
        x = tlcx + offset_x_meters + mpp * (current.width * 0.51)
        y = tlcy - offset_y_meters - mpp * (current.height * 0.51)

        is_last_image_tile = current.next is None
        latlng = meters_to_coords(x, y)
        img = fetch_mapbox_image(
            latlng,
            zoom,
            Size(current.width, current.height),
            map_id,
            is_last_image_tile,
        )
        full_image.paste(
            img,
            (offset_x, offset_y, offset_x + current.width, offset_y + current.height),
        )

        offset_x += current.width

        if current.next is not None and current.next.row != current.row:
            offset_x = 0
            offset_y += current.height

        current = current.next


def meters_per_pixel(lat, zoom):
    return (
        math.cos(lat * math.pi / 180.0)
        * 2
        * math.pi
        * 6378137
        / (TILE_SIZE * math.pow(2, zoom))
    )


def create_tile_list(image_width, image_height):
    columns = int(image_width / MAPBOX_WIDTH_LIMIT)

    if image_width % MAPBOX_WIDTH_LIMIT > 0:
        columns += 1

    rows = int(image_height / MAPBOX_HEIGHT_LIMIT)

    if image_height % MAPBOX_HEIGHT_LIMIT > 0:
        rows += 1

    head = ImageTile()
    current = head

    for i in range(rows):
        for j in range(columns):
            current.row = i
            current.height = get_row_height(image_height, i, rows)
            current.column = j
            current.width = get_column_width(image_width, j, columns)

            if i < (rows - 1) or j < (columns - 1):
                tile = ImageTile()
                current.next = tile
                current = tile

    return head


def get_row_height(image_height, row, n_rows):
    return get_column_width(image_height, row, n_rows)


def get_column_width(image_width, column, n_columns):
    if image_width <= MAPBOX_WIDTH_LIMIT:
        return image_width

    if column < (n_columns - 1):
        return MAPBOX_WIDTH_LIMIT

    remainder = image_width % MAPBOX_WIDTH_LIMIT
    return remainder if remainder > 0 else MAPBOX_WIDTH_LIMIT


def coords_to_meters(coords):
    lng = coords.lng * ORIGIN_SHIFT / 180.0
    lat = math.log(math.tan((90 + coords.lat) * math.pi / 360.0)) / (math.pi / 180.0)
    lat *= ORIGIN_SHIFT / 180.0

    return Coords(lng, lat)


def meters_to_coords(lng, lat):
    lng = lng / ORIGIN_SHIFT * 180.0
    lat = lat / ORIGIN_SHIFT * 180.0
    lat = (
        180.0
        / math.pi
        * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    )

    return Coords(lng, lat)


def fetch_mapbox_image(center, zoom, size, map_id, include_attribution):
    token = os.environ["MAPBOX_TOKEN"]

    url = (
        f"https://api.mapbox.com/styles/v1/mapbox/{map_id}/static"
        f"/{center.lng},{center.lat},{zoom}/{size.width}x{size.height}"
        f"?logo=false&attribution={str(include_attribution).lower()}"
        f"&access_token={token}"
    )

    response = requests.get(url)
    bytesio = io.BytesIO(response.content)
    img = Image.open(bytesio)
    return img
