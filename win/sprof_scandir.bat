:: lance l'analyse pfv sur tout un repretoire, et genere un fichier csv dans ce
:: repertoire et dans le repertoire d'analyse par defaut
@echo on
:: Remplacer la ligne suivante par le chemin approprié du projet
cd C:\Users\...\innovalie
call venv_sprof\Scripts\activate.bat
::cd sprof\sprof

@echo off
setlocal

set title='Choisissez le repertoire contenant les donnees radar a analyser'
::set rootFolder='C:\Users\...\innovalie'

set "psCommand="(new-object -COM 'Shell.Application')^
.BrowseForFolder(0,%title%,0,0).self.path""
::.BrowseForFolder(0,%title%,0,"%rootFolder%").self.path""

for /f "usebackq delims=" %%I in (`powershell %psCommand%`) do set "folder=%%I"

setlocal enabledelayedexpansion
echo ..... Analyse des donnees radar contenues dans le repertoire : ......
echo !folder!
echo ..........
endlocal

:: lance l'analyse
python sprof\sprof\pfv_dataset.py -d "%folder%"

:: get filename
:: chosen dir + yymmdd+'_pfv_Analyse.csv'
:: WARNING : if this name changes in the source code, this won't work anymore
:: this should be a temporary workaround
set mydate=%date:~8,2%%date:~3,2%%date:~0,2%
set csvFile=%folder%\%mydate%_pfv_Analyse.csv
:: echo %csvFile%
:: 
:: search notepad > ouvrir emplacement du fichier ; et depuis le fichier ouvrir les properties. 
:: set openWith="C:\Program Files (x86)\Notepad++\notepad++.exe"
set openWith="csvfileview\CSVFileView.exe"
:: set openWith="C:\Program Files (x86)\OpenOffice 4\program\scalc.exe"
:: echo %openWith%

%openWith% "%csvFile%"

:: laisse la fenetre de commande ouverte, pour voir le resultat et en cas d'erreur
cmd /k
