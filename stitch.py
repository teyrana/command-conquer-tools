#!/usr/bin/env python3

# Standard Library Imports
import argparse
from pathlib import Path
import sys

# 3rd Party Imports
import wand
from wand.image import Image


_stage_path = Path("data/stage/")

_output_path = Path("output/terrain/desert")

_write_path = Path("output/terrain/desert")

# load some test paths:
test_paths = [
    "/mnt/d/project/cnctd/data/stage/B6.DES-0000.png",
    "/mnt/d/project/cnctd/data/stage/B1.DES-0000.png",
    "/mnt/d/project/cnctd/data/stage/B2.DES-0000.png",
    "/mnt/d/project/cnctd/data/stage/B2.DES-0001.png",
    "/mnt/d/project/cnctd/data/stage/B4.DES-0000.png",
    "/mnt/d/project/cnctd/data/stage/B5.DES-0000.png",
]


# Constant For Command & Conque -- Tiberian Dawn
_tile_height = 128
_tile_width = 128

# ================
# DEBUG values:
tilesheet_height = 2 * _tile_height
tilesheet_width = 3 * _tile_height
# DEBUG

tilesheet = Image(width=tilesheet_width, height=tilesheet_height)

# ================
each_path = iter(test_paths)
pixels_from_top = 0
pixels_from_left = 0
for row in range(2):
    pixels_from_left = 0
    for col in range(3):
        curpath = next(each_path)
        print(
            f"        [{col},{row}]: @({pixels_from_top},{pixels_from_left}): {curpath}"
        )
        curimg = Image(filename=curpath)
        tilesheet.composite(curimg, top=pixels_from_top, left=pixels_from_left)

        pixels_from_left += _tile_width

    print(f"    << Finished Row: {row}")
    pixels_from_top += _tile_height

print(f"::Finished Compositing Tiles.")

tilesheet.save(filename="test.composite.exact.png")


if "__main__" == __name__:
    parser = argparse.ArgumentParser(
        prog="extractor", description="extract certain files from game archive"
    )
    parser.add_argument("-b", "--base-path")
    parser.add_argument("-s", "--search-path")
    parser.add_argument("-o", "--output-path")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    if args.base_path:
        base_path = args.base_path
    else:
        base_path = Path(_base_path)

    if args.search_path:
        search_path = args.search_path
    else:
        search_path = base_path.joinpath("TERRAIN", "DESERT")

    if args.output_path:
        _output_path = args.output_path
    else:
        _output_path = Path("data/stage/")

    verbose = args.verbose
    if 0 < verbose:
        print(f"Starting at: {search_path}")

    apply(search_path, filter=_dds_filter, action=action_dds_to_png, verbose=verbose)
