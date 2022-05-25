# -*- coding: utf-8 -*
# python3
# Author : LJK - Laboratoire Jean Kuntzmann - C. Bligny
"""
Move interactively sprint bounds, and print new pfv values
Usage : python move_bound.py [param]
"""
# To be improved, using inter-class links ?

import os
import sys
import matplotlib.pyplot as plt
from sprof.athlete import get_athlete_values
from sprof.radar_data import build_RD_from_file
from sprof.sprint import Sprint
from sprof.pfv import PFV

class MoveBound:

    def __init__(self, t_bound_min, t_bound_max, t_min, t_max, radar_data):
    
        self.t_bound_min = t_bound_min
        self.t_bound_max = t_bound_max
        self.t_bound_min_initial = t_bound_min
        self.t_bound_max_initial = t_bound_max
        self.t_middle = (t_bound_min+t_bound_max)/2
        #self.t = t_initial
        self.t_min = t_min
        self.t_max = t_max
        self.r=radar_data
        
        # fin athlete, mass and stature
        (mass,stature)=get_athlete_values(r.title)
        self.mass=mass
        self.stature=stature
        
        (Tsprint,Vsprint)=r.extract_sprint()
        #self.s = Sprint(Tsprint, Vsprint, r.title, outliers=False)
        self.s = Sprint(Tsprint, Vsprint, r.title)
        self.p = PFV(v_max=self.s.v_max, tau=self.s.tau, duration=self.s.duration, mass=self.mass, stature=self.stature)
        
        self.first_vmax=self.s.v_max
        self.first_tau=self.s.tau
        self.first_V0=self.p.V0
        self.first_F0_kg=self.p.F0_kg
        self.first_Pmax_kg=self.p.Pmax_kg
        self.first_sfv=self.p.sfv
        print(f"first svf : {self.first_sfv}")
        
        self._init_figure()
        
    @property
    def vmax_ratio(self):
        return round((self.s.v_max-self.first_vmax)*100/self.first_vmax,2)

    @property
    def tau_ratio(self):
        return round((self.s.tau-self.first_tau)*100/self.first_tau,2)    

    @property
    def V0_ratio(self):
        return round((self.p.V0-self.first_V0)*100/self.first_V0 ,2)

    @property
    def F0_ratio(self):
        return round((self.p.F0_kg-self.first_F0_kg)*100/self.first_F0_kg ,2)
        
    @property
    def Pmax_ratio(self):
        return round((self.p.Pmax_kg-self.first_Pmax_kg)*100/self.first_Pmax_kg,2)
       
    @property
    def sfv_ratio(self):
        print("Calcul sfv ratio")
        print(f"first sfv : {self.first_sfv}")
        print(f"sfv : {self.p.sfv}")
        return round((self.p.sfv-self.first_sfv)*100/self.first_sfv,2)
    
    def _init_figure(self):

        # pour info, on affiche toujours les valeurs initiales
        plt.axvline(x=self.t_bound_min_initial, linewidth=1)
        plt.axvline(x=self.t_bound_max_initial, linewidth=1)

        t_sprint_acc_end = self.s.T_sprint[self.s.i_end_acc]
        self.t_bound_max = t_sprint_acc_end

        self.line_min = plt.axvline(x=self.t_bound_min, linewidth=1,picker=5, linestyle='--', color='black')
        self.line_max = plt.axvline(x=self.t_bound_max, linewidth=1,picker=5, linestyle='--', color='black')    
    
        #self.canvas=self.line.get_figure().canvas
        self.canvas=plt.figure(1).canvas
        self.canvas.mpl_connect('pick_event', self.onpick)
        self.canvas.draw()
        
        self.active_line=None
 
    def onpick(self, event):
        artist = event.artist
        #print(artist)
        
        if (self.line_min == artist):
            self.active_line = self.line_min
        else:
            self.active_line = self.line_max
        
        self.follower = self.canvas.mpl_connect("motion_notify_event", self.follow_mouse)
        self.releaser = self.canvas.mpl_connect("button_release_event", self.release_mouse)
        #print(releaser)
        
    def follow_mouse(self,event):
        # delclanche pour chaque line
        self.active_line.set_xdata([event.xdata, event.xdata])
        #self.line.set_xdata([event.xdata, event.xdata])
        self.canvas.draw_idle()
        
    def release_mouse(self,event):
        #self.line= event.artist
        #line = event.artist
        x=event.xdata
        print(f" event data : {x}")
        #new_t = self._check_new_value(x)
        
        if self.active_line == self.line_min:
            x=self._check_new_value(x, self.t_min, self.t_middle)
            self._update_lower(x)
        else:
            x=self._check_new_value(x, self.t_middle, self.t_max)
            self._update_upper(x)
            
        self.canvas.mpl_disconnect(self.releaser)
        self.canvas.mpl_disconnect(self.follower)
    
        #self.active_line.set_xdata([x, x])
        fig.canvas.draw_idle()
        self.active_line=None
   
    def _update_lower(self,new_t_sprint_start):
        print("---------- Update sprint lower bound ----------")
        #self.r.set_sprint_bounds(t_start=new_t_sprint_start)
        self.r.set_sprint_start(t_start=new_t_sprint_start)
        self.t_bound_min=new_t_sprint_start

        (Tsprint,Vsprint) = self.r.extract_sprint()
        self.s = Sprint(Tsprint, Vsprint, self.r.title)
        
        self._update_data()

    def _update_upper(self,new_t_sprint_end):
        print("---------- Update sprint upper bound ----------")
        #self.r.set_sprint_end(t_end=new_t_sprint_end)
        
        self.t_bound_max=new_t_sprint_end
        
        self.s.set_end_acc(new_t_sprint_end)
        

        self._update_data()
   
    def _update_data(self):

        #(Tsprint,Vsprint) = self.r.extract_sprint()
        #self.s = Sprint(Tsprint, Vsprint, self.r.title)
        
        print(f"\tt start = {self.t_bound_min:.2f}, t end = {self.t_bound_max:.2f}")
        print(f"\tv max = {self.s.v_max:.2f}, tau = {self.s.tau:.2f}, delay = {self.s.delay:.2f}, duration = {self.s.duration:.2f}")

        #self.p = PFV(v_max=self.s.v_max, tau=self.s.tau, duration=self.s.duration, mass=self.mass, stature=self.stature, pression=760)
        self.p = PFV(v_max=self.s.v_max, tau=self.s.tau, duration=4, mass=self.mass, stature=self.stature, pression=760)
        
        
        self.print_infos()      
        
        plt.clf()
        self.plot()
        self._init_figure()
        self.canvas.draw()
        
        # Si on veut calculer les ratio par rapport à la valeur précédent
        self.first_vmax=self.s.v_max
        self.first_tau=self.s.tau
        self.first_V0=self.p.V0
        self.first_F0_kg=self.p.F0_kg
        self.first_Pmax_kg=self.p.Pmax_kg
        self.first_sfv=self.p.sfv

    def _check_new_value(self, new_value, min, max):
        if (new_value):
            if (new_value < min): 
                new_value = min
            if (new_value > max):
                new_value = max  

        return new_value
            
    def plot(self):
        #self.r.plot_bounds()
        plt.plot(self.r.T, self.r.V, alpha=0.5)
        plt.plot(self.s.T_sprint, self.s.V_sprint, alpha=0.5)
        plt.plot(self.s.T_sprint_acc, self.s.V_model,color='r')#, alpha=0.5)
        plt.plot(self.s.T_sprint, self.s.V_smooth,color='g')
        plt.axhline(y=self.s.v_max, linewidth=1,linestyle='--',color='r')
        plt.axhline(y=self.s.vs_max, linewidth=1,linestyle='--', color='g')
        plt.axvline(x=self.s.T_sprint[self.s.i_vs_max], linewidth=1, alpha=0.5)
        plt.axvline(x=self.s.T_sprint[self.s.i_start_plateau], linewidth=1,alpha=0.5) 
        plt.axvline(x=self.s.T_sprint[self.s.i_end_plateau], linewidth=1,alpha=0.5)       
    
    def print_infos(self):
        #v_smooth=self.r.V_smooth[self.r.i_end_sprint]
        #v_smooth=self.s.V_smooth[self.r.i_end_sprint]
        #print(f"V smooth end sprint : {v_smooth} - {v_smooth/self.r.vs_max*100:.2f} % v mesure max")
        #print(f"Variation v end sprint / v mesure max : - {(v_smooth-self.r.vs_max)*100/self.r.vs_max:.2f} % v mesure max")
        print(f"Variation v max / v mesure max : - {(self.s.v_max-self.r.vs_max)*100/self.r.vs_max:.2f} % v mesure max")
        print(f"Variation vmax = {self.vmax_ratio:.2f} %")
        print(f"Variation tau = {self.tau_ratio:.2f} %")
        print(f"Variation V0 = {self.V0_ratio:.2f} %")
        print(f"Variation F0 = {self.F0_ratio:.2f} %")
        print(f"Variation Pmax = {self.Pmax_ratio:.2f} %")
        print(f"Variation sfv = {self.sfv_ratio:.2f} %")
    
