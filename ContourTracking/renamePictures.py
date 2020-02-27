import argparse
import configparser
import os
import shutil as sh

# from loadPictures import getPictWavelength

class DataBase:
    # initializing rom config
    def __init__(self):
        # TODO
        self.seriesQuantity = 0

    def loadConfig(self, configPath):
        # TODO
        # TODO
        config.read(baseDirect)

    def incQuantity(self):
        self.seriesQuantity +=1


    def saveConfig(self, configPath):
        # TODO
        pass

if __name__ == '__main__':
    cmdParser = argparse.ArgumentParser(
        description='Create test series from an existing preordered sequence of'
                    ' frames.\n'
                    'Note that the sequence must:\n'
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
    baseDirect  = cmdArgs.dataBaseDirec
    fileDirects = cmdArgs.fileDirec
    isFluo      = cmdArgs.fluo
    isBg        = cmdArgs.background

# TODO: mb засунуть это в класс, а класс - в отд. файл
    config = configparser.ConfigParser()
    if not os.access(baseDirect, os.F_OK):
        while True:
            ans = input('DataBase directory doesn\'t exist. Create? (y/n)\n')
            if ans is 'n':
                exit(0)
            elif ans is 'y':
                break
        os.mkdir(baseDirect)
        dataBase = DataBase()
        dataBase.saveConfig(baseDirect + '\\config.ini')
    elif not os.access(baseDirect + '\\config.ini', os.F_OK):
        while True:
            ans = input('DataBase doesn\'t exist in this directory. Create new?'
                        ' (y/n)\n')
            if ans is 'n':
                exit(0)
            elif ans is 'y':
                break
        dataBase = DataBase()
        dataBase.saveConfig(baseDirect + '\\config.ini')
    else:
        cmdParser.error('')

