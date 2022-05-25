# -*- coding: utf-8 -*
# python3
# Author : LJK - Laboratoire Jean Kuntzmann - C. Bligny
"""
Radar Data module
input : full radar data records, as a time array and a velocity array.
The main pupose of this module is to extract the sprint part of the whole radar data.
The velocity fonction f, related to time t during the sprint acceleration is :
    f(t) = v_max * ( 1-exp(-t/tau) )
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import logging
from sprof.utils import lissage, sum_distances, bisect_left, bisect_right, print_obj_attr, get_iprevious, get_inext
from sprof.radar_file import RadarFile, build_RF_from_pattern


def build_RD_from_file(filename, auto=True):
    """
    Build and returns a RadarData instance, using a radar data file.
    """
    rf = RadarFile(filename)
    rd = RadarData(rf.T,rf.V,rf.title, auto=auto)
    return rd
 
def build_RD_from_pattern(dir="", pattern="",ext="", auto=True):
    """
    Build and returns a RadarData instance, using a pattern for the radar data file.
    Search donne in the default radar data dir
    """
    rf=build_RF_from_pattern(dir=dir, pattern=pattern,ext=ext)
    rd = RadarData(rf.T,rf.V,rf.title, auto=auto)
    return rd
 
class RadarData:
  
	# Computation constants
    SMOOTH_ITERATION = 300 # artisanal way to compute v_smooth - much slower
    PLATEAU_RATIO = 0.2
    SPRINT_VMAX_MIN = 6
    SPRINT_VMAX_MAX = 11
    
    def __init__(self, T, V, title="", auto=True):
        """ init Class Attributes. 
           Convention : for velocity (v, V) and time (T, t), Arrays/Vectors starts 
           with uppercase, scalar with lowercase
           If auto=True, automatically search and set sprint bounds :
            - search most accurate sprint start
            - set sprint end when v = vmax * plateau ratio. A more accurate value for
              sprint ent time is computed by the Sprint class
        """

        # input Datas
        # input T and V
        self.T_in = np.array([],dtype='float') # float np array 1D
        self.V_in = np.array([],dtype='float') # float np array  1D
        # T and V potentially without outliers
        self.T = np.array([],dtype='float') # float np array 1D
        self.V = np.array([],dtype='float') # float np array  1D
        self.title=title
        
        # Smooth velocity, used to roughtly locate the end of acceleration, check the data
        # and reduce the portion to search for start sprint
        self.V_smooth = np.array([],dtype='float') 
        self.vs_max = 0.0 # Max velocity measured after smoothing
        self.i_vs_max = 0 # index of the max velocity measured after smoothing
        self.data_error = True

        # Sprint bounds and values inside data
        self.i_start_sprint = 0 # Sprint start index
        self.i_end_sprint = 0 # Sprint end index
        self.i_start_plateau = 0 # Sprint start index
        self.i_end_plateau = 0 # Sprint end index
        
        # working data used to find sprint start
        self.V_model_simp = np.array([],dtype='float') # Function used to find i_start - minimise the sum of squares distance to F
        self.i_start_v_model = 0
        self.i_end_v_model = 0

        # Some input data checks
        if len(V)!=len(T):
            print("ERREUR : les tableau d'entrée ne sont pas de la même taille")  
        elif len(V)==0:
            print("ERREUR : les données sont vides")
        else:
            # Datas
            self.T_in = np.array(T,dtype='float') # Time array
            self.V_in = np.array(V,dtype='float') # Velocity array   
            self.T = np.copy(self.T_in)
            self.V = np.copy(self.V_in)
            
            self._init_Vsmooth()
            
            self.data_error = self._has_data_error()
            
            if not(self.data_error):
                #self._init_plateau()
                if auto:
                    #self.find_sprint()
                    self.find_sprint_start()
                else:
                    self.set_sprint_total()

                print(f"Données radar initialisées. Sprint : {len(self.T_sprint)} points")

    def _init_Vsmooth(self):
        """ Init V smooth, and vs_max (velocity max), using signal functions
        """    
        if self.n==0:
            print("Radar Data - Les données sont vides")
            return
        
        # calcul de la courbe de vitesse lissée - old way
        #self.V_smooth = lissage(self.V, self.SMOOTH_ITERATION)
        # en prenant en compte les points aberrants
        #self.V_smooth = self._init_Vfilter()
        
        # first pass, to detect vmesure max
        # on filtre pas mal les hautes fréquences pour lisser les anomalies.
        b, a = signal.butter(2, 0.018, 'low', analog=False)
        self.V_smooth = signal.filtfilt(b, a, self.V)
        # extraction de la vitesse max mesurée
        self.i_vs_max = np.argmax(self.V_smooth)
        self.vs_max = self.V_smooth[self.i_vs_max]
        
        self.find_sprint_end() # set i_end_sprint to v = vs_max*plateau_ratio
    
    
    def _has_data_error(self):
        # controle qualité : les données contiennent-elles un sprint?
        # returns true if an error is detected
   
        # if v max mesure is too hight or too low     
        if (self.vs_max < self.SPRINT_VMAX_MIN or self.vs_max > self.SPRINT_VMAX_MAX):
            print("ERREUR : les données ne semblent pas correspondre à un sprint")
            print(f"La vitesse max mesurée est de {self.vs_max} m/s")
            return True
   
        # If v max happens too early 
        if (self.T[self.i_vs_max] < 2):
            print("ERREUR : les données ne semblent pas correspondre à un sprint")
            print(f"La vitesse max est mesurée au bout de {self.T[self.i_vs_max]} s")
            return True
            
        return False 
    
    # attributs calculés
    
    @property
    def n(self):
        return len(self.T) # Points number (arrays size)
    
    @property
    def T_sprint(self):
        if self.i_end_sprint > 0:
            return self.T[self.i_start_sprint:self.i_end_sprint+1]
        else:
            return []
 
    @property
    def V_sprint(self):
        if self.i_end_sprint > 0:
            return self.V[self.i_start_sprint:self.i_end_sprint+1]
        else:
            return []
             
    @property
    def T_model(self):
        if self.i_end_v_model > 0:   
            return self.T[self.i_start_v_model:self.i_end_v_model+1]
        else:
            return []
             
    @property
    def timeframe(self):
        """timeframe method as an attribute
        suppose that mesures are regular"""
        if self.n > 0:
            return (self.T[-1]-self.T[0])/self.n
        else:
            return None
    
    #------------------ Methodes publiques ---------------------------------------------        
        
    def print_attr(self):
        print_obj_attr(self)


    def find_sprint_end(self):
        """
        Find the index of the end of the sprint.
        Update attributes i_end_sprint
        """

        # todo : rename set_sprint_end ? ; test V_smooth not empty

        logging.debug(f"Positionnement auto fin du sprint")
        
        # il faut
        ratio = self.PLATEAU_RATIO
        self.i_end_sprint = get_inext(self.V_smooth, self.i_vs_max, ratio)
        if self.i_end_sprint is None:
            self.i_end_sprint=self.i_vs_max
        
    
    def find_sprint_start(self):
        """
        Find the index of the sprint start.
        Updates attributs i_start_sprint, i_start_v_model
        
        Method
        Before i_start, type fonction is y=constante. Sprinter is stopped, but there is a "base" velocity
        After i_start, the function is of type y = beta * (1-np.exp(t_start-ti). It is called
        	V_model_simp in the code. (V model simplified)
        
        we search i_start which minimise :
            - For i < i_start, sum of the square of the distance to the mean velocity
            - For i >= i_start, sum of the square of the distance to V_model_simp
        For each i, we calculate the sum or this 2 distances. 
        (To reduce the calcul amount, we coule probably target the possible i_start zone - but
        currently calcul time is not a problem)
        
		Then i_start must be adjusted, to take into account the parasite stop velocity.
		The first sprint velocity points are not kept
        """

        # rename set_sprint_start ? check V_smooth not empty?

        logging.debug(f"Calcul du début du sprint")

        if self.n==0:
            print("Radar Data find sprint start - Les données sont vides")
            return

        if self.data_error:
            print("Radar Data find sprint start - Les données ne correspondent pas à un sprint")
            return

        # si on n'a pas callé la fin du sprint, on le fait ici - ça réduit un peu le nb de calculs
        #if self.i_end_sprint == 0:
        #    self.find_sprint_end() # ca va lancer aussi le find_sprint_end
            
        # on calcule la fonction modele jusqu'à self.i_end_v_model
        self.i_end_v_model = self.i_vs_max
    

        # Affinage de la zone à chercher
        # pour diminuer un peu le nb de calculs, détermination d'une fenêtre encadrant le
        # début du sprint pour lequel on va appliquer la méthode des moindres carré.
        # on prend le temps pour une vitesse de vmax/2, env au milieu de l'acceleration, 
        # puis on cherche le debut du sprint dans la fenetre (t-2s, t)
        
        # ATTENTION : cela suppose un échantillonnage régulier des pas de temps
        
        #ratio_end = 4/self.vs_max 
        ratio_end = 0.5
        i_end = get_iprevious(self.V_smooth,self.i_vs_max, ratio_end)
        i_start = i_end-int(2/self.timeframe)
        if i_start < 0:
            i_start = 0
    
        # Calcul de la somme des carré des distance aux courbes pour chaque point de la zone à chercher
        # sum of the square distances to mean and V_model_simp for start acc points
        l1 = np.array(tuple(self._get_sum_mean_distance(i) + self._get_sum_Vmodel_distance(i) for i in range(i_start,i_end)))

        # get i start theorical that minimise this sum
        # this is t0 for the generic velocity function.
        # the real sprint mesures starts a little bit after this theorical t0 : 
        # the first sprint values are hidden by the residual velocity noise.
        istart = np.argmin(l1) + i_start # on n'a pas fait le calcul sur toute la courbe
        self.i_start_v_model = istart
        # Compute final V_model_simp and vmax_simp - for debug.
        #self.V_model = self.get_F_beta(istart)[0]
        (self.V_model_simp, vmax_simp) = self._get_V_model(self.i_start_v_model)

        # search for i start sprint mesure (<> i start sprint th)
        self.i_start_sprint = self._get_start_next(self.i_start_v_model)

        logging.debug(f"indice théorique: {self.i_start_v_model}, indice corrigé : {self.i_start_sprint}")


    def extract_sprint(self):
        """
        Extracts the sprint part of the velocity and time datas.
        Suppose that i_start and i_end have been adjusted, using set_i_start() or 
        find_sprint_start and set_i_end() or find_sprint_end
        
        Array data are copied, in case we want to recalculate time using :
            self.T_sprint = self.T_sprint - self.T_sprint[0] (-self.delay ?)
        """ 

        if self.n == 0:
            print("Radar Data - Les données sont vides")
            return

        if self.data_error:
            print("Radar Data - Les données ne sont pas un sprint")
            return

        logging.debug(f"Extraction des données de sprint")

        Tsprint = np.array([],dtype='float')
        Vsprint = np.array([],dtype='float')   

        if self.i_end_sprint > 0:        
            Vsprint = np.copy(self.V_sprint)
            Tsprint = np.copy(self.T_sprint)

            # replace last value by V_smooth value - condition limites pour la suite
            Vsprint[-1] = self.V_smooth[self.i_end_sprint]

        return(Tsprint,Vsprint)

    def set_i_start_sprint(self,i_start):
    
        if i_start < 0 or i_start > self.n-1:
            i_start = 0
            
        self.i_start_sprint = i_start 

    def set_sprint_end(self,t_end):

        if t_end is None:
            i_end = self.n-1
        else:
            i_end = bisect_left(self.T, t_end)

        if i_end > self.n-1 or i_end < 0:
                i_end = self.n-1  

        self.i_end_sprint = i_end

    def set_sprint_start(self,t_start):
    
        if t_start is None:
            i_start = 0
        else:
            i_start = bisect_left(self.T, t_start)
            
        self.set_i_start_sprint(i_start)
           
    def set_sprint_bounds(self, t_start=None, t_end=None):
        """
        manually set the sprint bounds
        si start = none : on prend la première valeurs
        Pareil pour t_end, on prend la dernière
        pour tout avoir : set_sprint_bounds()
        On vérifie que i_start > i_end 
        """
        
        # On pourrait ajuster extract_sprint plutot ?
        
        logging.debug(f"\nAjustement des limites du sprint")
        
        if self.n==0:
            print("Radar Data - Les données sont vides")
            return
            
        if t_start is None:
            i_start = 0
        else:
            i_start = bisect_left(self.T, t_start)
        
        if t_end is None:
            i_end = self.n-1
        else:
            i_end = bisect_left(self.T, t_end)
        
        if i_end > self.n-1 or i_end < 0:
                i_end = self.n-1     
        
        if i_end <= i_start :
            print(f"ERREUR : La fin du sprint ne peut pas être avant le début")
            return
        
        # update self values and sprint arrays
        self.set_i_start_sprint(i_start)
        self.i_end_sprint = i_end

    def reset_sprint_bounds(self):
        """ Remet les valeurs calculés pour les bornes du sprint, sans recalculer le début
            Si cela a déjà ete fait.
        """
        
        # on ne relance pas les calculs pour i_sprint_start si ils ont déjà tourné
        if len(self.V_model_simp) > 0:
            i_start = self._get_start_next(self.i_start_v_model)
            self.set_i_start_sprint(i_start)
        else:
            self.find_sprint_start()
            
        self.find_sprint_end() # pas de calculs specifiques 

    def set_sprint_total(self):
        """ Case when sprint = all data """
        # default i_start is 0, OK
        # i_end must take all the data
        self.i_end_sprint = self.n - 1
        self.set_i_start_sprint(0)

    def plot_plateau(self):
    
        # V lissée pour la détection de v mesure max
        #plt.plot(self.T,self.V_smooth)
        plt.axhline(y=self.vs_max, linewidth=1,linestyle='--')
        #plt.axhline(y=self.v_max, linewidth=1,linestyle='--')
        
        # plot plateau
        plt.axvline(x=self.T[self.i_vs_max], linewidth=1)
        plt.axvline(x=self.T[self.i_start_plateau], linewidth=1) 
        plt.axvline(x=self.T[self.i_end_plateau], linewidth=1) 
   
    def plot_sprint(self):
    
        plt.plot(self.T_sprint, self.V_sprint, alpha=0.5)
        # plot i_start et i_end
        plt.axvline(x=self.T[self.i_end_sprint], linewidth=1)
        plt.axvline(x=self.T[self.i_start_sprint], linewidth=1)
        
    def plot_all(self):
        
        # donnnées brutes
        #plt.plot(self.T_in, self.V_in, alpha=0.3)
        plt.plot(self.T, self.V, alpha=0.5)
        plt.plot(self.T, self.V_smooth)
        
        if self.n>0 and not(self.data_error):
        
            # sprint
            #self.plot_sprint()
            plt.plot(self.T[self.i_start_sprint:self.i_vs_max+1], self.V[self.i_start_sprint:self.i_vs_max+1], alpha=0.5)
            # V smooth and plateau
             # V model if calculated
            if len(self.V_model_simp > 0):
                plt.plot(self.T_model, self.V_model_simp)
 
            plt.legend(('V mesure','V smooth','V sprint', 'V model'))
            
            #self.plot_plateau()
            plt.axvline(x=self.T[self.i_start_sprint], linewidth=1, label="start sprint")
          
            plt.axvline(x=self.T[self.i_vs_max], linewidth=1)
            plt.axvline(x=self.T[self.i_start_v_model], linewidth=1, linestyle='--')
            
            # pour la doc    
            #plt.xlabel('Time (s)')
            #plt.ylabel('Velocity (m/s)')
            #plt.text(self.T[self.i_vs_max +5],0,'end sprint')
            #plt.text(self.T[self.i_start_sprint +5],0,'start sprint')
            
                
            #V_smooth = lissage(self.V_in, self.SMOOTH_ITERATION)
            #plt.plot(self.T_in,V_smooth,color='r')

    #------------------ Methodes privées ------------------------------------------------
    def _get_sum_mean_distance(self,idx):
        """ Retourne la somme des carrés des distances à la moyenne à partir du premier 
        élément de self.V jusqu'à l'éléments idx inclus """

        sum = 0
        mean = self.V[:idx+1].mean()

        for i in range (0,idx+1): #idx+1 not included
            sum=sum+(self.V[i]-mean)**2

        return sum

    def _get_V_model(self, idx):
        """
        Returns V_model fonction whith a vmax_simp value that minimize the difference between V mesured and V_model.
        V_model is the model function f(ti) = vmax_gen*(1-np.exp((t_start-ti)/tau_gen)
        Applied to V and T values with i >= idx
        On ajuste vmax_gen parce que c'est rapide, on choisi un tau_gen un peu inf aux valeurs cibles pour être sur de pas
        Rater les démarrages
        TODO : faire les tests avec une v_model plus proche de la fonction visée, soit v_max(1-np.exp((t_start + delay - t)/tau))
           cf classe Sprint.
        """
        tau_gen = 0.8 # un peu plus raide que la moyenne pour être sur de ne pas rater le démarrage
        vmax_gen = 0

        T_sprint = self.T[idx:self.i_end_v_model+1]
        t_start=T_sprint[0]
        V_sprint=self.V[idx:self.i_end_v_model+1]
        
        # Fonction generique (ou fonction modèle)
        F = np.array([ (1-np.exp((t_start-ti)/tau_gen)) for ti in T_sprint ])

        # Calcul de vmax_gen. Cf les explications de stéphane L.
        vmax_gen=np.vdot(F,V_sprint)/np.linalg.norm(F)**2 
        #print(vmax_gen)

        # Apply vmax_gen to F
        V_model = vmax_gen*F
        return V_model, vmax_gen

    def  _get_sum_Vmodel_distance (self, idx):
        """ For index = idx, retuns the sum or the square differences between V and V model"""
        V_mesure = self.V[idx:self.i_end_v_model+1]
        V_model = self._get_V_model(idx)[0]
        return sum_distances(V_mesure,V_model)

  
    def _get_start_next(self, istart):
 		# The first start points velocities are modified by the parasite stop vitesse.
		# We want to keep only the acceleration points
		# Let's look at the xx points after i_start.
		# If Velocity(i+1) - Velocity[i]  > 0.1 OK, there is an acceleration
		# (empirically tested)
        # Since with floats 0.1 can be 0,099...998, let's use d >= 0.09
           
        #d_limit = 0.09 # pas tout à fait assez pentu
        d_limit = 0.1
        d = self.V[istart+1]-self.V[istart]
        i=0
        while (d <= d_limit and i<20):
            i+=1
            d = self.V[istart+i+1]-self.V[istart+i]
        return istart+i  
            
# ------ Main ---------------------------------------------------------------------------
if __name__ == "__main__":
    # execute only if run as a script : python radar_data.py
    # load file
    from radar_file import params_get_file

    # measure execution time
    import time

    # Debut du decompte du temps
    start_time = time.time()

    file = params_get_file()
    rd = build_RD_from_file(file)

    # tests
    #rd = build_RD_from_file(file, auto=False) # set sprint bounds manually
    #(Tsprint,Vsprint) = rd.extract_sprint()
    #rd.set_sprint_total()
    #rd.reset_sprint_bounds()
   
    load_time = time.time()
    print("Temps de chargement et d'initialisation: %s secondes ---" % (load_time - start_time))
    
    rd.plot_all()
    plt.title(f"{rd.title}")
    #plt.title(f"Sprint Février")
    plt.show()
    
    '''
    # measure execution time
    import time

    # Debut du decompte du temps
    start_time = time.time()
    
    load_time = time.time()
    print("Temps de chargement et d'initialisation: %s secondes ---" % (load_time - start_time))
    
    bound_time = time.time()
    print("Temps pour déterminer les bornes :  %s secondes ---" % (bound_time - load_time))
    '''
