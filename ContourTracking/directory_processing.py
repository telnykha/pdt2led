import os
import pyqtgraph
import tkinter
import shutil as sh

def directory_processing(is740only=False):
    def callback():
        files = os.listdir(directory)
        name = var.get()
        root.newdirectory =  ''.join([l for l in directory + '\\' + name])
        root.fullname = ''.join([l for l in root.newdirectory + '\\' + name])
        if not os.access(root.newdirectory, os.F_OK):
            os.mkdir(root.newdirectory)
        else:
            sh.rmtree(str(root.newdirectory))
            os.mkdir(root.newdirectory)
        i_0 = 1
        i_400 = 1
        i_660 = 1
        i_740 = 1
        progress = tkinter.Entry(root)
        progress.insert(0, 'Progress: 0')
        progress.config(width=14)
        progress.grid(row=3, column=1, rowspan=1, columnspan=2)
        for f in files:
            if not (f[-3:] == 'pkl'):
                if f[-7:-5] == '_0':
                    sh.copy2(directory + '\\' + f,
                             root.fullname + '_' + str(i_0) + '_0.tiff')
                    i_0 += 1
                    progress.delete(10, tkinter.END)
                    progress.insert(10, str(i_0))
                    progress.update()
                elif f[-9:-5] == '_740':
                    sh.copy2(directory + '\\' + f,
                             root.fullname + '_' + str(i_740) + '_740.tiff')
                    i_740 += 1
                elif f[-9:-5] == '_400' and f[-10] != 'n' and is740only is False:
                    sh.copy2(directory + '\\' + f,
                             root.fullname + '_' + str(i_400) + '_400.tiff')
                    i_400 += 1
                elif f[-9:-5] == '_660' and f[-10] != 'n' and is740only is False:
                    sh.copy2(directory + '\\' + f,
                             root.fullname + '_' + str(i_660) + '_660.tiff')
                    i_660 += 1
        root.numFrames = i_0
        root.quit()

    app = pyqtgraph.GraphicsWindow().setBackground(None)
    directory = pyqtgraph.FileDialog().getExistingDirectory(
        parent=app, caption='Choose the directory with images to process').toUtf8()

    root = tkinter.Tk()
    root.title('Directory processing')
    root.geometry('+1000+500')

    message = tkinter.Entry(root)
    message.insert(0, 'Enter series name:')
    message.config(state='readonly', width=30)
    message.grid(row=1, column=1, rowspan=1, columnspan=4)

    var = tkinter.StringVar()
    textbox = tkinter.Entry(root, textvariable=var, width=30)
    textbox.focus_set()
    textbox.grid(row=2, column=1, rowspan=1, columnspan=4)

    b = tkinter.Button(root, text="OK", command=callback)
    b.grid(row=3, column=3, rowspan=1, columnspan=1)


    root.mainloop()
    newdirectory = root.newdirectory
    numFrames = root.numFrames
    fullname = root.fullname

    root.destroy()

    return fullname, newdirectory, numFrames


if __name__ == '__main__':
    directory_processing()