import os
import pyqtgraph

def rename():
    app = pyqtgraph.GraphicsWindow().setBackground(None)
    directory = pyqtgraph.FileDialog().getExistingDirectory(
        parent=app, caption='Choose the directory with images to rename').toUtf8()

    files = os.listdir(directory)
    name = ''
    for l in directory[::-1]:
        if l == '\\': break
        name = name + l
    name = name[::-1]
    for f in files:
        if f[:len(name)] == name:
            os.rename(directory + '\\' + f,
                      directory + '\\' + 'frame' + f[len(name):])
    os.rename(directory, directory[:-(len(name) + 1)] + '\\' + 'Test')


if __name__ == '__main__':
    while True:
        rename()