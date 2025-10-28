link github:
https://github.com/Giovanenero/escalonador


pyinstaller --onefile --add-data "/usr/share/tcltk/tcl8.6:lib/tcl8.6" --add-data "/usr/share/tcltk/tk8.6:lib/tk8.6" --hidden-import PIL._tkinter_finder --hidden-import tkinter --hidden-import matplotlib.backends.backend_tkagg main.py 
chmod ./dist/main
./dist/main


# Windows
pyinstaller --onefile --add-data "C:\Users\rafa1\AppData\Local\Programs\Python\Python313\tcl\tcl8.6;lib\tcl8.6" --add-data "C:\Users\rafa1\AppData\Local\Programs\Python\Python313\tcl\tk8.6;lib\tk8.6" --hidden-import PIL._tkinter_finder --hidden-import tkinter --hidden-import matplotlib.backends.backend_tkagg main.py



