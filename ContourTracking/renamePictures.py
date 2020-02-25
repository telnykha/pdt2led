import argparse
import os
import shutil as sh

# from loadPictures import getPictWavelength


if __name__ == '__main__':
    cmdParser = argparse.ArgumentParser(
        description='Create test series from existing preordered sequence(s) of'
                    ' frames.\n'
                    'Note that sequences must:\n'
                    ' - be ordered by name\n'
                    ' - have \".tiff\" format\n'
                    ' - have \"_wl\" postfix for fluoImages where wl is'
                    ' a wavelength',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    cmdParser.add_argument('dataBaseDirec', metavar='dbdir',
                           help='the data base directory')
    cmdParser.add_argument('fileDirec', metavar='fdir',
                           help='a directory containing frame sequence')
    cmdParser.add_argument('-fl', '--fluo', action='store_const', const=True,
                           default=False,
                           help='process clinic fluorescent series'
                                ' (default:False)')
    cmdParser.add_argument('-bg', '--background', action='store_const',
                           const=True, default=False,
                           help='subtract background with postfix \"_0\"'
                                ' (default:False)')

    cmdArgs = cmdParser.parse_args()
