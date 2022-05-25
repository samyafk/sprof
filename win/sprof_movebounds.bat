:: Teste les variations des parametres PFV pour un fichier de donnees lorsque l'on fait varier les
:: limites du sprint.
@echo on
:: Remplacer la ligne suivante par le chemin approprié du projet
cd C:\Users\...\innovalie
call venv_sprof\Scripts\activate.bat
cd sprof\sprof

@echo off
setlocal

set "psCommand="(new-object -COM 'Shell.Application')^
.BrowseForFolder(0,'Choisissez un repertoire contenant les donnees radar, ou annlez pour garder le repertoire par default',0,0).self.path""

for /f "usebackq delims=" %%I in (`powershell %psCommand%`) do set "folder=%%I"

if "%folder%" == "" set folder=default

setlocal enabledelayedexpansion
echo ..... Analyse PFV de donnees radar ......
echo Repertoire des donnees : !folder!
echo ..........
endlocal

:: boucler jusqu'a fermeture de la fenetre
:run-pfv

set /p pattern=Entrez un element du nom du joueur : 
:: lancer le module move_bound
if "%folder%" == "default" (
   python move_bound.py -p "%pattern%"
) else (
   python move_bound.py -p "%pattern%" -d "%folder%"
)
echo ..........
goto :run-pfv