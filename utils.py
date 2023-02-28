import json
import os
import time
from typing import Any, List, Dict

from rpi_ws281x import Color
from constants import LEDS_PER_M
from custom_types import PixelToLight, StripConfig


def assemble_strip_config(strip_config_parsed: dict):
    strip_configs: List[StripConfig] = []
    for config in strip_config_parsed:
        transformed_config = {
            "length": config["length"],
            "offset": config["offset"],
            "reverse": config["reverse"],
        }

        if config.get("leds_per_m", None):
            transformed_config["leds_per_m"] = config["leds_per_m"]
        elif config.get("ledsPerM", None):
            transformed_config["leds_per_m"] = config["ledsPerM"]

        if config.get("gpio_pin", None):
            transformed_config["gpio_pin"] = config["gpio_pin"]
        elif config.get("gpioPin", None):
            transformed_config["gpio_pin"] = config["gpioPin"]

        strip_configs.append(transformed_config)
    return strip_configs


def read_strip_config_from_env() -> List[StripConfig]:
    """
    reads the strip config from the env

    do some transormation to make it backwards compatible in a case kind of way
    """
    strip_1 = {
        "offset": 1.65,
        "length": 1,
        "leds_per_m": 60,
        "gpio_pin": 18,
        "reverse": True,
    }
    strip_2 = {
        "offset": 0.5,
        "length": 1,
        "ledsPerM": 30,
        "gpioPin": 13,
        "reverse": False,
    }
    strip_config_raw = json.dumps([strip_1, strip_2])
    strip_config_parsed = json.loads(strip_config_raw)
    return assemble_strip_config(strip_config_parsed)


def turn_strip_off(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


def hex_to_rgb(hex_color_code: str) -> tuple[int, int, int]:
    """convert hex color code to rgb tuple"""
    hex_color_code = hex_color_code.lstrip("#")
    rgb = tuple(int(hex_color_code[i : i + 2], 16) for i in (0, 2, 4))
    red = rgb[0]
    green = rgb[1]
    blue = rgb[2]
    return red, blue, green


def group_pixels_to_light_by_pin(
    pixels_to_light: List[PixelToLight],
) -> Dict[int, PixelToLight]:
    """
    groups pixels to be lit by pin number
    """
    grouped_by_pin = {}

    for p in pixels_to_light:
        if p["pin"] not in grouped_by_pin.keys():
            grouped_by_pin[p["pin"]] = []
        grouped_by_pin[p["pin"]].append(p)
    return grouped_by_pin


def get_strip_and_index(strips: List[StripConfig], dist: float):
    """
    get the strip and led index to be lit
    """
    relevant_strip_config = None
    led_index = None
    if strips:
        sorted_strips = sorted(strips, key=lambda x: x["offset"], reverse=True)
        for strip in sorted_strips:
            the_offset = strip["offset"]
            if dist <= the_offset and dist > the_offset - strip["length"]:
                relevant_strip_config = strip
                highlight_at = the_offset - dist
                led_index = int(highlight_at * strip["leds_per_m"])
                if strip["reverse"]:
                    led_index = strip["leds_per_m"] * strip["length"] - led_index
                if led_index > strip["leds_per_m"] * strip["length"]:
                    led_index = None
    return relevant_strip_config, led_index


def get_pixel_index(calibration_points: list, distance: float):
    """
    get the index of the pixel to be highlighted
    """
    if calibration_points:
        relevant_point = None
        for point in calibration_points:
            if distance <= point["offset"]:
                relevant_point = point
        if relevant_point:
            highlight_at = relevant_point["offset"] - distance
            led_index = int(highlight_at * LEDS_PER_M) + int(relevant_point["ledIndex"])
            return led_index


def light_individual_pixel(strip, pixel_index: int, color):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.setPixelColor(pixel_index, color)
    strip.show()


def light_n_pixels(strip_instance, pixels: List[PixelToLight]):
    """
    lights n pixels of a given strip instance
    """
    # clear
    for i in range(strip_instance.numPixels()):
        strip_instance.setPixelColor(i, Color(0, 0, 0))
    # set pixels and colors
    for pixel in pixels:
        # https://github.com/rpi-ws281x/rpi-ws281x-python/issues/7
        red, blue, green = hex_to_rgb(pixel["color"])
        color = Color(green, red, blue)
        strip_instance.setPixelColor(pixel["pixel_index"], color)
    strip_instance.show()


def wheel(pos: int):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)
