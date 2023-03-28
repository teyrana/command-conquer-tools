#!/usr/bin/env python3

import argparse
from pathlib import Path
import os
import re
from wand.image import Image
import sys
import zipfile

_wsl_base_path = Path('/mnt/d/project/cnctd/data/textures/textures_td_srgb/DATA/ART/TEXTURES/SRGB/TIBERIAN_DAWN')
_win_base_path = Path('c:d\project\cnctd\data\textures\textures_td_srgb\DATA\ART\TEXTURES\SRGB\TIBERIAN_DAWN')
_base_path = None

_output_path = None


if os.path.exists(_wsl_base_path):
    _base_path = _wsl_base_path
if os.path.exists(_win_base_path):
    _base_path = _win_base_path

_null_filter = re.compile('^\n$')

def action_none( _ ):
    return


def action_print( name : str ):
    print(name)

_png_filter = re.compile('.+\.png$')
_tga_filter = re.compile('.+\.TGA$')
_dds_filter = re.compile('.+\.DDS$')

# Uses package:
# https://docs.wand-py.org/en/0.6.11/
def action_dds_to_png( name: str ):
    from_suffix = 'DDS'.upper()
    to_suffix = 'png'.lower()
    if name.upper().endswith(from_suffix):
        with Image(filename=name) as read_image:
            with read_image.clone() as write_image:
                write_image.format = to_suffix
                write_image_name = str(_output_path.joinpath( Path(name).stem + '.' + to_suffix))
                print("<<<: " + write_image_name)
                write_image.save(filename=write_image_name)

_zip_filter = re.compile('.+\.ZIP$')
def action_unzip( zip_file_path: Path ):
    extract_dir = zip_file_path.parent
    with zipfile.ZipFile( zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

_matches_found = 0
_done = False

def apply( curpath: Path, filter: re.Pattern, action=None, **kwargs ):
    if isinstance( curpath, str):
        curpath = Path(curpath)

    indent = kwargs.get("indent", 4)
    kwargs["indent"] = indent + 4
    max_count = kwargs.get("max", sys.maxsize)
    verbose = kwargs.get("verbose", 0)

    if 2 < verbose:
        print(f"  @:path: {curpath}: {len(os.listdir(curpath))}")

    for subdir in os.listdir( curpath ):
        global _done
        if _done:
            return True
         
        subpath = curpath.joinpath(subdir)
        if subpath.is_dir():
            if 0 < verbose:
                print(f"{' ':{indent}}==> descending into: {subdir} ({str(subpath)})")
            apply( subpath, filter, action, **kwargs )

        elif filter.match(subdir):
            if 1 < verbose:
                print(f"{' ':{indent}}[o] Found:    {str(subpath)}")
            global _matches_found
            _matches_found += 1
            if max_count < _matches_found:
                _done = True
            filename = subdir
            action(str(subpath))
        else:
            filename = subdir
            if 2 < verbose:
                print(f"{' ':{indent}}XX:Skip: {filename}")

    return True

if "__main__" == __name__:

    parser = argparse.ArgumentParser(prog='extractor',
                    description='extract certain files from game archive')
    parser.add_argument('-b','--base-path')
    parser.add_argument('-s', '--search-path')
    parser.add_argument('-o','--output-path')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()
    
    if args.base_path:
        base_path = args.base_path
    else:
        base_path = Path(_base_path)

    if args.search_path:
        search_path = args.search_path
    else:  
        search_path = base_path.joinpath('TERRAIN','DESERT')

    if args.output_path:
        _output_path = args.output_path
    else:  
        _output_path = Path('data/stage/')

    verbose = args.verbose
    if 0 < verbose:
        print(f"Starting at: {search_path}")

    apply( search_path, filter=_dds_filter, action=action_dds_to_png, verbose=verbose )

