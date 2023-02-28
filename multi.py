import json
import os
import time
from typing import List


from rpi_ws281x import PixelStrip

import redis


from constants import (
    LED_FREQ_HZ,
    LED_DMA,
    LED_INVERT,
    LED_BRIGHTNESS,
)
from custom_types import PixelToLight
from utils import (
    light_n_pixels,
    rainbow,
    turn_strip_off,
    get_strip_and_index,
    group_pixels_to_light_by_pin,
    read_strip_config_from_env,
)

fucked_up_pin_mapping = {13: 18, 18: 13}


def main():

    #######
    # SETUP
    #######

    # load strips from env
    strip_configs = read_strip_config_from_env()

    # strip_1: StripConfig = {
    #     "offset": 1.65,
    #     "length": 1,
    #     "leds_per_m": 30,
    #     "gpio_pin": 13,
    # }
    # strip_2: StripConfig = {
    #     "offset": 0.5,
    #     "length": 1,
    #     "leds_per_m": 30,
    #     "gpio_pin": 18,
    # }
    # strip_configs = [strip_1, strip_2]

    strip_instances = {}

    # strip_1 = PixelStrip(
    #     30,
    #     13,
    #     LED_FREQ_HZ,
    #     LED_DMA,
    #     LED_INVERT,
    #     LED_BRIGHTNESS,
    #     1,
    # )
    # strip_1.begin()
    # turn_strip_off(strip_1)

    # strip_2 = PixelStrip(
    #     30,
    #     18,
    #     LED_FREQ_HZ,
    #     LED_DMA,
    #     LED_INVERT,
    #     LED_BRIGHTNESS,
    #     0,
    # )

    # strip_2.begin()
    # turn_strip_off(strip_2)

    # strip_instances[13] = strip_1
    # strip_instances[18] = strip_2

    for strip_config in strip_configs:
        total_leds = strip_config["leds_per_m"] * strip_config["length"]
        pin = strip_config["gpio_pin"]
        channel = 0 if pin in [18, 12] else 1
        strip_instance = PixelStrip(
            total_leds,
            pin,
            LED_FREQ_HZ,
            LED_DMA,
            LED_INVERT,
            LED_BRIGHTNESS,
            channel,
        )
        strip_instance.begin()
        turn_strip_off(strip_instance)
        strip_instances[pin] = strip_instance

    ###########
    # MAIN LOOP
    ###########
    dist = 3
    while dist > -0.5:
        # read state from redis
        state = {
            "distanceToNextTree": dist,
            "distanceFromPrevTree": dist,
            "nextSpecies": {"color": "#ff0000"},
            "prevSpecies": {"color": "#00ff00"},
        }
        if state.get("ledDiagnosticsMode") == True:
            for strip_instance in strip_instances.keys():
                inst = strip_instances[strip_instance]
                rainbow(inst, iterations=1)
            time.sleep(5)
            for strip_instance in strip_instances.keys():
                inst = strip_instances[strip_instance]
                turn_strip_off(inst)
        else:
            for strip_instance in strip_instances.keys():
                inst = strip_instances[strip_instance]
                turn_strip_off(inst)

            try:
                pixels_to_light: List[PixelToLight] = []

                ##############
                # NEXT SPECIES
                ##############
                distance_to_next = state.get("distanceToNextTree", None)
                next_color = state.get("nextSpecies", {}).get("color")
                if distance_to_next is not None and next_color:

                    strip_config, led_index = get_strip_and_index(
                        strip_configs, distance_to_next
                    )
                    if strip_config and led_index is not None:

                        desired_pin = strip_config["gpio_pin"]
                        desired_pin = fucked_up_pin_mapping[desired_pin]
                        pixels_to_light.append(
                            {
                                "pin": desired_pin,
                                "pixel_index": led_index,
                                "color": next_color,
                            }
                        )

                ##############
                # PREV SPECIES
                ##############
                distance_from_prev = state.get("distanceFromPrevTree", None)
                prev_color = state.get("prevSpecies", {}).get("color")

                if distance_from_prev is not None and prev_color:

                    strip_config, led_index = get_strip_and_index(
                        strip_configs, distance_from_prev * -1
                    )

                    if strip_config and led_index is not None:

                        desired_pin = strip_config["gpio_pin"]
                        desired_pin = fucked_up_pin_mapping[desired_pin]
                        pixels_to_light.append(
                            {
                                "pin": desired_pin,
                                "pixel_index": led_index,
                                "color": prev_color,
                            }
                        )

                # group by pin
                grouped_by_pin = group_pixels_to_light_by_pin(pixels_to_light)

                for pin in grouped_by_pin.keys():
                    strip_instance = strip_instances[pin]
                    pixels_to_light = grouped_by_pin[pin]
                    light_n_pixels(strip_instance, pixels_to_light)

            except Exception as e:
                print(e)

        time.sleep(0.5)
        dist = dist - 0.1


if __name__ == "__main__":
    main()
