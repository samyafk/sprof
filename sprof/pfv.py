# -*- coding: utf-8 -*
# python3
# Author : LJK - Laboratoire Jean Kuntzmann - C. Bligny
# Sources : Excel spreadsheets build by Pierre Samozino

"""
PFV Profiling Module

Given the velocity fucntion for a sprint, + some external parameters - athele mass
and stature, temperature, pression, this module computes somes significant
Power-Force-Velocity relationship values.

Sources for the calculus : The excel spreashit build by Pierre Samozino
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import logging
from sprof.sprint import build_sprint_from_file
from sprof.athlete import get_athlete_values
from sprof.utils import bisect_left

# ------ Builders -----------------------------------------------------------------------
def build_pfv_from_file(file, pression=760, outliers=True, auto=True):

        s = build_sprint_from_file(file, outliers=outliers, auto=auto)
        pfv=None
        if s:
            (mass,stature)=get_athlete_values(file)
            pfv = PFV(v_max=s.v_max, tau=s.tau, duration = s.duration, mass=mass, \
                                    stature=stature, pression=pression)

        return pfv

# ------ Class PFV (Power Force Velocity ) ----------------------------------------------
class PFV:
    """
    Power-Force-Velocity Profiling class
    """
    # Constants
    TIMEFRAME = 0.01 # s
    RF_TIME_START = 0.3 # Start time for RF calculation. cf Excel spreadsheet, ?

    # Default values
    #DEF_PRESSION = 1015 #hPa - Default pression
    DEF_PRESSION = 760 #hPa - Default pression
    DEF_TEMP = 20 # °C, default temperature
    DEF_STATURE = 1.90 # m. Default athlete size
    DEF_MASS = 100.0 # kg. Default athlete size
    DEF_DURATION = 5 # s. Default sprint duration

    # ------------- Data initialisation -------------------------------------------------
    def __init__(self, v_max=8.0, tau=1.0, mass=None, duration=None, stature=None,
        temp=None, pression=None, drag_coef=None, debug=False):
        """
        Class attributes
            scalars : v_max, tau, duration, mass, stature, temperature, pression
        	arrays : times, velocities, distances, forces, powers, RFs
        convention : array name are plural
        """

        # input attributes
        self.sprint=None # link with sprint
        self.v_max=v_max
        self.tau=tau
        self.mass=mass

        # sprint duration
        if duration:
        	self.duration=duration
        else:
        	self.duration=self.DEF_DURATION
        # temperature
        if temp:
        	self.temp=temp
        else:
            self.temp=self.DEF_TEMP
        #pression
        if pression:
        	self.pression=pression
        else:
        	self.pression=self.DEF_PRESSION
        # athlete size
        if stature:
        	self.stature=stature
        else:
        	self.stature=self.DEF_STATURE
        # athlete mass
        if mass:
        	self.mass=mass
        else:
        	self.mass=self.DEF_MASS
        # drag coef - (air friction impact)
        if drag_coef:
        	self.drag_coef=drag_coef
        else:
        	self.drag_coef=self.get_drag_coef()

        # attributes to be computed :
        self.F0=0
        self.V0=0.0
        self.Pmax=0
        self.F0_kg=0.0
        self.Pmax_kg=0.0
        self.sfv=0.0
        self.RF_peak=0.0
        self.DRF=0.0 # en %
        self.top_speed = 0.0 # velocity reached at the end of the sprint

        logging.debug(f"PFV - V max théorique = {self.v_max} s; constante d'accélération = {self.tau}")
        logging.debug(f"durée du sprint : {self.duration}")
        logging.debug(f"Athlète : {self.mass} kg, pour {self.stature} m")
        logging.debug(f"Température = {self.temp} °C, et pression = {self.pression} kPa")

        # init self.times
        self._init_times()

        if len(self.times)>0:

            # init other arrays : self.velocities, distances, forces, powers, RF
            self._init_arrays()

            # top speed
            if len(self.velocities) > 0:
                self.top_speed = self.velocities[-1]

            # Compute significant PFV values (= init computed values)
            self.compute_PFV_values()

            # time index for which we start the RF calculation
            #self.irf_start = self.get_iRF_start() # a calculer si besoin en fonction de timeframe et rf_time_start
            #print(self.irf_start)

    def _init_times(self):

        self.times = []
        # data check
        # les autres données participent au drag coef, s'il est nul ça doit passer
        if 0 in (self.v_max,self.tau,self.mass):
            print("ERREUR : une des valeurs d'initialisation est nulle ")
        else:
            self.times = np.arange(0, self.duration, self.TIMEFRAME, dtype=float)

    def _init_arrays(self):
        logging.debug("PFV - Initialisation des tableaux de valeurs ...")

        if len(self.times)==0:
            print("problème d'initialisation : les pas de temps sont vides")
        else:
            self._init_velocities()
            self._init_distances()
            self._init_HZT_forces()
            self._init_HZT_powers()
            self._init_RFs()

    def _init_velocities(self):
        """Calcul de la vitesse pour tous les pas de temps"""
        #self.velocity = np.array([ self.v_max*(1-np.exp(-t/self.tau)) for t in self.time ])
        self.velocities = np.array([ self.f_velocity(t) for t in self.times ])

    def _init_distances(self):
        """Calcul de la distance pour tous les pas de temps"""
        self.distances = np.array([ self.f_distance(t) for t in self.times ])

    def _init_HZT_forces(self):
        """Calcul de la force pour tous les pas de temps"""
        self.HZT_forces = np.array([ self.f_HZT_force_v(v) for v in self.velocities ])
        #self.HZT_forces = np.array([ self.f_HZT_force(t) for t in self.times ])
        self.HZT_forces_kg = np.array([ self.f_HZT_force_kg(t) for t in self.times ])

    def _init_HZT_powers(self):
        self.HZT_powers = np.array([ self.f_HZT_power(t) for t in self.times ])
        self.HZT_powers_kg = np.array([ self.f_HZT_power_kg(t) for t in self.times ])

    def _init_RFs(self):
        # RF : Force Ratio je crois.
        # self.RF = self.HZT_force/((self.HZT_force**2 + (self.mass*9.81)**2)**0.5)
        # on s'interesse au RF après 0,3 s de course, soit au 50eme point.
        # self.time_RF = np.array([ self.time(t) for t in self.time ])
        RF_times = self.times[self.get_iRF_start():]
        self.RFs = np.array([ self.f_RF(t) for t in RF_times ])

	# ------------- Functions -------------------------------------------------------

    def f_velocity(self, t):
        """ vitesse en fonction du temps au cours du sprint """
        return self.v_max*(1-np.exp(-t/self.tau))

    def f_distance(self,t):
        return (self.v_max*(t+self.tau*np.exp(-t/self.tau))-self.v_max*self.tau)

    def f_acceleration(self,t):
        """ accelération en fonction du temps au cours du sprint """
        return (self.v_max/self.tau)*np.exp(-t/self.tau)

    def f_acceleration_v(self,velocity):
        """ accelération en fonction de la vitesse au cours d'un sprint """
        return (self.v_max-velocity)/self.tau

    def f_air_friction(self, velocity):
        """ resistance de l'air en fonction de la vitesse"""
        # cf feuille excel
        #f = 0.5 * 1.293 * self.pression/760 * 273/(273+self.temp) * 0.2025 * self.stature**0.725 * self.mass**0.425 * 0.266 * 0.9 * velocity**2
        return self.drag_coef * velocity**2
        # deuxième calcul, d'après la feuille exel ...

    # HZT stands for "horizontal"
    def f_HZT_force(self,t):
        """ Calcul de la force horizontale déployée au cours du sprint """
        velocity=self.f_velocity(t)
        #force = self.f_air_friction(velocity) + self.f_acceleration(t) * self.mass
        force = self.f_air_friction(velocity) + self.f_acceleration_v(velocity) * self.mass
        #force = self.f_acceleration(t) * self.mass
        return force

    # HZT stands for "horizontal"
    def f_HZT_force_v(self,velocity):
        """ Calcul de la force horizontale déployée au cours du sprint """
        force = self.f_air_friction(velocity) + self.f_acceleration_v(velocity) * self.mass
        return force

    def f_HZT_force_kg(self,t):
        """ Force horizontale déployée au cours du sprint par unité de masse
        Si la friction de l'air était négligeable, ce serait eq à l'accelération,
        et indépendant de la masse"""
        velocity=self.f_velocity(t)
        # return self.f_HZT_force(t) / self.mass
        return self.f_acceleration(t) + self.f_air_friction(velocity)/self.mass

    def f_HZT_power(self,t):
        """ Puissance horizontale au cours du sprint"""
        return self.f_velocity(t) * self.f_HZT_force(t)

    def f_HZT_power_kg(self,t):
        """ Puissance horizontale au cours du sprint par unité de masse
        Si on néglige la friction de l'air, indépendant de la masse"""
        return self.f_velocity(t) * self.f_HZT_force_kg(t)

    def f_force_all(self,t):
        """ Force totale, composante de 2 forces : accélération (HZT_force) et résistance à la pesanteur"""
        return (self.f_HZT_force(t)**2 + (self.mass*9.81)**2)**0.5

    def f_RF(self,t):
        """ Ratio de la force horizontale par rapport aux forces totales"""
        return(self.f_HZT_force(t)/self.f_force_all(t))


	# ------ Public methods  ------------------------------------------------------------

    def compute_PFV_values(self, t_start=None, t_end = None):
    #def extract_values(self, t_start=0.199, t_end = 4.5):

        # NB : function force(vitesse) contains also air friction, which is not linear.
        # --> t_start et t_end impacts the computed slope

        i_start=0
        i_end=len(self.times)-1

        if t_start:
            if (t_start > self.times[0]):
                i_start= bisect_left(self.times, t_start)
            else:
                print(f"WARNING : t_start < times[0]")
        if t_end:
            i_end= bisect_left(self.times, t_end)

        logging.debug("Calcul du profil Force/Vitesse (pente), de F0 et de V0")

        slope, intercept, r_value, p_value, std_err = linregress(self.velocities[i_start:i_end],self.HZT_forces[i_start:i_end])
        self.sfv = slope # slope of the force - vitesse line
        self.F0 = intercept
        self.V0 = -self.F0/self.sfv
        logging.debug(f"V0 : {self.V0}")
        logging.debug(f"F0 : {self.F0}")
        logging.debug(f"sfv (Pente) : {self.sfv}")

        '''
        print("test avec calcul direct : ")
        # Donne pas les mêmes valeurs que linregress car ce n'est pas tout à fait une
        # droite : le frottement de l'air est proportionnel à la vitesse au carré
        self.Svf=(self.HZT_force[-1]-self.HZT_force[0])/(self.velocity[-1]-self.velocity[0])
        self.F0 = self.HZT_force[0]
        self.V0 = -self.F0/self.Svf
        print(f"V0 : {self.V0}")
        print(f"F0 : {self.F0}")
        print(f"sfv (Pente) : {self.Svf}")
        '''

        self.F0_kg=self.F0/self.mass

        logging.debug("Calcul de la puissance max")
        # get pmax : max de self.HZT_power_kg
        self.Pmax_kg = np.amax(self.HZT_powers_kg)
        #self.Pmax = self.F0*self.V0/4/self.mass
        logging.debug(f"Pmax par kg : {self.Pmax_kg}")
        self.Pmax = np.amax(self.HZT_powers)
        logging.debug(f"Pmax : {self.Pmax}")

        logging.debug("Donnees relative a RF")
        self.RF_peak=np.amax(self.RFs)
        logging.debug(f"RF peak : {self.RF_peak}")
        DRF, RF_max, r_value, p_value, std_err = linregress(self.velocities[self.get_iRF_start():],self.RFs)
        self.DRF = DRF*100 # le self.DRF est en %
        logging.debug(f"DRF : {self.DRF}")
        logging.debug(f"RF max th : {RF_max}")

        print(f"PFV, valeurs caractéristiques :")
        print(f"\tP max = {self.Pmax_kg:.2f} W/kg, V0 = {self.V0:.2f} m/s, F0 = {self.F0_kg:.2f} N/kg (soit {self.Pmax:.2f} W et {self.F0:.2f} N pour une masse de {self.mass} kg)")

    def get_drag_coef(self):
        """ Returns the drag coef used for the air friction impact.
        air friction = drag coef * velocity**2
        Depends on the athlete and day characteristics.
        WARNING : wind is not used here. (Sprints are currently run inside).
        """
        coef = 0.5 * 1.293 * self.pression/760 * 273/(273+self.temp) * 0.2025 * self.stature**0.725 * self.mass**0.425 * 0.266 * 0.9
        return coef

    #def set_slope_bounds(self,t_start,t_end):
    def get_iRF_start(self):
    	# Start RF calculation at 0.3 s. (?)
        return int(self.RF_TIME_START/self.TIMEFRAME)

    def get_mean_RF(self, distance):
        """ Returns mean RF
        """
        # get indice for distance juste before distance (m)
        i= bisect_left(self.distances, distance)

        # note : timeframe is smaller than timeframe in the spreadsheet --> result slighly
        # different
        #print(self.time[i])

        return self.RFs[0:i-self.get_iRF_start()].mean()

    def get_time(self,velocity=None,distance=None):
        """Retuns time for given velocity or distancce.
        This works for numerical increasing arrays"""
        i=None
        t=None

        if velocity:
            if distance:
                print("ERREUR : methode get_time, il faut fournir soit la vitesse, soit la distance")
            else:
                if velocity <= self.velocities[-1]:
                    i = bisect_left(self.velocities, velocity)

        if distance:
            if distance <= self.distances[-1]:
                i = bisect_left(self.distances, distance)

        if i is not None:
            t = self.times[i]

        return t

    def print_data(self):
        '''
        Print the data.

        Excel spreadsheet order:
        Physical qualities
        Mass (kg)	Vmax theoretical V0 (m/s)	Fmax theoretical F0   (N)	Fmax theoretical F0 (N/kg)	Pmax (W)
        Max Horizontal Power Pmax (W/kg)	Force-Velocity profile
        Mechanical effectiveness
        mean RF on 10m	RFpeak	DRF
        Performances during accélération
        Time @ 5 m (s)	Time @ 10 m (s)	Time @ 20 m (s)	Time @ 30 m (s)	Time @ 40 m (s)
        Distance in 2 s (m)	Distance in 4 s (m)
        Top speed (m/s)
        Acceleration time constant (s)
        '''
        if len(self.times)>0:
            print("\n---- Results ------")
            print(f"Sprint duration\t\t{self.duration:.2f} s")
            print(f"Top speed reached\t{self.top_speed:.2f} m/s")
            print(f"Sprint distance\t\t{self.distances[-1]:.2f} m")
            print(f"Acc. time constant\t{self.tau:.2f}")
            print(f"V max theorical\t\t{self.v_max:.2f} m/s")
            print(f"-- Physical qualities")
            print(f"{4*' '}Mass\t{self.mass} \tkg")
            print(f"{4*' '}Stature\t{self.stature} \tm")
            print(f"{4*' '}Coef air friction\t{self.drag_coef:.2f} (pression : {self.pression} hPa, temp : {self.temp} °C, no wind)")
            print(f"-- PFV Profile")
            print(f"{4*' '}V0\t\t{self.V0:.2f}\tm/s\ttheorical max Velocity")
            print(f"{4*' '}F0/kg\t{self.F0_kg:.2f}\tN/kg\tForce Max theorical per kg")
            print(f"{4*' '}F0\t\t{self.F0:.2f}\tN\ttheorical max Force")
            print(f"{4*' '}P max/kg\t{self.Pmax_kg:.2f}\tW/kg\tmax Horizontal Power per kg")
            print(f"{4*' '}P max\t{self.Pmax:.2f}\tW\tmax Horizontal Power")
            print(f"{4*' '}FV profile\t{self.sfv:.2f}\t\tForce-Velocity profile (pente)")
            print("-- Mechanical effectiveness")
            print(f"{4*' '}Mean RF 10m\t{self.get_mean_RF(10):.2f}")
            print(f"{4*' '}RF Peak\t{self.RF_peak:.2f}")
            print(f"{4*' '}DRF\t\t{self.DRF:.2f} %")
            print("-- Performances during acceleration")
            self._print_time_distance((5,10,20,25,30))
            self._print_distance_time((2,4))

        else:
            print("les données n'ont pas été initialisées correctement")
        # En combien de temps on atteint x% de la v max ?
        '''
        x=95
        v_limit=x*self.v_max/100
        if (v_limit < self.top_speed):
            print(f"{x}% de la v_max atteints en {self.get_time(velocity=v_limit):.2f} s")
        else:
            print(f"{x}% de la v_max non atteints")
		'''

    def str_time_distance(self,distance):
        str_time=""
        time = self.get_time(distance=distance)
        if time:
            str_time = f"{time:.2f}"
            #print(f"{4*' '}Time @ {dist}m\t{time:.2f} s")
        return str_time

    def str_distance_time(self,time):
        str_dist=""
        if time < self.duration:
            dist=self.f_distance(time)
            str_dist=f"{dist:.2f}"
        return str_dist

    def _print_time_distance(self,distances):
        for dist in distances:
            time = self.get_time(distance=dist)
            if time:
                print(f"{4*' '}Time @ {dist}m\t{time:.2f} s")
            else:
                print(f"{4*' '}Time @ {dist}m\tTemps non trouvé")

    def _print_distance_time(self,times):
        for time in times:
            if time < self.duration:
                dist=self.f_distance(time)
                print(f"{4*' '}Distance in {time}s\t{dist:.2f} m")
            else:
                print(f"{4*' '}Distance in {time}s\tDistance non trouvée")


    def simp_vars(self):
        """
        Returns a dictionnary with the class atributes, wihout the arrays, and with
        float values rounded
        Does not contain computed attributes
        """
        dict = vars(self)
        dict = {k:v for (k,v) in dict.items() if not isinstance(v,np.ndarray)}
        dict = {k:round(v,2) if isinstance(v,float) else v for (k,v) in dict.items()}
        return dict

