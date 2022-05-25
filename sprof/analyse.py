# -*- coding: utf-8 -*
# python3
# Author : LJK - Laboratoire Jean Kuntzmann - C. Bligny
"""
Fonctionnalities that simultaneously use main classes : radar_file, radar_data, sprint, pfv 
"""
# Replace in a next step by adding inter-classes links?

from sprof.radar_file import RadarFile
from sprof.radar_data import RadarData
from sprof.sprint import Sprint
from sprof.pfv import PFV
from sprof.athlete import get_athlete_values
from sprof.utils import bisect_left

import matplotlib.pyplot as plt

# ------ Analyse Builder ----------------------------------------------------------------
def build_analyse_from_file(file, auto=True, outliers=True, pression=None, temp=None):
    a=None
    rf = RadarFile(file)
    rd = RadarData(rf.T,rf.V,rf.title, auto=auto)
    
    if not(rd.data_error):
    
        (Tsprint,Vsprint)=rd.extract_sprint()
        s = Sprint(Tsprint, Vsprint, rd.title, outliers=outliers)
    
        # Get athlete stature and mass
        # Faire une fonction dans 
        (mass,stature)=get_athlete_values(file)
    
        pfv = PFV(v_max=s.v_max, tau=s.tau, duration = s.duration, mass=mass, \
                                    stature=stature, pression=pression,temp=temp)
                                
        a=Analyse(radar_file=rf,radar_data=rd,sprint=s,pfv=pfv)
    
    return a

