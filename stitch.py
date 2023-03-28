#!/usr/bin/env python3

# Standard Library Imports
import argparse
from collections import namedtuple
from math import ceil, sqrt
import os
from pathlib import Path
import sys
from typing import List

Rectangle = namedtuple("Rectange", ["height", "width"])

# 3rd Party Imports
import wand
from wand.image import Image


# Constant For Command & Conque -- Tiberian Dawn
_tile = Rectangle(height=128, width=128)

background_color = wand.color.Color("black")

_verbosity = 0

# =============================================================================================================
def _gather_tiles(input_path: str, ext: str) -> List[str]:
    if not os.path.exists(input_path):
        return []

    found = []
    for file in os.listdir(input_path):
        if file.endswith(ext):
            if not file.endswith(f".stitched{ext}"):
                found.append(os.path.join(input_path, file))

    return found


def _stitch_tiles(inputs, output_path):
    tile_count_x = ceil(sqrt(len(inputs)))
    tile_count_y = ceil(len(inputs) / tile_count_x)
    print(f"    ::Canvas:size: {tile_count_x}x{tile_count_y}")

    # just double-check my math :P
    assert len(inputs) <= (tile_count_x * tile_count_y)

    canvas_width = tile_count_x * _tile.width
    canvas_height = tile_count_y * _tile.height

    each_path = iter(inputs)
    with Image(width=canvas_width, height=canvas_height, background=background_color) as canvas:
        canvas.alpha_channel = True
        print(f"    ::Canvas:size: {canvas.size}")
        try:
            for row in range(tile_count_y):
                for col in range(tile_count_x):
                    pixels_from_top = row * _tile.height
                    pixels_from_left = col * _tile.width
                    curpath = next(each_path)
                    print(f"        [{col},{row}]: @({pixels_from_top},{pixels_from_left}): {curpath}")
                    with Image(filename=curpath) as each_tile:
                        canvas.composite(each_tile, top=pixels_from_top, left=pixels_from_left)

                # print(f"    << Finished Row: {row}")

            # print(f"::Finished Compositing Tiles.")
        except StopIteration:
            # just done with files, before filling the sheet. that's fine.
            pass

        # not (yet) necessary ?
        # canvas.transparent_color(wand.color.Color('#FFF'))

        canvas.save(filename=output_path)

    return


if "__main__" == __name__:
    parser = argparse.ArgumentParser(
        prog="extractor", description="extract certain files from game archive"
    )
    parser.add_argument("-i", "--input-dir")
    parser.add_argument("-o", "--output-dir")
    parser.add_argument("-x", "--tile-height")
    parser.add_argument("-y", "--tile-width")
    # parser.add_argument("-x", "--canvas-height")
    # parser.add_argument("-y", "--canvas-width")

    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    # =============================================
    # default values
    input_dir = Path("data/desert/object/village/")

    if args.input_dir:
        input_dir = args.input_dir

    output_dir = input_dir
    if args.output_dir:
        output_dir = args.output_dir
    output_name = os.path.basename(output_dir)
    output_path = Path(output_dir, f"{output_name}.stitched.png")

    # if args.tile_height and args.tile_width:
    #     _tile = Rectangle( width=int(args.tile_width), height=int(args.tile_height))

    _verbosity = args.verbose
    if 0 < _verbosity:
        print(f"==> Gathering Input")

    input_paths = _gather_tiles(input_dir, ".png")

    if input_paths:
        if 0 < _verbosity:
            print(f"==> Stiching tiles ...")
        _stitch_tiles(input_paths, output_path)
