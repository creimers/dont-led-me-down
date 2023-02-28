from typing import NamedTuple


class StripConfig(NamedTuple):
    offset: float
    length: float
    leds_per_m: int
    gpio_pin: int
    reverse: bool


class PixelToLight(NamedTuple):
    pin: int
    pixel_index: int
    color: str
