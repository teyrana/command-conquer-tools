#!/usr/bin/env python3

# Standard Library Imports
import argparse
from collections import namedtuple
from math import ceil, sqrt
import os
from pathlib import Path
import re
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
def _gather_tiles(input_path: str, pattern: str, ext: str) -> List[str]:
    if not os.path.exists(input_path):
        return []

    if pattern:
        pattern = re.compile(pattern)

    found = []
    for file in os.listdir(input_path):
        if file.endswith(ext):
            if pattern and not pattern.match(file):
                continue
            if file.endswith(f".stitched{ext}"):
                continue

            found.append(os.path.join(input_path, file))

    return found


def _stitch_tiles(inputs: List[str], **kwargs ) -> Image:
    tile_horizontal = kwargs.get("tile_horizontal", False)
    tile_vertical = kwargs.get("tile_vertical", False)

    if tile_horizontal:
        tile_count_x = len(inputs)
        tile_count_y = 1
    elif tile_vertical:
        tile_count_x = 1
        tile_count_y = len(inputs)
    else:
        tile_count_x = ceil(sqrt(len(inputs)))
        tile_count_y = ceil(len(inputs) / tile_count_x)
    # just double-check my math :P
    assert len(inputs) <= (tile_count_x * tile_count_y)

    print(f"    ::Canvas: {len(inputs)} tiles => size: {tile_count_x}x{tile_count_y}")

    pixels_from_top = 0
    pixels_from_left = 0

    # convert paths to images:
    images = [ Image(filename=each_path) for each_path in iter(inputs) ]
    for i,im in enumerate(images):
        images[i].filename = inputs[i]    
    print(f"    ::Converted {len(inputs)} paths to {len(images)} images.")

    tile_max_width = max([ im.width for im in images ])
    tile_max_height = max([ im.height for im in images ])

    if tile_horizontal:
        # sort the tiles max height:
        sorted_tiles = sorted(images, key=lambda x: x.height)
        canvas_width = tile_max_width * len(inputs)
        canvas_height = tile_max_height
    elif tile_vertical:
        # sort the tiles by max width:
        sorted_tiles = sorted(images, key=lambda x: x.width)
        canvas_width = tile_max_width
        canvas_height = tile_max_height * len(inputs)
    else:
        # sort the tiles max height:
        sorted_tiles = sorted(images, key=lambda x: x.height)
        canvas_width = tile_count_x * tile_max_width
        canvas_height = tile_count_y * tile_max_height

    print(f"    ::tiles(max): {sorted_tiles[-1].width}x{sorted_tiles[-1].height}")

    pixels_for_next_row = _tile.height
    # output image:
    canvas = Image(width=canvas_width, height=canvas_height)
    canvas.alpha_channel = True
    print(f"    ::Canvas:size: ({canvas.width}x{canvas.height})")
    try:
        for row in range(tile_count_y):
            pixels_for_next_row = sorted_tiles[-1].height
            for col in range(tile_count_x):
                this_tile = sorted_tiles.pop()
                print(f"        [{col:4d},{row:4d}]: @({pixels_from_top:4d},{pixels_from_left:4d}) += {this_tile.size} (::{this_tile.filename})")
                canvas.composite(this_tile, top=pixels_from_top, left=pixels_from_left)
                pixels_from_left += this_tile.width
                pixels_for_next_row = max(pixels_for_next_row, this_tile.height)

            # print(f"    << Finished Row: {row}")
            pixels_from_top += pixels_for_next_row
            pixels_from_left = 0    

        # print(f"::Finished Compositing Tiles.")
    except IndexError:
        # merely finished processing tiles from our list -- this is expected.
        pass

    # not (yet) necessary ?
    # canvas.transparent_color(wand.color.Color('#FFF'))

    return canvas

if "__main__" == __name__:
    parser = argparse.ArgumentParser(
        prog="extractor", description="extract certain files from game archive"
    )
    parser.add_argument("-i", "--input-dir", required=True)
    parser.add_argument("-p", "--pattern")
    parser.add_argument("-l", "--list", action="store_true")
    parser.add_argument("-H", "--horizontal-tile", action="store_true")
    parser.add_argument("-V", "--vertical-tile", action="store_true")
    parser.add_argument("-o", "--output-dir")
    parser.add_argument("-x", "--tile-height")
    parser.add_argument("-y", "--tile-width")
    parser.add_argument("-r", "--remove", action="store_true")
    # parser.add_argument("-x", "--canvas-height")
    # parser.add_argument("-y", "--canvas-width")

    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    # =============================================
    
    input_dir = args.input_dir if bool(args.input_dir) else None

    input_pattern = args.pattern if bool(args.pattern) else None

    if not os.path.exists(input_dir):
        print("Invalid input directory!! Exiting.")
        exit(-10)

    output_dir = None
    output_path = None
    if args.output_dir:
        output_dir = args.output_dir
        if "auto" == output_dir:
            output_basename = os.path.basename(input_dir.rstrip("/"))
            output_path = Path(input_dir, f"{output_basename}.stitched.png")
        elif output_dir.endswith(".png"):
            output_path = Path(output_dir)
        else:
            output_basename = os.path.basename(input_dir.rstrip("/"))
            output_path = Path(output_dir, f"{output_basename}.stitched.png")

    # if args.tile_height and args.tile_width:
    #     _tile = Rectangle( width=int(args.tile_width), height=int(args.tile_height))

    _verbosity = args.verbose
    
    # =============================================

    print(f"==> Gathering Input")
    input_paths = _gather_tiles(input_dir, input_pattern, ".png")
    if not input_paths:
        print("No input files found. Exiting.")
        exit(-4)

    if args.list:
        print(f"==> Found {len(input_paths)} files:")
        for index, each_path in enumerate(input_paths):
            print(f"    [{index:3d}]: {each_path}")


    canvas = None
    if input_paths:
        opts = {"tile_horizontal": args.horizontal_tile, 
                "tile_vertical": args.vertical_tile}
        print(f"==> Stitching tiles ...")
        canvas = _stitch_tiles(input_paths, **opts )

    if canvas and output_path:
        print(f"==> Writing Canvas to {output_path}:  ({canvas.size})")
        if canvas.size:
            canvas.save(filename=output_path)

    if args.remove:
        print(f"==> Removing input files ...")
        for each_path in input_paths:
            os.remove(each_path)