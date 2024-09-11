import threading
from ListeBrandDic import ListeBrandDic

class SharedListBrandDic:
    def __init__(self):
        self.allBrandDic = []
        self.data = []
        self.lock = threading.Lock()
        self.listeBrandDic = ListeBrandDic()
        self.nb_BrandDic = 0
        self.load_data()
        self.Delete_Duplicates()
        self.filtrer_dictionnaires()
        
    def load_data(self) :
        self.allBrandDic = self.listeBrandDic.load_data()
        self.nb_BrandDic = len(self.allBrandDic)
        
    def Delete_Duplicates(self):
        vue = set()
        liste_sans_doublons = []
        for d in self.allBrandDic:
            t = tuple(d.items())  # Convertir le dictionnaire en un tuple de tuples (clé, valeur)
            if t not in vue:      # Vérifier si ce tuple existe déjà dans le set 'vue'
                vue.add(t)        # Ajouter le tuple au set
                liste_sans_doublons.append(d)  # Ajouter le dictionnaire à la liste finale
        self.allBrandDic = liste_sans_doublons
        self.nb_BrandDic = len(self.allBrandDic)
        
    def filtrer_dictionnaires(self):
        self.allBrandDic = [d for d in self.allBrandDic if d['start_year'] != '2004']
        self.nb_BrandDic = len(self.allBrandDic)
        
    def select_data(self, start, end):
        if end < self.nb_BrandDic:
            self.data = self.allBrandDic[start:end]
        else:
            self.data = self.allBrandDic[start:self.nb_BrandDic]