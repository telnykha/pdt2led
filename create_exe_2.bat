rem f:\Python\PDT_2Led\virtenv\Scripts\pyinstaller.exe --onedir --onefile --paths="F:\Python\PDT_2Led\virtenv\Lib\site-packages" --upx-dir="f:\Python\PDT_2Led" --name=Fluovisor --console main.py
rem f:\Python\PDT_2Led\virtenv\Scripts\pyinstaller.exe --onedir --paths="F:\Python\PDT_2Led\virtenv\Lib\site-packages" --upx-dir="f:\Python\PDT_2Led" --name=Fluovisor --console main.py
C:\Python27\Scripts\pyinstaller.exe --onefile --paths="C:\Python27\Lib\site-packages" --upx-dir="f:\Python\PDT_2Led"  --name=Fluovisor --console f:\Python\PDT_2Led\Main.py

del /q /s f:\Python\PDT_2Led\dist\Fluovisor\*
rmdir /S /Q "f:\Python\PDT_2Led\dist\Fluovisor\"
C:\Python27\Scripts\pyinstaller.exe --paths="C:\Python27\Lib\site-packages" --onedir --name=Fluovisor --console f:\Python\PDT_2Led\Main.py --win-private-assemblies
md f:\Python\PDT_2Led\dist\Fluovisor\Additional
copy "f:\Python\PDT_2Led\Additional\*" "f:\Python\PDT_2Led\dist\Fluovisor\Additional"
rem f:\Python\PDT_2Led\virtenv\Scripts\python.exe setup.py build
rem f:\Python\PDT_2Led\virtenv\Scripts\python.exe setup.py py2exe
