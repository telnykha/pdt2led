import os
import tkinter
import tkinter.messagebox as mb
import shutil as sh


def callback():
    ans = mb.askokcancel('Warning',
                         'File processing will be done inside the current directory of the file dirwork.py.',
                         icon='warning', parent=root)
    if ans:
        files = os.listdir('.')
        s = var.get()
        direc = os.getcwd()+'\\'+s
        os.mkdir(direc)
        i_0 = 1
        i_400 = 1
        i_660 = 1
        i_740 = 1
        for f in files:
            if not (f[-3:] == 'pkl'):
                if f[-7:-5] == '_0':
                    sh.copy2(f, s + str(i_0) + '_0.tiff')
                    sh.move(s + str(i_0) + '_0.tiff', direc)
                    i_0 += 1
                elif f[-9:-5] == '_740':
                    sh.copy2(f, s + str(i_740) + '_740.tiff')
                    sh.move(s + str(i_740) + '_740.tiff', direc)
                    i_740 += 1
                elif f[-9:-5] == '_400' and f[-10] != 'n':
                    sh.copy2(f, s + str(i_400) + '_400.tiff')
                    sh.move(s + str(i_400) + '_400.tiff', direc)
                    i_400 += 1
                elif f[-9:-5] == '_660' and f[-10] != 'n':
                    sh.copy2(f, s + str(i_660) + '_660.tiff')
                    sh.move(s + str(i_660) + '_660.tiff', direc)
                    i_660 += 1

        root.destroy()

root = tkinter.Tk()
root.title('dirwork')
root.geometry('+500+200')

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