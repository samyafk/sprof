# -*- coding: utf-8 -*
# python3
# Author : LJK - Laboratoire Jean Kuntzmann - C. Bligny
"""
Watch a dir, waiting for radar data (= file ending with .rda)
When such a file is copied in the dir, launch the analyse for the file, and displays 
some datas:
v max, 30 m time (based on acceleration mesured, not "real time"), power / kg
V max mesured (souvent > vmax - je pense que c'est l'effet 'ligne d'arrivée') 
Also display the sprint image

usage : python radar_watcher.py dir_to_watch
"""
import sys
import time
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
from PIL import Image

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from sprof.analyse import build_analyse_from_file
from sprof.pfv_dataset import PFVDataset

class RadarDataHandler(FileSystemEventHandler):

    def __init__(self,dir):
        self.last_modified = datetime.now() - timedelta(seconds=10)
        self.last_file = 'None Yet'
        #print (self.last_modified)
        self.dataset=PFVDataset("data_watcher")
        self.dir=dir
        
        dt=datetime.today()
        strDate=dt.strftime("%y%m%d")
        self.export_file=os.path.join(dir, strDate+'_pfv_analyse.csv')

        # si on a dejà des résultats d'analyse, on les conserve
        if os.path.exists(self.export_file):
            self.dataset.read_csv(self.export_file)
            #print("Données déjà analysées dans ce répertoire : ")
            #print(self.dataset.datas)
        
    def on_created(self, event):
            
        #print(event.event_type)
        if not event.is_directory:
            #print("Le fichier %s a été modifé" % event.src_path)
            if event.src_path:
                ext = os.path.splitext(event.src_path)[-1]
                if (ext==".rda"): 
                    print(f"On create Data Watcher - Analyse du fichier {event.src_path}")
                    self._run_sprint_analyse(event.src_path)
    
    '''   
    # genere des doublons avec windows      
    def on_modified(self,event):

        if not event.is_directory:
            #print("Le fichier %s a été modifé" % event.src_path)
            if event.src_path:
                ext = os.path.splitext(event.src_path)[-1]
                if (ext==".rda"):
                    print(f"On modify Data Watcher - Analyse du fichier {event.src_path}")
                    self._run_sprint_analyse(event.src_path)  
    '''
                  
    def _run_sprint_analyse(self,file):
        """ On the fly analysis for a radar file
        """        
        
        # Patch windows - prevent from running twice
        # for creation. set to 6 seconds after test
        # site effects : wait 6 seconds between analyses for same files
        if ( (datetime.now() - self.last_modified < timedelta(seconds=6)) and (self.last_file == file) ):
            print("Fichier déjà traité.")
        else:
            self.last_modified = datetime.now()
            self.last_file=file
            # Windows patch : wait until the file is fully copied
            copying = True
            size_past = -1
            while copying:
                size_now = os.path.getsize(file)
                if size_now == size_past:
                    #print(f"file has copied completely now size: {size_now}")
                    break
                    #why sleep is not working here ?
                else:
                    size_past = os.path.getsize(file)
                    #print(f"file copying size: {size_past}")
        
            # previous patch not enough, add a delay, until file is fully saved and can
            # be opened
            time.sleep(2)
        
            a=build_analyse_from_file(file)
        
            if a:
                # print pfv values
                a.print_analyse()
                print()
                
                n=self.dataset.add_row_from_analyse(a)
                if n>0:
                    self.dataset.export_csv() # save to default analyse datadir
                    self.dataset.export_csv(self.export_file) # export to data watcher dir 
                               
            '''
            a=build_analyse_from_file(file)
        
            if a:
                # print pfv values
                a.print_analyse()
                print()
            
                # save data into csv file
                self.dataset.add_row_from_pfv(a.pfv, a.radar_data.title)
                self.dataset.export_csv() # save to default analyse datadir
                self.dataset.export_csv(self.export_file) # export to data watcher dir
                        
                # save img with plot
                plt.figure(figsize = (9, 7))
                a.plot_normalize()
                img_file=file[:-4]+'.png' # remove .rda and add .png
                plt.savefig(img_file)
                plt.close()
        
                # show imgae
                # image = Image.open(img_file)
                # image.show(title='test') # titre marche pas
            '''
        
        print("\nWaiting .......")
    
    
if __name__ == "__main__":

    # get dir to watch. If not provided : watch current dir
    rd_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    # get abspath - and check dir
    abspath = os.path.abspath(rd_path)
    if not os.path.isdir(abspath):
        print(f"Erreur : le répertoire {abspath} n'existe pas")
    else :
        
        print(f"Start watching dir {abspath}")
        print("Pour quitter, taper CTR c ou fermer cette fenêtre")
    
        rd_handler = RadarDataHandler(abspath)
        rd_observer = Observer()
        rd_observer.schedule(rd_handler, abspath, recursive=True)
        rd_observer.start()
        print("Waiting .....")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            rd_observer.stop()
        
        rd_observer.join()