# ------ Main ---------------------------------------------------------------------------
if __name__ == "__main__":
    """ Tests, examples
    """
    from sprof.radar_file import params_get_file

    def get_alex2_prof():
        # Use same values that for Alexandre 2_SimpleMethodSprint_V14_mps.xlsm
        # spreadsheet, in order to compare output values
        tau = 1.15758375049727
        vmax = 8.22437782527865
        duration = 4.93
        mass=100
        stature=1.86
        pression=760

        p = PFV(v_max=vmax, tau=tau, duration = duration, mass=mass, \
                                    stature=stature, pression=pression)

        return p

    def validation():
        """
        Validation test for PFV calculated values : compare with spreadsheet
        Alexandre 2_SimpleMethodSprint_V14_mps.xlsm - July sprint.
        """
        print("\n=============== START TEST PVF =====================")

        p = get_alex2_prof()
        p.print_data()

        # BILAN des lègères différences - mais c'est OK
        # 1) calcul de la pente, sfv qui n'est finalement pas une droite - ça depend si on
        # prend le début ou pas, et diff de calcul excel/python
        # 2) distance à 2 ou 4 secondes : dans excel, recherche de la valeur la plus
        # proche dans le tableau, alors que ici on utilise la fonction distance

        # Bien vérifier que le drag coef est le même, sinon ça modifie les résultats

    def validation_points():
        """
        Validation des calculs des fonctions (vitesse, distance, force ...) pour qq points
        Comparaiston avec la feuille excel Alexandre 2_SimpleMethodSprint_V14_mps.xlsm
        des sprint de juillet
        """
        # test calculs pour un point donné - vérification pour alexandre 2
        # FVP(v_max=r.Vmax, tau=r.tau, stature=1.86, mass=100, temp=20, pression=760)

        p = get_alex2_prof()

        delai = -0.177405773298039
        t8_init = 0.128
        t8 = t8_init - delai
        print("\n=============== Point test =====================")
        print("Test des valeurs ligne 8 pour alexandre 2 - Vérifier la justesse des calculs")
        print(f"t8 - délai : {t8}")
        print(f"Vitesse : {p.f_velocity(t8)} m/s")
        print(f"Distance : {p.f_distance(t8)} m ")
        print(f"Accélération : {p.f_acceleration(t8)} m/s²")
        print(f"Force horizontale : {p.f_HZT_force(t8)} N")
        print(f"Force horizontale par kg: {p.f_HZT_force_kg(t8)} N/kg")
        print(f"Puissance horizontale : {p.f_HZT_power(t8)} W")
        print(f"Puissance horizontale par kg: {p.f_HZT_power_kg(t8)} W/kg")
        print (f"Forces totales : {p.f_force_all(t8)} N")
        print(f"RF - Ratio force Horizontale / forces totales : {p.f_RF(t8)}")


    def print_pfv():
        print("\n=============== FILE TEST =====================")
        file = params_get_file()
        pfv = build_pfv_from_file(file, auto=True, outliers=True)
        if pfv:
            pfv.print_data()
        else:
            print("Erreur sur les données. Impossible d'afficher le profil PFV")

    #validation_points()
    #validation()
    print_pfv()
