# -*- coding: utf-8 -*
# python3
# Innovalie - LJK - septembre 2019
"""
Scripts de comparaison de 2 datasets calculés :
 - avec ou sans outliers, 
 - avec ou sans auto-bounds
 - Résultats manuels (fournis par FCG) vs calculés
"""
from sprof.pfv_dataset import build_PFV_DS_from_files
from sprof.radar_file import params_get_files
import pandas as pd
from sprof.settings import PFV_ANALYSE_DIR
from datetime import datetime
import os

# ------- Méthodes --------

def save_df_to_csv(df, title):
    filename= datetime.now().strftime("%y%m%d")+'_'+title+".csv"
    file=os.path.join(PFV_ANALYSE_DIR, filename)
    df.to_csv(file,index = None, header=True)

def compare_to_manual(files,title,auto,outliers):

    manual_file="/Users/bligny/Projects/innovalie/sources_git/sprof/data/analyse_manuelle_juillet2019.csv"
    df_man=pd.read_csv(manual_file, decimal=",") # manual analyses

    ds=build_PFV_DS_from_files(files,title, auto=auto, outliers=outliers)
    df_diff=ds.compare(df_man)
    
    print(ds)
    print(df_man)
    print(df_diff)
    
    save_df_to_csv(df_diff,title)

# ------- Les differntes comparaisons --------
# build FVP dataset from file with default options, and export a csv file
def analyse():
    ds=build_PFV_DS_from_files('Analyse')
    ds.export_csv() 

# bien utiliser -e rad dans les params, sinon ça rime à rien
# compare prepared data files (=.rad) results with excel sheet results
# même résultats attendus. diff : pas la stature, et pente un peu diff excel vs python
# il faut aussi qu'il y ait exactement le même nombre de ligne.
# Bref. il faudrait être sur de comparer les bonnes lignes. A améliorer.
def manual_vs_nodefaults(files):
    
    title='manual_vs_nodefaults'
    compare_to_manual(files,title, auto=False, outliers=False)

    
def manual_vs_auto(files):
    """
    Comparaison de l'analyse automatique et de l'analyse manuelle
    """
    title='manual_vs_auto'
    compare_to_manual(files,title, auto=True, outliers=True)
    
# bien utiliser -e rad dans les params, sinon ça rime à rien
def manual_vs_outliers(files):
    """ Comparaison de l'analyse manuelle et de l'analyse automatique sans calculer les 
    sprint bounds, mais en enlevant les points aberrants
    """
    title='manual_vs_outliers'
    compare_to_manual(files,title, auto=False, outliers=True)

# bien utiliser -e rad dans les params, sinon ça rime à rien
def manual_vs_bounds(files):
    """ Comparaison de l'analyse manuelle et de l'analyse automatique en recalculant
    les sprints bounds, mais sans enlever les points aberrants
    """
    title='manual_vs_bounds'
    compare_to_manual(files,title, auto=True, outliers=False)
 
      
if __name__ == "__main__":

    files=params_get_files()

    # avec ou sans l'option -e rad
    #analyse()
    manual_vs_auto(files)
    
    # avec l'option -e rad
    #manual_vs_nodefaults(files)
    #manual_vs_outliers(files)
    #manual_vs_bounds(files)

 