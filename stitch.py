#!/usr/bin/env python3

from pathlib import Path
import wand
from wand.image import Image
import sys




_stage_path = Path("data/stage/")

_output_path = Path("output/terrain/desert")

_write_path = Path("output/terrain/desert")

# load some test paths:
test_paths = ["/mnt/d/project/cnctd/data/stage/B6.DES-0000.png","/mnt/d/project/cnctd/data/stage/B1.DES-0000.png","/mnt/d/project/cnctd/data/stage/B2.DES-0000.png","/mnt/d/project/cnctd/data/stage/B2.DES-0001.png","/mnt/d/project/cnctd/data/stage/B4.DES-0000.png","/mnt/d/project/cnctd/data/stage/B5.DES-0000.png"]


# ================
# DEBUG values:
tile_height = 128
tile_width = tile_height
tilesheet_height = 2*tile_height
tilesheet_width = 3*tile_height
# DEBUG

tilesheet = Image( width=tilesheet_width, height=tilesheet_height )

# ================
each_path = iter(test_paths)
pixels_from_top = 0
pixels_from_left = 0
for row in range(2):
    pixels_from_left = 0
    for col in range(3):
        curpath = next(each_path)
        print(f"        [{col},{row}]: @({pixels_from_top},{pixels_from_left}): {curpath}")
        curimg = Image(filename=curpath)
        tilesheet.composite(curimg, top=pixels_from_top, left=pixels_from_left)
                                
        pixels_from_left += tile_width

    print(f"    << Finished Row: {row}")
    pixels_from_top += tile_height

print(f"::Finished Compositing Tiles.")

tilesheet.save(filename='test.composite.exact.png')
