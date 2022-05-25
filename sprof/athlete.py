# -*- coding: utf-8 -*
# python3
# Author : LJK - Laboratoire Jean Kuntzmann - C. Bligny

"""
Athlete and AthleteDS (DS for Dataset) Classes.
Main functionnality : find an athlete datas (currently, mass and stature), given a
name pattern.
"""

from sprof.utils import str_isin, str_eq, print_obj_attr
from sprof.settings import ATHLETE_DATA_DIR, ATHLETE_DATA_FILE, CSV_ATHLETE_SEPARATOR
import pandas as pd
import os

# ------ Utils --------------------------------------------------------------------------
def get_athlete_values(pattern):
    """ Get athlete mass and stature wich name matches the input pattern
        returns (mass,stature)
    """
    mass=None
    stature=None
    a=build_athlete(pattern)
    if not a:
        print(f"WARNING : athlete non trouvé dans les donnees")
    else:
        print(f"Athlete : {a.name}, {a.mass} kg, {a.stature} m")
        mass=a.mass
        stature=a.stature
        
    return(mass,stature)
    
# ------ Athlete Builder ----------------------------------------------------------------

def build_athlete(pattern):
    """
    An Athlete builder.
    Input : athlete name pattern
    Return an Athlete class instance matching this pattern, if one and only one was 
    found.
        - if pattern is included in an athlete name (and only one)
        - if an athlete name (and only one) is included in the file name
        - insensible à la casse et aux accents ou autres caractères speciaux
    """
    ds = AthleteDS()
    a = ds.find_athlete(pattern)
    return a
    
# ------ Athlete Class ------------------------------------------------------------------
class Athlete():

    def __init__(self, name, mass=None, stature=None):
    
        self.name=name
        self.mass=None
        self.stature=None
        
        if mass:
            try:
                self.mass=float(mass)
            except ValueError:
                self.mass=float(mass.replace(",","."))
                
        if stature:
            try:
                self.stature=float(stature)
            except ValueError:
                self.stature=float(stature.replace(",","."))
                
    def __str__(self):
        str= f"Caractéristiques de l'athlète {self.name}"
        if self.mass:
            str+=f"\nMass\t {self.mass} kg"
        if self.stature:
            str+=f"\nStature\t {self.stature} m"
        return str
  
    def __repr__(self):
        return self.name
      
    def print_attr(self):
        print_obj_attr(self)  
       
       
# ------ Athlete Dataset Class ----------------------------------------------------------

class AthleteDS():
    """
    Manage the athlete dataset, using pandas data struture.
    The athlete list and characteristics are store in a csv file
    """

    DATA_FILE = os.path.join(ATHLETE_DATA_DIR, ATHLETE_DATA_FILE)
    
    def __init__(self, datafile=None, debug=False):
        # init the self.datas attribute as a panda dataframe containing all the athletes
        # datas
        
        if (datafile):
            self.datas=pd.read_csv(datafile,sep=CSV_ATHLETE_SEPARATOR)
        else:
            self.datas=pd.read_csv(self.DATA_FILE,sep=CSV_ATHLETE_SEPARATOR)

        # on pourrait ici convertir en float

    def __str__(self):
        return str(self.datas)

    # TODO : group the following functions, (get_athlete_values) and return a dic?

    def get_mass(self,pattern):
        """
        Returns the mass for athlete matching the pattern name. None value if 0 or 
        several athletes matches the pattern, or if the mass was not provided.
        """
        mass=None      
        a=self.find_athlete(pattern)
        if a:
            mass=a.mass
        return mass
 
    def get_stature(self,pattern):
        """
        Returns the stature for athlete matching the pattern name. None value if 0 or 
        several athletes matches the pattern, or if the mass was not provided.
        """
        stature=None      
        a=self.find_athlete(pattern)
        if a:
            stature=a.stature
        return stature
        
    def find_athlete(self, pattern):
        """
        Returns the athlete which name matches the pattern. Returns None 0 or 
        several athletes are found.
        WARNING : This function is OK with the current datas (10-2019), but could fails 
        for new athlete names :
        Let's add the athlete "Reykjavik" in the input dataset. Then use : 
        find_athlete("Juillet Reykjavik 1.rad") 
        There are 2 candidates : Rey and Reykjavik
        Same pb will arise if an athlete get a month name (juillet), or any other string 
        included in the file name.
        """
        rows=[] # c'est quel type?$
        a = None
    
        # Find "exact" match (excepting upper/lower case, and any not ascii or special
        # characters
        rows = self._find_name(pattern)
        
        # If not found, - check if there is one athlete for which the pattern is included
        # in the name 
        if len(rows)!=1:
            rows = self._find_name_contains(pattern)
        
        # If not, check if there is one athlete for witch the name is included in the 
        # pattern.    
        # This may happen when the pattern is a filename; So let's remove first the path.
        if len(rows)!=1:
            basefile=os.path.basename(pattern)
            rows = self._find_name_in(basefile)
        
        # If one and only one athlete was found, build and returns the Athlete instance    
        if len(rows)==1:
            # ps.isnull, eq NaN --> None
            name=rows['name'].iloc[0]
            if pd.isnull(name):
                print(f"ERROR : le nom ne doit pas être vide")
            else:
                mass=rows['mass'].iloc[0]
                stature=rows['stature'].iloc[0]
                if pd.isnull(mass):
                    mass=None
                if pd.isnull(stature):
                    stature=None
                a=Athlete(name=name,mass=mass,stature=stature)
        else:
            print(f"L'athlete n'a pas ete identifié a partir du pattern fourni : {pattern}")

        return a

    def _find_name_in(self, pattern):
        rows = self.datas.loc[self.datas['name'].apply(lambda x: str_isin(x,pattern))]
        return rows
        
    def _find_name_contains(self, pattern):
        rows = self.datas.loc[self.datas['name'].apply(lambda x: str_isin(pattern,x))]
        return rows
        
    def _find_name(self, name):
        rows = self.datas.loc[self.datas['name'].apply(lambda x: str_eq(x,name))]
        return rows
        
# ------ Main ---------------------------------------------------------------------------
if __name__ == "__main__":
    
    # test AtheleDS Class
    def test_dataset():
        ds=AthleteDS()
        #print(ds.datas)
        print(ds)

        file="my/path/to/Juillet berruyer 1.rad"
        mass=ds.get_mass(file)
        stature=ds.get_stature(file)
        print(file)
        print(mass)
        print(stature)

        file="berru"
        mass=ds.get_mass(file)
        stature=ds.get_stature(file)
        print(file)
        print(mass)
        print(stature)

        file = "Mon voisin totoro"
        mass=ds.get_mass(file)
        print(mass)
   
        file="tui"
        mass=ds.get_mass(file)
        stature=ds.get_stature(file)
        print(file)
        print(mass)
        print(stature)
    
    # test Athlete Class        
    def test_athletes():
    
        a = build_athlete("Tuinukuafe 2_SimpleMethodSprint_V14_mps.xlsm")
        print(a)
        a = build_athlete("Tui")
        print(a)
        a = build_athlete("berru")
        print(a)
        a = build_athlete("a")
        print(a)
   
    def test_athlete():
        a=build_athlete("juillet l-trial 1 juillet")
        print(a)
               
    #test_athletes()
    #test_dataset()
    test_athlete()
     