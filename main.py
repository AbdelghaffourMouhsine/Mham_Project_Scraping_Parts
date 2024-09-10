################################################ main #####################################################
###########################################################################################################

import threading
import time
import os
from SharedListBrandDic import SharedListBrandDic
from WorkerThread import WorkerThread
from ProxyLoader import ProxyLoader


file_path = r"./proxies/Webshare 100 proxies.txt"
proxy_loader = ProxyLoader(file_path)

# Créer une liste partagée, une file de résultats et un verrou CSV
shared_list = SharedListBrandDic()

# Créer et démarrer les threads
num_threads = 10

start = 0
end = min(100,shared_list.nb_BrandDic)
step = 50

for i in range(start, end, step):
    
    shared_list.select_data(i,i+step)
    
    threads = []
    for j in range(num_threads):
        thread = WorkerThread(j+1, shared_list, proxy_loader)
        thread.start()
        threads.append(thread)
        time.sleep(2)

    # Attendre que tous les threads se terminent
    for thread in threads:
        thread.join()
    
    print(f"%"*100)
    print("saved URLs : ",i+step)
    print(f"%"*100)