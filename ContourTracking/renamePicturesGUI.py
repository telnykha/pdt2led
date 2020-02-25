import os
import pyqtgraph
import tkinter
import shutil as sh

from loadPictures import getPictWavelength

def renamePictures(is740only=False):
    def callback():
        files = os.listdir(root.directory)
        name = root.var.get()
        root.newdirectory =  ''.join([l for l in root.directory + '\\' + name])
        root.fullname = ''.join([l for l in root.newdirectory + '\\' + name])
        if not os.access(root.newdirectory, os.F_OK):
            os.mkdir(root.newdirectory)
        else:
            sh.rmtree(str(root.newdirectory))
            os.mkdir(root.newdirectory)

        progress = tkinter.Entry(root)
        progress.insert(0, 'Progress: 0')
        progress.config(width=14)
        progress.grid(row=3, column=1, rowspan=1, columnspan=2)
        if root.isFluo.get():
            i_wl = {'0': 1,
                    '400': 1,
                    '660': 1,
                    '740': 1}
            for f in files:
                if f.endswith('tiff'):
                    wl = getPictWavelength(f)
                    if str(wl) == '0':
                        sh.copy2(root.directory + '\\' + f,
                                 root.fullname + '_' + str(wl) + '_' + str(i_wl[str(wl)]) + '.tiff')
                        i_wl[str(wl)] += 1
                        progress.delete(10, tkinter.END)
                        progress.insert(10, str(i_wl[str(wl)]))
                        progress.update()
                    elif str(wl) == '740':
                        sh.copy2(root.directory + '\\' + f,
                                 root.fullname + '_' + str(wl) + '_' + str(i_wl[str(wl)]) + '.tiff')
                        i_wl[str(wl)] += 1
                    elif (str(wl) == '400' or str(wl) == '660') and not f[:-9].endswith('superposition') and is740only == False:
                        sh.copy2(root.directory + '\\' + f,
                                 root.fullname + '_' + str(wl) + '_' + str(i_wl[str(wl)]) + '.tiff')
                        i_wl[str(wl)] += 1
                    root.numFrames = i_wl[str(0)]
        else:
            i = 1
            for f in files:
                if f.endswith('tiff'):
                    sh.copy2(root.directory + '\\' + f,
                             root.fullname + '_' + str(i) + '.tiff')
                    i += 1
                    progress.delete(10, tkinter.END)
                    progress.insert(10, str(i))
            root.numFrames = i
        root.quit()

    root = tkinter.Tk()
    root.title('Directory processing')
    root.geometry('+1000+500')

    app = pyqtgraph.GraphicsWindow().setBackground(None)
    root.directory = pyqtgraph.FileDialog().getExistingDirectory(
        parent=app,
        caption='Choose the directory with images to process').toUtf8()

    message = tkinter.Entry(root)
    message.insert(0, 'Enter series name:')
    message.config(state='readonly', width=30)
    message.grid(row=1, column=1, rowspan=1, columnspan=4)

    root.var = tkinter.StringVar()
    textbox = tkinter.Entry(root, textvariable=root.var, width=30)
    textbox.focus_set()
    textbox.grid(row=2, column=1, rowspan=1, columnspan=4)

    root.isFluo = tkinter.BooleanVar()
    check = tkinter.Checkbutton(root, text="Clinic fluorescent series",
                                variable=root.isFluo)

    b = tkinter.Button(root, text="OK", command=callback)
    b.grid(row=3, column=3, rowspan=1, columnspan=1)


    root.mainloop()
    newdirectory = root.newdirectory
    numFrames = root.numFrames
    fullname = root.fullname

    root.destroy()

    return fullname, newdirectory, numFrames


if __name__ == '__main__':
    renamePictures()