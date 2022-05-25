# sprof - Installation et utilisation Windows


## Installation de python 3 et virtualenv

Note 1 : il faut une connection internet pour cette étape

note 2 : pour vérifier si on est en 32 ou 64 : taper `système` dans la recherche pour ouvrir le panneau de configuration, et regarder dans `Système\type du système`

### 1) Vérifier si python est est déjà installé

- Taper `dos` dans la recherche, et ouvrir l'application `invite de commande``
- Tester la commande `python` ou éventuellement `python3`

### 2) Installation python

Site de téléchargement : https://www.python.org/downloads/windows/

Choisir le lien pour python 3.8 : `Download Windows x86-64 executable installer` (ou `Download Windows x86 executable installer` si on est en système 32)

Cliquer sur l'executable téléchargé. (Par défaut il est dans home\Downloads)

**Attention :** Bien cocher l'option de mise à jour du path, pour que la commande `python` soit accessible de tous les répertoires

Pour finir l'installation, dans le répertoire d'execution (`.../Download` par défaut), on clique sur l'application qui est apparue (`python 3.8 Amd64`).

mise à jour mars 2021 : au niveau de cette étape, cocher les options suivantes
- pip
- add python to env variables
- precompile standard librairie (?)

test : la commande python depuis le doc doit marcher.

On peut effacer les fichiers d'install, mais alors on ne pourra plus changer les options d'installation.

### 3) installation de virtualenv

- Ouvrir l'invite de commande (faire une recherche sur `dos`)
- taper la commande : `pip install virtualenv`

## Installation de sprof

### Installer

Créer un dossier pour l'application (par exemple, `innovalie`) et y copier le répertoire `sprof`

Bien garder le nom sprof, si besoin renommer sprof-master

Ouvrir l'invite de commande et taper les commandes :
```console
cd innovalie
virtualenv -p python3 venv_sprof
...\innovalie>venv_sprof\Scripts\activate.bat
cd ..\sprof
pip install -r requirements.txt
# ancien : python setup.py develop
pip install -e .
```

### Tester

Pour vérifier que le code tourne correctement sur les données de test, se placer dans le  répertoire sprof/sprof :

(La première execution prend beaucoup de temps, c'est normal il faut créer les fichiers .pyc)
```console
cd sprof
python radar_data.py -p blanc1
python sprint.py
```

### configurer

On peut configurer :
- Le répertoire par défaut dans lequel sprof ira chercher les données radar,
- Le fichier dans lequel se trouvent la masse et la stature des athletes,
- Les fichiers d'export csv - emplacement, caractère séparateur et décimale.

Pour cela, il faut copier le fichier `sprof\sprof\settings_local_sample.py` et le renommer en `settings_local.py`
```console
copy settings_local_sample.py settings_local.py
```

Puis ouvrir `settings_local.py` et y apporter les modifications nécessaires.

Conseil : sauvegarder une version de la configuration locale hors du code source, car en cas de mise à jour il risque d'être effacé, en utilisant par ex un répertoire 'local' :
```
mkdir ..\..\local
copy settings_local.py ..\..\local\
```
De même, ne pas mettre dans le répertoire du code source les fichiers de données des athletes. Les mettre par exemple dans ce répertoire 'local'

pour tester que le répertoire des données radar par défaut est valide, taper
(toujours à partir de `...\sprof\sprof`)
```console
python radar_file.py
```

pour tester que le fichier contenant les données des athletes est bien trouvé,
utiliser (toujours à partir de `...\sprof\sprof`):
```console
python athlete.py
```

## Utilisation

### Executables

Des executables dans le répertoire `\sprof\win\` permettent de lancer les principales fonctionnalités. Pour qu'ils soient utilisables, il faut les ouvrir en écriture et mettre à jour le chemin du projet (4eme ligne souvent)

Le mieux est de les copier dans un répertoire externe au code source, pour faciliter les mises à jour futures, par exemple le répertoire 'local'

- `sprof_analyse` : boucle sur un répertoire (par défault, ou selectionné) pour lancer un à un l'analyse pfv des fichiers souhaités
- `sprof_scandir` : scanne un répertoire de données choisi et génère un fichier csv avec lers réstultats des analyses pfv. Ce fichiers est sauvé dans le répertoire des données, et dans un répertoire d'analyse
- `sprof_watcher` : surveille un répertoire, et analyse tout nouveau fichier de données radar qui y est placé. Génère un fichier csv des résultats dans ce répertoire et dans le répertoire d'analyse
- `sprof_movebounds` : permet de tester les variations des parametres PFV pour un fichier de donnees lorsque l'on fait varier les limites du sprint
- `sprof_cdes` : Permet d'utiliser directement les commandes python sprof (= Active le virtualenv python, et de place dans le répertoire sprof su projet.

sprof_watcher et sprof_scandir ouvrent le fichier de résultat csv avec l'utilitiare `csv file viewer` de nirsoft. Une version est incluse dans le code source mais on peut aussi aller chercher les sources de cet utilitaire sur internet. **par défault, il faut dézipper les fichiers directement à la racine du projet**

On peut aussi aller modifier les executables pour utiliser plutot excel, ou open office (ou rien)

### Sous dos
- Ouvrir une invite de commande dos
- activer le virtual env python si ce n'est pas déjà fait :
`....\venv_sprof\Scripts\activate.bat`
- Se placer dans le répertoire `...\sprof\sprof`

Ou, plus moderne, utiliser PowerShell

### Exemples

Voir le README

## Mise à jour du code source sprof

Il faut recopier les fichiers sources en remplaçant les précédants, mais attention à ne pas effacer le fichier de conf local `settings_local.py`, ou à le remettre à partir d'un emplacement où il a été sauvegardé ('local' par ex)

Si on veut changer le code de place, il faut désinstaller le précédent :

```console
# python setup.py develop -u #ancien
pip uninstall sprof
````
Sous windows il faut aussi éditer le fichier `.../venv_sprof/Lib/site-packages/easy-install.pth` et effacer la ligne qui n'est plus valide. Puis on peut ré-installer sprof, à partir du répertoire racine sprof : `python setup.py develop`

Mise à jour mars 2021 : avec l'utilisation de `pip install -e .`, à priori plus besoin de faire cette manip


## Utile

Quelques commandes sous dos, l'invite de commande windows :

- cd : change de répertoire
- dir : liste le contenu d'un répertoire
- mkdir : créé un répertoire
- del : delete file
- copy : copie un fichier vers un autre
- move : déplace un fichier

Memo sur mon poste maison windows:
Pour retrouver les fichiers, aller dans dans C(Acer):Utilisateur puis Caro. C'est le répertoire
equivalent à home : si on lance l'invite de commande on est dans :C:\Users\Caro>
