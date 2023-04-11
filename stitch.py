#!/usr/bin/env python3

# Standard Library Imports
import argparse
from collections import namedtuple
from math import ceil, sqrt
import os
from pathlib import Path
import re
import sys
from typing import List

Rectangle = namedtuple("Rectange", ["height", "width"])

# 3rd Party Imports
import wand
from wand.image import Image


# Constant For Command & Conque -- Tiberian Dawn
_default_tile = Rectangle(height=128, width=128)

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
    tile_auto = kwargs.get("tile_auto", False)
    tile_explicit = kwargs.get("tile_explicit", "")
    tile_horizontal = kwargs.get("tile_horizontal", False)
    tile_vertical = kwargs.get("tile_vertical", False)

    if 1 < int(tile_horizontal) + int(tile_vertical) + int(tile_auto):
        raise ValueError("Only one of --horizontal, --vertical, or --auto may be specified.")

    tile_max_width = _default_tile.width
    tile_max_height = _default_tile.height
    indices = list(range(len(inputs)))
    
    if tile_auto:
        # extract the file-basename-index-suffix:
        offsets = set([ int(os.path.basename(s)[8:12]) for s in inputs ])

        tile_count_x = ceil(sqrt(max(offsets)))
        tile_count_y = ceil(tile_count / tile_count_x)
        tile_count = tile_count_x * tile_count_y
        print(f"    ::Calculated count size: {tile_count_x}x{tile_count_y} => {tile_count} ")

        indices = [ int(i) if i in offsets else None for i in range(max(offsets)+1) ]
        indices += [None] *(tile_count - len(indices))

    elif tile_explicit:
        print(f"    ::tiles: using explicit tiles (DEBUG):")
        rows = tile_explicit.split("/")
        indices = [ [int(i) if i.isnumeric() else None for i in (r.split(","))] for r in rows ]
        tile_count_x = len(indices[0])
        tile_count_y = len(rows)

        print(f"    ::reshaped ordering:...")
        for row in indices:
            sys.stderr.write(f"            ")
            for index in row:
                sys.stderr.write( f" {index},".ljust(6) )
            sys.stderr.write("\n")
        ## DEBUG

    elif tile_horizontal or tile_vertical:
        # convert paths to images:
        for each_path in iter(inputs):
            with Image(filename=each_path) as each_image:
                tile_max_width = max( tile_max_width, each_image.width )
                tile_max_height = max( tile_max_height, each_image.height )

        if tile_horizontal:
            tile_count_x = len(inputs)
            tile_count_y = 1
            # sort the tiles by max width:
            sorted_tiles = sorted(images, key=lambda x: x.width)
        elif tile_vertical:
            tile_count_x = 1
            tile_count_y = len(inputs)
            # # sort the tiles by max width:
            # sorted_tiles = sorted(images, key=lambda x: x.height)
    else:
        tile_count_x = ceil(sqrt(len(inputs)))
        tile_count_y = ceil(len(inputs) / tile_count_x)

    # just double-check my math :P
    assert len(inputs) <= (tile_count_x * tile_count_y)

    print(f"    ::Canvas: {len(inputs)} tiles => size: {tile_count_x}x{tile_count_y}")

    # tile_max_width = max([ im.width for im in images ])
    # tile_max_height = max([ im.height for im in images ])
    # print(f"    ::tiles(max): {tile_max_width}x{tile_max_height}")

    
    canvas_width = tile_count_x * tile_max_width
    canvas_height = tile_count_y * tile_max_height
    print(f"        => {canvas_width}x{canvas_height}")

    pixels_from_top = 0
    pixels_from_left = 0

    # output image:
    canvas = Image(width=canvas_width, height=canvas_height)
    canvas.alpha_channel = True
    print(f"    ::Canvas:size: ({canvas.width}x{canvas.height})")
    try:
        pixels_from_top = 0
        j=0
        for row in indices:
            pixels_from_left = 0
            i=0
            for each_index in row:
                if each_index is None:
                    continue

                each_path = inputs[each_index]
                # convert path to image:
                with Image(filename=each_path) as each_image:
                    print(f"        [{i:4d},{j:4d}]: @({pixels_from_left:4d},{pixels_from_top:4d}) += {each_image.size} (::{each_path})")
                    canvas.composite(each_image, top=pixels_from_top, left=pixels_from_left)
                pixels_from_left += tile_max_width
                i+=1
            # print(f"    << Finished Row: {row}")
            pixels_from_top += tile_max_height
            pixels_from_left = 0    
            j+=1
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
    parser.add_argument("-A", "--auto", action="store_true")
    parser.add_argument("-E", "--explicit")
    parser.add_argument("-i", "--input-dir", required=True)
    parser.add_argument("-p", "--pattern")
    parser.add_argument("-l", "--list", action="store_true")
    parser.add_argument("-H", "--horizontal", action="store_true")
    parser.add_argument("-V", "--vertical", action="store_true")
    parser.add_argument("-o", "--output-dir")
    parser.add_argument("-r", "--remove", action="store_true")


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
            output_basename = args.pattern.rstrip("*")[0:7]
            if len(output_basename) < 7:
                print("Invalid auto name!! Exiting.")
                exit(-1)
            else:
                print("=>> Choosing auto basename: {output_basename}")
                output_path = Path(input_dir, f"{output_basename}.png")
                print(f"    =>> {output_path}")
        elif output_dir.endswith(".png"):
            output_path = Path(output_dir)
        else:
            output_basename = os.path.basename(input_dir.rstrip("/"))
            output_path = Path(output_dir, f"{output_basename}.stitched.png")

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
        opts = {"tile_auto": args.auto,
                "tile_explicit": args.explicit,
                "tile_horizontal": args.horizontal, 
                "tile_vertical": args.vertical}
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