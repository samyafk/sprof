# -*- coding: utf-8 -*
# python3
# innovalie - LJK - Sept 2019
"""
Scripts pour boucler des plots sur toutes les données d'un répertoire
    - boucler sur une visu avec passage à la suivante en cliquant sur une toucbe
        (arret si ctr c ou x  ou esc)
    - visu automatique avec arret de 3 (ou x) secondes entre les visus,  ctr x ou c si on 
       veut arreter
    - Sauvegarde des images dans le répertoire
    - ...
"""
import matplotlib.pyplot as plt
import os 
from sprof.analyse import build_analyse_from_file
from sprof.radar_file import scan_dir 
from sprof.sprint import build_sprint_from_file

#------ Methods -------------------------------------------------------------------------

def plot_scroll():
    plt.waitforbuttonpress()
    plt.close() 

def plot_auto():
    plt.pause(3)
    plt.close()

def save_img(dir,file, pattern=""):
    # check dir
    basefile = os.path.basename(os.path.normpath(file))
    basefile = basefile[:-4]
    if pattern:
        basefile+='_'+pattern
    basefile+='.png'
    fullpath=os.path.join(dir,basefile)
    print(fullpath)
    plt.savefig(fullpath) 
    plt.close()

# bien mettre l'option -e rad
@scan_dir(max_file=1)
def sprint_manual(file):
    rd=build_sprint_from_file(file, auto=False,outliers=False)
    s.print_result()
    s.plot_outliers()
    plt.show()

@scan_dir(max_file=50)
def points_impact_0out(file):
    dir='/Users/bligny/Projects/innovalie/img/outliers/pt_impact_0out'
    s = build_sprint_from_file(file, outliers=False) 
    s.plot_points_impact()
    save_img(dir,file)

def points_impact(file,dir):
    s = build_sprint_from_file(file) 
    s.plot_points_impact()
    save_img(dir,file,'imp')
    s.plot_outliers()
    save_img(dir,file,'sprint')

@scan_dir(max_file=50)
def points_impact_allout(file):
    dir="/Users/bligny/Projects/innovalie/img/outliers/pt_impact_allout"
    points_impact(file,dir)

# on modifie le code de sprint.py pour ne garder qu'une partie du filtre des outliers 
# 1) enleve retrait systématique des pts distants
@scan_dir(max_file=50)
def points_impact_distout(file):
    dir="/Users/bligny/Projects/innovalie/img/outliers/pt_impact_distout"
    points_impact(file,dir)

# on modifie le code de sprint.py pour ne garder qu'une partie du filtre des outliers 
# 1) enleve retrait systématique des pts impactants
@scan_dir(max_file=50)
def points_impact_impout(file):
    dir="/Users/bligny/Projects/innovalie/img/outliers/pt_impact_impout"
    points_impact(file,dir)

@scan_dir(max_file=50)
def plot_normalize(file):
    # same scale for all plots
     # v from 0 to 10 m/s
    # t from i start -1 to i start + 6

    plt.figure(figsize = (10, 8))

    # save images
    dir='/Users/bligny/Projects/innovalie/img/run_juillet'

    a=build_analyse_from_file(file)

    if a:
        a.plot_normalize()
        save_img(dir,file)
    #plt.show()

# ------  Analyses ----------------------------------------------------------------------
    
if __name__ == "__main__":

    #points_impact_0out()
    #points_impact_allout()
    #points_impact_distout()
    #points_impact_impout()
    plot_normalize()