import cv2 as cv
import os

def getPictWavelength(filename):
    wl = ''
    for l in filename[-6::-1]:
        if l == '_':
            break
        wl += l
    try:
        return int(wl[::-1])
    except ValueError:
        return None

def getPictNumber(filename, wl):
    num = ''
    for l in filename[-7 - len(str(wl))::-1]:
        if l == '_':
            break
        num += l
    return int(num[::-1])

def getDirectoryFromFullPictName (fullName):
    direc = fullName[:]
    for l in fullName[::-1]:
        if l == '\\':
            break
        direc = direc[:-1]
    return direc

def getPictTrue(filename, wl=None):
    pictFluo = cv.imread(filename, cv.IMREAD_UNCHANGED)
    pictNull = cv.imread(filename.replace(wl+'.tiff', '0.tiff'), cv.IMREAD_UNCHANGED)
    pictFluo = (pictFluo - pictNull) * (pictFluo > pictNull)
    return pictFluo

def getPictsByNumber(name, begin, end, wl):
    vctPicts = []
    for i in range(begin, end + 1):
        vctPicts.append(getPictTrue(name + '_' + str(i) + '_' + str(wl) + '.tiff', wl))
        print('frame ' + str(i) + ' (' + str(i-begin) + '/' + str(end-begin) + ')')
    return vctPicts

def getPictFromDirecAll(direc, wl):
    vctPicts = []
    files = {}
    for f in os.listdir(direc):
        if f.startswith('frame') and f.endswith(str(wl) + '.tiff'):
            number = f[6:-6 - len(str(wl))]
            for l in f[6:]:
                if l.isdigit():
                    number = number + l
                else: break
            files[f] = int(number)
    sortedFiles = [k for (k, v) in sorted(files.items(), key=lambda kv: (kv[1], kv[0]))]
    for f in sortedFiles:
        vctPicts.append(getPictTrue(direc + '\\' + f, wl))
        print('\t\t\tget ' + f)
    return vctPicts