# ------ Analyse Class ------------------------------------------------------------------   
class Analyse:
    
    def __init__(self, radar_file=None, radar_data=None, sprint=None, pfv=None):
        
        self.radar_file=radar_file
        self.radar_data=radar_data
        self.sprint=sprint
        self.pfv=pfv  
        
        # data quality .  
        self.plateau_duration= round(self.sprint.plateau_duration,2)
        self.points_out=self.sprint.n_out
        self.vmax_diff=round(self.sprint.v_max-self.sprint.vs_max,2)

        # Pas utilisé pour le moment, test.
        # on pourrait directement récupérer l'erreur de scipy lors de calcul de vmodel
        # mais là, c'est rapide à placer    
        # Cas des les sprinteurs démarrant un peu plus lentement - v smooth et v model
        # plus éloignés en début de course? 
        # Voir avec l'expérience quelles sont les seuils critiques 
        # ou ((self.sprint.V_model-self.sprint.V_sprint_acc)**2).mean() ? 
         # moyenne des carrés des ecart entre v th et v smooth
        self.curves_gap=((self.sprint.V_model-self.sprint.V_smooth[0:self.sprint.i_end_acc+1])**2).mean()

    # needs radar_data and sprint
    def plot_normalize(self):
        # same scale for all plots
        # v from 0 to 10 m/s
        # t from i start -1 to i start + 6

        rd = self.radar_data
        s = self.sprint

        # some checks
        if (rd.data_error==False and s.n>0 and len(self.pfv.times)>0):

            plt.ylim(0,11)
            plt.xlim(-1,6)

            # on fait démarrer le sprint à T=0
            T=s.shift_time(rd.T)
            T_sprint=s.shift_time(s.T_sprint)
            T_sprint_acc=s.shift_time(s.T_sprint_acc)
            
            plt.plot(T, rd.V, alpha=0.5)
            plt.plot(T_sprint_acc, s.V_sprint_acc, alpha=0.5, color='b')

            # V lissée pour la détection de v mesure max et plateau
            plt.plot(T_sprint,s.V_smooth,color='g')
            
            # plot  V model for the acceleration portion
            plt.plot(T_sprint_acc, s.V_model, color='r')
            
            #V mesure max and v max thorical
            plt.axhline(y=s.vs_max, linewidth=1,linestyle='--', color='g')
            plt.axhline(y=s.v_max, linewidth=1,linestyle='--', color='r')
            #plt.axhline(y=0, linewidth=1,linestyle='--')
            
            # plot start sprint
            t_start_sprint=s.shift_time(s.T_sprint[0])
            plt.axvline(x=t_start_sprint, linewidth=1, linestyle='--')
            #plt.axvline(x=0, linewidth=1, linestyle='--')   
            
            # plot end plateau = i end acc et i start plateau
            t_end_plateau=s.shift_time(s.T_sprint[s.i_end_plateau])
            plt.axvline(x=t_end_plateau, linewidth=1, linestyle='--',color='g')
            t_start_plateau=s.shift_time(s.T_sprint[s.i_start_plateau])
            plt.axvline(x=t_start_plateau, linewidth=1, linestyle='--',color='g')  
            
            # plot v max - ou pas
            t_vs_max= s.shift_time(s.T_sprint[s.i_vs_max])   
            #plt.axvline(x=t_vs_max, linewidth=1, linestyle='--')   
            
            # print model velocity
            # build and plot V model therical = from T=0 to end sprint
            i_start_th=bisect_left(T, 0)
            T_sprint_th = T[i_start_th:rd.i_end_sprint+1]
            V_model = s._f_velocity(rd.T[i_start_th:rd.i_end_sprint+1])
            plt.plot(T_sprint_th, V_model,linestyle='--', color='r')
            
            # plot V max (theorical)s
            plt.title(f"{rd.title}")
            
            # pour doc
            #plt.title(f"test 1")
            #plt.xlabel('Time (s)')
            #plt.ylabel('Velocity (m/s)')
            #plt.text(-0.9,8.1,'v max reached',color='g')
            #plt.text(-0.9,8.8,'v max theorical',color='r')
            #plt.text(3.7,0.2,'<--- plateau --->',color='g')
                  
            plt.grid()    
    
    def print_data_quality(self):

            signal_quality='BON'
            if self.sprint.n_out > 2:
                signal_quality='CORRECT'
            if self.sprint.n_out > 6:
                signal_quality='PASSABLE'
            if self.sprint.n_out > 10:
                signal_quality='MEDIOCRE'
            if self.sprint.n_out > 15:
                signal_quality='MAUVAIS'             
            
            print("\n---- Data quality ------")
            # En fct nb point aberrants : qualité signal
            print(f"{4*' '}Signal : {signal_quality}  - {self.sprint.n_out} points enlevés")
            
            # ecart V moyenne et V model : qualité & durée de l'acceleration
            #print(f"{4*' '}Ecart courbes : {self.curves_gap*100:.2f} .10^2")        
            # durée plateau : mesure totale de l'acceleration
            end_acc=self.sprint.plateau_duration
    
            print(f"{4*' '}Durée plateau {self.plateau_duration:.2f} s, Ecart vmax mesurée et vmax th {self.vmax_diff}")
                        
            if self.vmax_diff <= 0.5 and end_acc >= 0.9:
                # si mean_gap < ... and vmax_dif < ... and plateau > ...
                print(f"{4*' '}Le sprint à l'air OK")
            
            else:
                print(f"{4*' '}Sprint, à VERIFIER :")
                if self.vmax_diff > 0.5:
                    print(f"{6*' '}Ecart entre vmax mesurée et vmax th > 0.5") 
                if end_acc < 0.9:
                    print(f"{6*' '}Durée plateau < 0.9 s) ")        

                            
    # pour cette methode, il faut p, mais aussi s
    def print_analyse(self):
        self.pfv.print_data()
        self.print_data_quality()

    def plot_analyse(self):
        plt.figure(figsize = (9, 7))
        self.plot_normalize()
        plt.legend(('V mesure','V sprint','V smooth', 'V model'))
        plt.show()
                  
    def get_quality(self):
        vmax_diff=round(self.sprint.v_max-self.sprint.vs_max,2)
        return(self.sprint.title,round(self.sprint.plateau_duration,2),vmax_diff)
        #print(f"{self.sprint.title}, plateau : {self.sprint.plateau_duration:.2f}, Ecart : {vmax_diff}")
        
# ------ Main ---------------------------------------------------------------------------
if __name__ == "__main__":

    from radar_file import params_get_file, params_get_files
    
    def analyse_one():
        file = params_get_file() 
    
        if file:    
            a=build_analyse_from_file(file)
            if a:
                a.print_analyse()
                a.plot_analyse()
        else:  
            print("Pas de fichier radar trouvé correspondant aux paramètres fournis")

    def analyse_many():
        files = params_get_files() 
        table=(('sprint title','plateau duration','v max diff'),)
        for file in files:
            a=build_analyse_from_file(file)
            if a:
                res=a.get_quality() 
                table+=(res,) 
        for res in table:
            print(f"{res[0]}\t{res[1]}\t{res[2]}")
        
    #analyse_many() 
    analyse_one()