if __name__ == "__main__":

    from sprof.radar_file import params_get_file

    print("========== Move Sprint bounds - Start ==========")
    file=params_get_file()

    r = build_RD_from_file(file)
    
    if r.n > 0:
 
        # static datas
        print(f"Vitesse max mesurée : {r.vs_max:.2f}")
        #print(f"Durée plateau : {r.plateau_duration:.2f} s (borne : v = {r.PLATEAU_RATIO} * v max mesurée")
        #print(f"Durée plateau sup (> v max): {r.plateau_duration_sup:.2f} s")
        
        # limit inf
        t_sprint_min=r.T[r.i_start_sprint]
        t_sprint_max=r.T[r.i_end_sprint]
        #t_sprint_middle=(t_sprint_min+t_sprint_max)/2
        t_min=r.T[0]
        t_max=r.T[-1]
        #print(f"\tt start = { t_sprint_min:.2f}, t end = {t_sprint_max:.2f}")
        move = MoveBound(t_sprint_min, t_sprint_max,t_min,t_max, r) 
        move.plot()
        #v_line=DraggableLine(line_start,line_stop,r)
      
        fig = plt.figure(1)
        fig.canvas.draw()
        strTitle=r.title#+' '+r.file_ext
        fig.suptitle(strTitle, fontsize=16)
        
        #fig.title(f"{r.title}, format : {r.file_ext}")
        plt.show()
