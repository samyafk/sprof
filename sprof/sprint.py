# -*- coding: utf-8 -*
# python3
# Author : LJK - Laboratoire Jean Kuntzmann - C. Bligny
"""
	Sprint class
	input : times and velocities arrays for the sprint (namely T sprint and V sprint)
	Remove point outliers, search for and accurate end acceleration time
	compute tau, vmax, delay
	prepare plots
	The velocity fonction f, related to time t during the sprint acceleration is :
	    f(t) = v_max * ( 1-exp(-t/tau) )
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import leastsq
from scipy import signal
from sprof.radar_data import build_RD_from_file, build_RD_from_pattern
import pandas as pd
import logging
from sprof.utils import print_obj_attr, get_iprevious, get_inext, bisect_left

def build_sprint_from_file(filename, outliers=True, auto=True):
    """
    Build and returns a Sprint instance, using a radar data file.
    """
    rd = build_RD_from_file(filename,auto=auto)
    return build_sprint_from_RD(rd,outliers=outliers,auto=auto)


def build_sprint_from_pattern(dir="", pattern="",ext="", auto=True, outliers=True):
    """
    Build and returns a RadarData instance, using a pattern for the radar data file.
    Search done in the default radar data dir
    """
    rd=build_RD_from_pattern(dir=dir, pattern=pattern,ext=ext, auto=auto)
    return build_sprint_from_RD(rd,outliers=outliers,auto=auto)

def build_sprint_from_RD(radar_data, outliers=True, auto=True):
    """
    Build and returns a Sprint instance, using a radar data instance.
    """
    #rd = build_RD_from_file(filename,auto=auto)
    s=None
    if radar_data and not radar_data.data_error:
        (Tsprint,Vsprint)=radar_data.extract_sprint()
        if len(Tsprint) > 0:
            s = Sprint(Tsprint, Vsprint, radar_data.title, outliers=outliers)
            if not(auto):
                s.reset_end_acc()
    return s

class Sprint:
  
    # Computation constants. empirical values, tests on july data
    VGAP_LIMIT = 3
    WEIGHTED_VGAP_LIMIT = 3 #  v diff ponderee par 1/(racine de la pente)
    VMAX_DIFF_RATIO = 0.5 # %
    TAU_DIFF_RATIO = 2.5 # %
    PLATEAU_RATIO = 0.02
    
    def __init__(self, T_sprint, V_sprint, title="", outliers=True):
        """Class Attributes. 
           Convention : for velocity (v, V) and time (T, t), Arrays/Vectors starts 
           with uppercase, scalar with lowercase
        """

        # input Datas
        self.T_sprint_in = np.array([],dtype='float')# np array
        self.V_sprint_in = np.array([],dtype='float') # np array    
        self.title=title
        
        #Calculated datas
        self.V_smooth=np.array([],dtype='float')
        self.i_end_acc = 0 # fin du sprint
        
        # Datas eventually without outliers
        self.T_sprint = np.array([],dtype='float')# np array
        self.V_sprint = np.array([],dtype='float') # np array   
        self.n_out = 0 # number of points removed 

        # Values to extract :
        self.v_max = 0.0    # max velocity
        self.tau = 0.0 
        self.delay = 0.0    # TIme delay before first sprint data
        self.V_model = np.array([],dtype='float') # Theorical velocity for the sprint 

        # Check input datas
        if len(V_sprint)!=len(T_sprint):
            print("Erreur : les tableau d'entrée ne sont pas de la même taille")  
        elif len(V_sprint)==0:
            print("Erreur : les données sont vides")
        else:
            # Datas
            # _in as input : unchanged arrays.
            self.T_sprint_in = np.array(T_sprint, dtype='float') # Time array
            self.V_sprint_in = np.array(V_sprint,dtype='float') # Velocity array 
            self.T_sprint = np.copy(self.T_sprint_in)
            self.V_sprint = np.copy(self.V_sprint_in)
            self.i_end_acc = self.n-1
            self._init_V_smooth(outliers)
            #self._init_params(outliers)
            self._init_V_model(outliers)
            
        logging.debug(f"Sprint initialisé avec {self.n} points")

    @property
    def T_sprint_acc(self):
        return self.T_sprint[0:self.i_end_acc+1]
    
    @property  
    def V_sprint_acc(self):
        return self.V_sprint[0:self.i_end_acc+1]

    @property
    def n(self):
        return len(self.T_sprint)
    
    # debut du sprint, légèrement inférieur aux mesures généralement
    @property
    def t_model_start(self):
        if self.n > 0:
            return self.T_sprint[0] + self.delay
        else:
            return None
        
    @property
    def t_end(self):
        if self.n > 0:
            return self.T_sprint[self.i_end_acc]
        else:
            return None
            
    @property
    def i_vs_max(self):
        return np.argmax(self.V_smooth)
        
    @property   
    def vs_max(self):
        return self.V_smooth[self.i_vs_max]

    @property
    def plateau_duration(self):
        return self.T_sprint[self.i_end_plateau]-self.T_sprint[self.i_start_plateau]

    @property
    def plateau_duration_sup(self):
        return self.T_sprint[self.i_end_plateau]-self.T_sprint[self.i_vs_max]

    '''
    @property
    def v_max_measure(self):
        if len(self.V_smooth) > 0:
            i_v_max = np.argmax(self.V_smooth)
            return self.V_smooth[i_vs_max]
        else:
            return None
    '''
    
    # 2 possibilities : duration of sprint data record, or duration of sprint
    # duration of sprint record = self.t_end - self.t_start
    # duration of sprint =  self.t_end - self.t_model_start (inclu le delai)
    @property
    def duration(self):
        #return self.t_end - self.t_start # t
        if self.n > 0:
            return self.t_end - self.t_model_start
        else:
            return None
            
    #-------------------- Init computed attributes --------------------------------------

    def _init_V_smooth(self, outliers=True):
    
        # calcul de V smooth, en enlevant/remplaçant les points aberrants par défaut
        # c'est à dire ceux éloignés de plus de 3 de v_smooth

        limit=3 # empirique. On peut affiner 

        if outliers:
            V_smooth = self._smooth(self.V_sprint)
            n_out1=0
            n_out2=0
            n_out1 = self._remove_outliers_abs(self.V_sprint, V_smooth,limit)
            #print(n_out1)
            # 2eme passe
            if n_out1>0:
                V_smooth = self._smooth(self.V_sprint)
                n_out2 = self._remove_outliers_abs(self.V_sprint,V_smooth,limit)

            logging.debug(f"Outliers / V smooth, {n_out1+n_out2} points enlevés")

        # check last point
        # si dernier point abbérant, c'est problématique. 
        # vérif : i_end plateau avec un point en moins doit être pareil, 
        # ou v(-1) et v(-2) trop diff. 
        # attention que ça peut être l'avant dernier point qui est aberrent
        # on compare le dernier à la moyenne des 3 dernier par ex?
        # question résolue dans radar_data.py, extract sprint : on remplace la dernière
        # valeur de V_sprint par celle de V_smooth
        
        self._set_V_smooth()
    
        #logging.debug(f"Durée plateau : {self.plateau_duration:.2f} s")
        # a afficher après le retrait des points aberrants
    
    def _set_plateau(self):
    
        ratio = self.PLATEAU_RATIO
    
        self.i_start_plateau = get_iprevious(self.V_smooth, self.i_vs_max, ratio)
        self.i_end_plateau = get_inext(self.V_smooth, self.i_vs_max, ratio)

        if self.i_start_plateau is None:
            self.i_start_plateau=self.i_vs_max
        if self.i_end_plateau is None:
            self.i_end_plateau=self.i_vs_max 
     
    def _remove_outliers_abs(self, V_mesure, V_model, limit):
        vgaps=abs(V_mesure - V_model)   
        return self._remove_outliers(vgaps,limit)
     
    def _remove_outliers_weighted(self, V_mesure, V_model, T, limit): 
        #vgaps=abs(V_mesure - V_model)
        # on a besoin de t pour la pente .
        vgaps = abs(V_mesure-V_model)[1:]*(np.diff(T)/np.diff(V_model))**(1/2)
        # For the first one (or last one), there is no slope . Furthermore, we don't 
        # want to remove the first point
        # --> let's add a 0 gap for the first point.
        vgaps = np.concatenate(([0.0], vgaps)) 
        
        return self._remove_outliers(vgaps,limit)
          
    def _remove_outliers(self, vgaps, limit):

        #vgaps=abs(V_mesure - V_model)
        
        # on enlève tous les points avec un écart > 3
        boolArr = (vgaps >= limit)
        indexArr = np.argwhere(boolArr)
        nout=len(indexArr)
        #print(f"Nombre points enlevés : {len(indexArr)}")
        if nout > 0:
            self.V_sprint=np.delete(self.V_sprint,indexArr)
            self.T_sprint=np.delete(self.T_sprint,indexArr)
            self.n_out+=nout
            #self.V_smooth = self._smooth(self.V_sprint)
        return nout

    def _set_V_smooth(self):
        #logging.debug(f"Sprint - Set V Smooth")
        self.V_smooth = self._smooth(self.V_sprint)
        self._set_plateau()
        self._set_end_acc()
        
    def _set_end_acc(self):
        self.i_end_acc=self.i_end_plateau
    
    def _init_V_model(self, outliers=True):
    
        logging.debug(f"Sprint - Init V model")
    
        # premier calcul des param et vmodel
        self._set_V_model()

        # remove outliers --> mise à jour éventuelle des attributs T_sprint et V_sprint
        
        if outliers:

            #self.n_out = self._remove_outliers()
            
            # 1) remove points too far from smooth velocity
            
            # Compare difference between V_sprint (V measure) and V_model
            n_v_smooth_out=self.n_out
            n_vgap_out = self._remove_outliers_abs(self.V_sprint_acc, self.V_model, self.VGAP_LIMIT)
            if n_vgap_out>0:
                self._set_V_smooth()
                self._set_V_model()
            
            # Compare V_sprint and V_model, but weighted by the slope
            n_weigthed_vgap_out=0
            #weigthed_vgaps = self._get_weighted_vgaps()
            #n_weigthed_vgap_out = self._remove_farthest_points(weigthed_vgaps, self.WEIGHTED_VGAP_LIMIT) 
            n_weigthed_vgap_out = self._remove_outliers_weighted(self.V_sprint_acc, self.V_model, self.T_sprint_acc, self.WEIGHTED_VGAP_LIMIT)
            if n_weigthed_vgap_out>0:
                self._set_V_smooth()
                self._set_V_model()
            
            
            '''
            # tend to lower F0 compare to manual results --> let's comment below outliers
            
            # 2 - Impacting points - Remove the farthest points if they are impacting.
            n_impact_vgap_out=0
            n_impact_weighted_vgap_out=0
            # absolute distance
            vgaps=abs(self.V_sprint_acc - self.V_model)
            n_impact_vgap_out = self._remove_impact_points(vgaps)
            
            # distance weighted by slope
            weigthed_vgaps = self._get_weighted_vgaps()
            n_impact_weighted_vgap_out = self._remove_impact_points(weigthed_vgaps)
 
            n_far_out = n_v_smooth_out+n_vgap_out
            n_impact_out = n_impact_vgap_out+n_impact_weighted_vgap_out
    
            n_total=n_vgap_out+n_weigthed_vgap_out+n_impact_vgap_out+n_impact_weighted_vgap_out
            '''
            
            n_far_out = n_v_smooth_out+n_vgap_out
            print(f"Outliers points. Trop loin : {n_far_out}, Trop loin / pente : {n_weigthed_vgap_out}")            
        
        print(f"Sprint Initialisé. V max = {self.v_max:.2f}, tau = {self.tau:.2f}, durée de l'accéleration : {self.duration:.2f} s")
        print(f"{self.n_out} points enlevé(s), durée plateau : {self.plateau_duration:.2f} s")


    def _set_V_model(self):
        """
        init attributs v_max, tau, delay, V_model from T_sprint and V_sprint
        """
        #logging.debug(f"Sprint - Set V model")
        (v_max, tau, delay) = self.compute_f_velocity_params(self.T_sprint_acc, self.V_sprint_acc)
        self.v_max = v_max
        self.tau = tau
        self.delay = delay
        self.V_model = self._f_velocity(self.T_sprint_acc)
        
        # Recherche optimum de v_end, à creuser. Minimise erreur?
        # minimise distance entre v_smooth (v mesure) et v_model?
        # tests. get erreur python, calcule la distance

    def _smooth(self, V):
        # lissage moins lisse, pour garder la chute, au plus proche de _lissage
        b2, a2 = signal.butter(1, 0.036, 'low', analog=False)
        # pour lisser le lissage moins lisse
        b3, a3 = signal.butter(2, 0.05, 'low', analog=False)
        V_smooth = signal.filtfilt(b2, a2, V,padlen=25) 
        # padlen : 1er et derniere valeur non lissée (pas parfait pour la dernière)
        V_smooth = signal.filtfilt(b3, a3, V_smooth) #method='gust'
        return V_smooth
     
    def _remove_point(self,i_remove):
        """ Remove one point from sprint. Update v_smooth and v_model
        """
        # Remove point from Sprint arrays
        self.V_sprint = np.delete(self.V_sprint ,i_remove)
        self.T_sprint = np.delete(self.T_sprint, i_remove)
        self.n_out+=1
        # Update computed attributes : v_max, tau, delay and V_model
        self._set_V_smooth()
        #self._init_f_velocity_params()
        self._set_V_model()
            
    def _remove_farthest_points(self, gaps, gap_limit):
        """
        Enleve les points trop éloignés (en recalculant v_smooth et v_model a chaque pas)
        mais c'est qu'à moitié juste car on ne recalcule pas le gap
        """
        
        # get first farthest point
        i_max_gap = np.argmax(gaps)
        gap = gaps[i_max_gap]
        nb_i_out = 0
        
        # Remove all points farther than gap limit
        while gap >= gap_limit:
            self._remove_point(i_max_gap)
            gaps = np.delete(gaps, i_max_gap)
            i_max_gap = np.argmax(gaps)
            gap = gaps[i_max_gap]
            nb_i_out+=1
        
        return nb_i_out
        
    def _remove_impact_points(self, gaps, n=0):
        """ Remove the farthest points if they implies a variation of tau or v_max
        greater than a limit (self.VMAX_DIFF_RATIO and self.TAU_DIFF_RATIO )
        Recursive call until the diff ratio is smaller than the limit or a max number of
        iteration is reached, currently 10.
        Returns the number of points removed
        (note : pas detecté si c'est le 2eme point le plus eloigné qui induit cette variation.
        cf eglaine1 je crois)
        """
        #print("_remove_impact_points - début")
        nb_max_iter=10 # If too much points are removed, there is a pb.
        i=0 # number of points removed
        
        if (n<0):
            print(f"ERROR : This iteration value cannot be negative. Do not use this param")
            return None
        
        # Init values for the farthest point
        i_max_gap = np.argmax(gaps)
        gap = gaps[i_max_gap]
        
        if i_max_gap < len(self.V_sprint_acc):
            V=np.delete(self.V_sprint_acc , i_max_gap)
            T=np.delete(self.T_sprint_acc, i_max_gap)
        
            # Compute the v_max and tau variation (%100) without this point
            (v_max, tau, delay) = self.compute_f_velocity_params(T, V)
            v_max_diff=abs(self.v_max-v_max)*100/self.v_max
            tau_diff=abs(self.tau-tau)*100/self.tau
        
            #print(f"old vmax : {self.v_max:.2f}, new vmax : {v_max:.2f}, v_max_diff : {v_max_diff:.2f} %")
            #print(f"old tau : {self.tau:.2f}, new tau : {tau:.2f}, tau_diff : {tau_diff:.2f} %")
        
            # Eventually, remove the point, and continue the process with the next point.
            # (todo : warning if nb_max_point reached?)
            if (n < nb_max_iter):
                n+=1
                if (v_max_diff > self.VMAX_DIFF_RATIO or tau_diff > self.TAU_DIFF_RATIO):
                    self._remove_point(i_max_gap)
                    gaps=np.delete(gaps, i_max_gap)
                    # Recursive call. Just for fun
                    j=self._remove_impact_points(gaps,n)
                    i=i+j+1

        return i

    #-------------------- Private methods -----------------------------------------------

    def _f_velocity(self, t):
        """
        Returns the theorical velocity as time t, using the attributes tau, v_max and 
        delay.
        """
        # self.T_sprint[0] : first time value measured for the sprint.
        return self.v_max * (1-np.exp((self.T_sprint[0] + self.delay - t)/self.tau))

    def _get_weighted_vgaps(self):
        """
        Returns the difference between V measured and V model, but weighted by the inverse
        of the V model slope.
        After some tests, use 1/sqrt(slope). 
        """
        
        vgaps = abs(self.V_sprint_acc-self.V_model)[1:]*(np.diff(self.T_sprint_acc)/np.diff(self.V_model))**(1/2)
        vgaps = np.concatenate(([0.0], vgaps)) 
        return vgaps
        
        #weighted_vdiffs = abs(self.V_sprint_acc-self.V_model)[1:]*(np.diff(self.T_sprint_acc)/np.diff(self.V_model))**(1/2)
        # For the first one (or last one), there is no slope . Furthermore, we don't 
        # want to remove the first point
        # --> let's add a 0 gap for the first point.
        #weighted_vdiffs = np.concatenate(([0.0], weighted_vdiffs)) 
        #return weighted_vdiffs            
            
    #-------------------- Public methods ------------------------------------------------
 
    def set_end_acc(self,t_end_acc):
        ''' Used by move_bound.py - compare result with diff end acc
            don't remove outliers again
        '''
        
        # get i corresponding to t_enc_acc
        if t_end_acc is None:
            return
        else:
            i_end_acc = bisect_left(self.T_sprint, t_end_acc)

        if i_end_acc > self.n-1 or i_end_acc < 0:
            return  

        self.i_end_acc = i_end_acc

        # compute model velocity again
        self._set_V_model()
 
    def reset_end_acc(self):
        self.i_end_acc=self.n-1
        self._set_V_model()
        
    def compute_f_velocity_params(self,T,V):
        """
        Returns the velocity function params, using the scipy leastsq methods
        Inpus are the measured time and velocity arrays for the sprint.
        """
        # initial values
        v_max = 8.0
        tau = 1.0
        delay = 0.0 # en seconde
        p_initial=np.array([v_max, tau, delay],dtype=float)
        t_start = T[0]
        
        # get optimum params
        F = lambda p, t : p[0] * (1-np.exp((t_start + p[2] - t)/p[1]))
        F_err = lambda p, t, v: F(p, t)-v
        p_final, success = leastsq(F_err,p_initial[:],args=(T,V))

        v_max = p_final[0]
        tau = p_final[1]
        delay = p_final[2]   
        
        return(v_max, tau, delay)
 
    def print_attr(self):
        print_obj_attr(self)

    #def get_f_velocity_params(self):
    #    return (self.v_max, self.tau, self.delay)

    def f_velocity(self, t, v_max, tau, delay):
        """
        Returns the theorical velocity as time t for the input param
        """
        # self.T_sprint[0] : first time value measured for the sprint.
        # t_start_measure = self.T_sprint[0]
        
        #return self.v_max * (1-np.exp((self.T_sprint[0] + self.delay - t)/self.tau))
        return v_max * (1-np.exp((self.T_sprint[0] + delay - t)/tau))
        
    def shift_time(self,t):
        # recale le temps tq t=0 est le début du sprint
        if len(self.T_sprint)==0:
            return None
        return t - self.T_sprint[0] - self.delay

    def plot_outliers(self):
    
        # plot vmesure, vmodel et pareil pour self.
        plt.plot(self.T_sprint_in, self.V_sprint_in, alpha=0.3)
        plt.plot(self.T_sprint, self.V_sprint, alpha=0.5)
        plt.plot(self.T_sprint_acc, self.V_sprint_acc,color='g')
        plt.plot(self.T_sprint, self.V_smooth)
        plt.plot(self.T_sprint_acc, self.V_model,color='r')
        plt.title(f"{self.title}")
        
        # plateau
        plt.axhline(y=self.vs_max, linewidth=1,linestyle='--')
        plt.axvline(x=self.T_sprint[self.i_vs_max], linewidth=1)
        plt.axvline(x=self.T_sprint[self.i_start_plateau], linewidth=1) 
        plt.axvline(x=self.T_sprint[self.i_end_plateau], linewidth=1) 
        
        # sans les outliers
        T_sprint_in = self.T_sprint_in[0:self.i_end_acc+self.n_out]
        V_sprint_in = self.V_sprint_in[0:self.i_end_acc+self.n_out]
        (v_max, tau, delay) = self.compute_f_velocity_params(T_sprint_in, V_sprint_in)
        Vmodel_in=self.f_velocity(T_sprint_in, v_max=v_max,tau=tau,delay=delay)
        #plt.plot(T_sprint_in, Vmodel_in, alpha=0.5)
        
        v_max_diff=(self.v_max-v_max)*100/self.v_max
        tau_diff=(self.tau-tau)*100/self.tau
    
        print(f"plot_outliers. v max diff {v_max_diff:.2f} % ; tau diff {tau_diff:.2f} %")
    
    def get_points_impact(self):#,Vmesure, Vmodel,T):
        """
        Get points impact on the calculation of tau and v_max
        Compute v_max and tau variation when removing each points.
        Returns a pandas dataframe containg the variations for each points.
        """   
        # objectif de variation max en quelque sorte.
        #vmax_diff_lim = 0.5
        #tau_diff_lim = 2.5
        
        #v_diffs=abs(Vmesure-Vmodel)  
        weighted_gaps = self._get_weighted_vgaps()
        
        pd_columns=['index','time','v measure','v gap','weighted vgap','v max', 'vmax variation', 'tau', 'tau variation']#,'diff dist']
        pd_outliers = pd.DataFrame(columns=pd_columns)

        # on ne touche pas au point 0
        dict={'index':0,
               'time':self.T_sprint[0],
               'v measure':self.V_sprint[0],
               'v gap' : 0.0,
               'weighted vgap': 0.0,
               'v max':self.v_max,
               'vmax variation':0.0,
               'tau':round(self.tau,2),
               'tau variation':0.0
               }
               #,'diff dist':0.0}

        for i in range(1,self.i_end_acc):                   
        #for i in range(1,self.n-1):

            V=np.delete(self.V_sprint_acc.copy() ,i)
            T=np.delete(self.T_sprint_acc.copy(), i)
             # compute params again
            (v_max, tau, delay) = self.compute_f_velocity_params(T,V)
            #print(v_max, tau, delay)

            vmax_variation=abs(self.v_max-v_max)*100/self.v_max
            tau_variation=abs(self.tau-tau)*100/self.tau
            
            #tau_diff_ratio=tau_diff/tau_diff_lim
            #vmax_diff_ratio=v_max_diff/vmax_diff_lim
            #diff_dist=((tau_diff/tau_diff_lim)**2+(v_max_diff/vmax_diff_lim)**2)**1/2
            
            dict={'index':i,
                   'time': self.T_sprint[i],
                   'v measure': self.V_sprint[i],
                   'v gap' : round(abs(self.V_sprint[i]-self.V_model[i]),2),
                   'weighted vgap':round(weighted_gaps[i],2),
                   'v max':round(v_max,2),
                   'vmax variation':round(vmax_variation,2),
                   'tau':round(tau,2),
                   'tau variation':round(tau_variation,2)
                   }
                   #,'diff dist':round(diff_dist,2)}

            pd_outliers = pd_outliers.append(dict, ignore_index=True)

        #print(pd_outliers)
        return pd_outliers

    def plot_points_impact(self):
    
        impacts=self.get_points_impact()
        
        '''
        fig, axs = plt.subplots(1,2,figsize=(12,5))
        fig.canvas.set_window_title(f"{self.title}")
        
        plt1=axs[0]
        plt1.scatter(impacts["v diff"],impacts["v max diff"])
        plt1.set_title('impact v abs sur v max')
        
        plt2=axs[1]
        plt2.scatter(impacts["gap"],impacts["v max diff"])
        plt2.set_title('impact v slope sur v max')
        '''
        
        fig, axs = plt.subplots(2,2,figsize=(12,7))
        fig.canvas.set_window_title(f"{self.title}")
        #fig.figure(figsize=(3,4))
        plt1=axs[0][0]
        plt1.scatter(impacts["v gap"],impacts["vmax variation"])
        plt1.set_title('V gap impact on v max')
        
        plt2=axs[0][1]
        plt2.scatter(impacts["weighted vgap"],impacts["vmax variation"])
        plt2.set_title('Weighted V gap impact on v max')
        
        plt3=axs[1][0]
        plt3.scatter(impacts["v gap"],impacts["tau variation"],color='g')
        plt3.set_title('V gap impact on tau')
        
        plt4=axs[1][1]
        plt4.scatter(impacts["weighted vgap"],impacts["tau variation"],color='g')
        plt4.set_title('Weighted V gap impact on tau')

    def print_result(self):
        print(f"\nRésultats pour le sprint {self.title}")
        print(f"v max \t{self.v_max:.2f} m/s")
        print(f"Acceleration constant\t{self.tau:.2f}")
        print(f"V th reached (top speed) \t{self.V_model[-1]:.2f} m/s")
        #print(f"T th : \t{self.T_sprint[-1]-self.T_sprint[0]-self.delay:.2f} m/s")
        print(f"Sprint duration\t{self.duration:.2f} s")
        
        diff = self.v_max - self.V_model[-1]
        print(f"Diff V max V reached : {diff:.2f} s")

    #------------------ Private methods -------------------------------------------------

if __name__ == "__main__":
    # execute only if run as a script : python radar_data.py
    # load file
    from radar_file import params_get_file #, scan_dir
    import time
    
    file = params_get_file()   
    
    def view_points_impact():
        #plt.plot(s.T_sprint,s.V_sprint)
        #plt.plot(s.T_sprint,s.V_model)
        s = build_sprint_from_file(file) 
        s.plot_outliers()
        #plt.show()
        s.plot_points_impact()
        plt.show()
        
    def view_auto():
        s = build_sprint_from_file(file) 
        if s:
            s.print_result()
            s.plot_outliers()
            plt.show()
    
    # attention, bien donner l'option -e rad
    def view_manual():
        """
        Sprint with bounds manually set to the whole radar data, and with no outlier
        points removed
        """
        s = build_sprint_from_file(file, auto=False,outliers=True) 
        #s = build_sprint_from_file(file, auto=True,outliers=False) 
        #rd=initRDFromFile(file)
        #rd.set_sprint_total()
        #(Tsprint,Vsprint)=rd.extract_sprint()
        #s = Sprint(Tsprint, Vsprint, rd.title, outliers=False)
        s.print_result()
        s.plot_outliers()
        plt.show()
    
    def compare():
        rad_file=file[:-4]+'.rad'
        rda_file=file[:-4]+'.rda'
        
        plt.figure(1)
        s_manual=build_sprint_from_file(rad_file, auto=False,outliers=False)
        s_manual.plot_outliers()
        #plt.show()
    
        plt.figure(2)
        s_auto=build_sprint_from_file(rda_file)
        s_auto.plot_outliers()
        
        plt.show()
    
    view_auto()
    #view_manual()
    #view_points_impact()
    #compare()

    
    # Debut du decompte du temps
    #start_time = time.time()
    #load_time = time.time()
    #print("Temps chargement données, extract sprint, compute params, remove outliers: %s secondes ---" % (load_time - start_time))


