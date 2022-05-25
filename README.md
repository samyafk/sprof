# sprof - Sprint Profiling using radar data

Analyse automatique de données radar de sprint, en vue d'extraire des valeurs caractéristiques du profil Puissance - Force - Vitesse des athlétes.
Code python développé au Laboratoire Jean Kuntzmann (Caroline Bligny), en collaboration avec le FCG, et basé sur les travaux de recherche de Pierre Samozino.

Le code sprof est distribué sous la license LGPL-3.0. Cette license est référencée sur le site https://www.data.gouv.fr/en/licence

# Install

## Requirements
python 3 et virtualenv

## Get source code
from https://gricad-gitlab.univ-grenoble-alpes.fr/innovalie/sprof

Download the source code and unzip, or clone the repository

## Create and activate a python virtual env
```console
cd [my/project/dir]
# créer le virtual env
virtualenv -p python3 venv_sprof
# activer le virtual env
source venv_sprof/bin/activate
# ou, depuis un autre répertoire
source my/project/dir/venv_sprof/bin/activate
```
Note : pour désactiver le virtual env, utliser : ```deactivate```

## Install python packages

```console
# Se placer à la racine du code source
cd sprof
# Intaller les paquets pyhon requis
pip install -r requirements.txt
# Installer les module sprof
pip install -e .
```

Note : en cas de mise à jour du path contenant les sources, il faudra probablement désinstaller puis ré-installer sprof:
```console
# Se placer à la racine du code source
pip uninstall sprof
```
Sous windows cela n'a pas été suffisant, il faut éditer le fichier `.../venv_sprof/Lib/site-packages/easy-install.pth`
et supprimer la ligne qui n'est plus valide

## Update settings

Pour mettre à jour les répertoires de données par défault que doit utiliser sprof, copier le fichier settings_local_sample.py, le renommer en settings_local.py, puis modifier les données voulues.

# Basic Usage

sprof est à la base une librairie python, mais il contient aussi quelques executables en ligne de commande.

## Préalable :
- activer le virtual env python si ce n'est pas déjà fait (```source ..../venv_sprof/bin/activate```)
- Se placer dans le répertoire sprof/sprof

## Commandes pour un fichier de données

- ``` python analyse.py -p berru1 ``` : Lance l'analyse complete du profil PFV pour le fichier de données source "Juillet Berruyer 1.rda" trouvé dans le répertoire par défaut, et affiche une image des données.

- ```python pfv.py -p berru1```: Même chose que la commande précédente, mais sans l'image.

- ```python sprint.py``` : Affiche le sprint et les points abérrants enlevés, ainsi que les paramètres de la fonction vitesse calculée. Utilise le premier fichier de données radar trouvé dans le répertoire par défaut.

- ```python radar_data.py``` : charge les données radar et cherche la portion de données correspondant à un sprint. Affichage de toutes les données et du sprint extrait

- ```python radar_data.py -p blanc2``` va utiliser comme données source le fichier "Juillet blanc mappaz 2.rda" trouvé dans le répertoire par défault des données.





- ```python pfv_dataset.py``` : Analyse tous les fichiers radar trouvés, et export les valeurs caractéritiques dans un fichier csv

- ```python move_bound.py``` : Permet de bouger manuellement les bornes d'un sprint, et de voir les nouvelles valeurs ainsi générées pour l'analyse pfv


## Analyse des données à la volée

```console
python radar_watcher.py [dir_to_watch]
```
**Taper control C pour stopper l'analyse.**

Principe : Pour chaque nouveau fichier de données qui est sauvegardé dans le réperoire [dir_to_watch], l'analyse détaillée du profil PFV est lancée, et le résultat texte s'affiche dans la console. D'autre part, une image du sprint s'affiche. Elle est sauvegardée dans le répertoire [dir_to_watch].

## Analyse a postériori de tout un réportoire de données

Principe : génération d'un fichier au format csv contenant les analyses des profils PFV pour tout un jeux de données.

Pour analyser le répertoire par défaut, défini dans `settings_local.py` :
```
python pfv_dataset.py
```
Pour préciser quel réportoire on veut analyser :
```
python pfv_dataset.py -d [my_data_dir]
```

Le résultat est exporté par défaut sous `...\sprof\test\`, sauf si un autre
répertoire a été défini dans `settings_local.py`

## Paramètres utilisés pour trouver le fichier de données

Les exemples ci-dessous sont donnés pour l'athlète Berruyer, sprint 1.
Pour avoir un autre athlete, il suffit de donner tout ou parti de son nom, plus
le numéro du sprint. (ex : blanc2 analysera le run 2 de l'athlete 'blanc mappaz').
Pour voir les autres paramètre que l'on peut fournir, taper `python pfv.py -h`

Toutes les commandes listées ci-dessous commencent par chercher un fichier de données radar. On peut passer 4 paramètres (optionnels) pour préciser quel fichier on veut analyser :

- -d pour désigner le répertoire des données radar. Si non fourni, le répertoire défini dans les settings est utilisé
- -p indique le pattern que doit contenir le nom du fichier de données, c'est à dire tout ou parti du nom de l'athlete et le numéro du sprint
- -e pour forcer l'extension du fichier à prendre en compte à '.rad'. Par défaut, c'est le fichier .rda qui est utilisé
- -f si on veut donner le nom du fichier complet avec son répertoire

**Afficher l'analyse détaillés :**
```
python analyse.py -p berru1
```

**Afficher l'analyse détaillés sans l'image:**
```
python pfv.py -p berru1
```

**Afficher le sprint, et les points enlevés :**
```
python sprint.py -p berru1
````

**Afficher toutes les données, pour voir les limites du sprint retenu :**
```
python radar_data.py -p berru1
````

**Analyser un fichier de données qui a déjà été traité :**

Par défault, on charge les données brutes (`.rda`). Toutefois, on peut choisir de lancer l'analyse sur les données déjà traitées (`.rad`)
```
python radar_data.py -p berru1 -e rad
# ou
python sprint.py -p berru1 -e rad
# etc
````

**Modifier manuellement les bornes du sprint, et voir les résultats :**
```
python move_bound.py -p berru1
````
