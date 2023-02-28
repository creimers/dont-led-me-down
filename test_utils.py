from custom_types import PixelToLight
from utils import get_strip_and_index, group_pixels_to_light_by_pin, assemble_strip_config


def test_get_strip_and_index_none():
    """
    too far away to light anything
    """
    strip_1 = {
        "offset": 2.2,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 18,
        "reverse": False,
    }
    strip_2 = {
        "offset": 1,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 13,
        "reverse": False,
    }
    strips = [strip_1, strip_2]

    dist = 3

    strip, index = get_strip_and_index(strips, dist)
    assert strip is None
    assert index is None


def test_get_strip_and_index_strip_1():
    """
    light strip further away
    """
    strip_1 = {
        "offset": 2.2,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 18,
        "reverse": False,
    }
    strip_2 = {
        "offset": 1,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 13,
        "reverse": False,
    }
    strips = [strip_1, strip_2]

    dist = 2

    strip, index = get_strip_and_index(strips, dist)
    assert strip["offset"] == strip_1["offset"]
    assert index is not None


def test_get_strip_and_index_strip_1_reverse():
    """
    light strip further away
    """
    strip_1 = {
        "offset": 2.2,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 18,
        "reverse": True,
    }
    strip_2 = {
        "offset": 1,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 13,
        "reverse": False,
    }
    strips = [strip_1, strip_2]

    dist = 2

    strip, index = get_strip_and_index(strips, dist)
    assert strip["offset"] == strip_1["offset"]
    expected_index = (
        strip_1["length"] * strip_1["leds_per_m"]
        - (strip_1["offset"] - dist) * strip_1["leds_per_m"]
    )
    assert index == round(expected_index)


def test_get_strip_and_index_strip_2():
    """
    light strip closer by
    """
    strip_1 = {
        "offset": 2.2,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 18,
        "reverse": False,
    }
    strip_2 = {
        "offset": 1,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 13,
        "reverse": False,
    }
    strips = [strip_1, strip_2]

    dist = 0.1

    strip, index = get_strip_and_index(strips, dist)
    assert strip["offset"] == strip_2["offset"]
    assert index is not None


def test_get_strip_and_index_gap():
    """
    don't light anything in strip gap
    """
    strip_1 = {
        "offset": 2.2,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 18,
        "reverse": False,
    }
    strip_2 = {
        "offset": 1,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 13,
        "reverse": False,
    }
    strips = [strip_1, strip_2]

    dist = 1.1

    strip, index = get_strip_and_index(strips, dist)
    assert strip is None
    assert index is None


def test_group_pixels_by_pin():
    """
    group pixels to be lit correctly by pin number
    """
    pixel_1: PixelToLight = {"pin": 1, "pixel_index": 3, "color": "#f00000"}
    pixel_2: PixelToLight = {"pin": 2, "pixel_index": 3, "color": "#ffffff"}
    pixel_3: PixelToLight = {"pin": 2, "pixel_index": 4, "color": "#000000"}

    grouped = group_pixels_to_light_by_pin([pixel_1, pixel_2, pixel_3])

    assert 1 in grouped.keys()
    assert 2 in grouped.keys()
    assert len(grouped[2]) == 2


def test_assemble_strip_config():
    """
    assemble strip config correctly
    """
    strip_1 = {
        "offset": 2.2,
        "length": 1,
        "leds_per_m": 30,
        "gpio_pin": 18,
        "reverse": False,
    }
    strip_2 = {
        "offset": 1,
        "length": 1,
        "ledsPerM": 60,
        "gpioPin": 13,
        "reverse": False,
    }
    strips = [strip_1, strip_2]

    strip_config = assemble_strip_config(strips)

    assert len(strip_config) == 2
    assert strip_config[0]["gpio_pin"] == strip_1["gpio_pin"]
    assert strip_config[0]["leds_per_m"] == strip_1["leds_per_m"]
    assert strip_config[1]["gpio_pin"] == strip_2["gpioPin"]
    assert strip_config[1]["leds_per_m"] == strip_2["ledsPerM"]