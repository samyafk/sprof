:: lancer le data watcher sprof
@echo on
:: Remplacer la ligne suivante par le chemin approprié du projet
cd C:\Users\...\innovalie
call venv_sprof\Scripts\activate.bat
::cd sprof\sprof

@echo off
setlocal

set "psCommand="(new-object -COM 'Shell.Application')^
.BrowseForFolder(0,'Choisissez le repertoire ou vont etre enregistrees les donnees radar',0,0).self.path""

for /f "usebackq delims=" %%I in (`powershell %psCommand%`) do set "folder=%%I"

setlocal enabledelayedexpansion
echo ..... Analyse a la volee de donnees radar ......
echo Repertoire des donnees !folder!
echo ..........
endlocal

:: Pre-ouvrir le csv de resultats pour voir les resultats en live
:: get filename
:: chosen dir + yymmdd+'_pfv_Analyse.csv'
:: WARNING : if this name changes in the source code, this won't work anymore
:: this should be a temporary workaround
set mydate=%date:~8,2%%date:~3,2%%date:~0,2%
set csvFile=%folder%\%mydate%_pfv_Analyse.csv
:: echo %csvFile%
:: search notepad > ouvrir emplacement du fichier ; et depuis le fichier ouvrir les properties. 
:: set openWith="C:\Program Files (x86)\Notepad++\notepad++.exe"
set openWith=sprof\win\csvfileview-x64\CSVFileView.exe
:: set openWith="C:\Program Files (x86)\OpenOffice 4\program\scalc.exe"
:: echo %openWith%

:: Si le fichier de resultat n'existe pas on le créé
if not exist "%csvFile%" echo.> "%csvFile%" 
timeout 1

:: ajouter start permet de lancer la visua du csv dans un autre process
start %openWith% "%csvFile%"

:: lance l'analyse
python sprof\sprof\radar_watcher.py "%folder%"

:: laisse la fenetre de commande ouverte en cas d'erreur
cmd /k
