import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import requests
import os
import re
import threading
import zipfile
import math
from collections import defaultdict
import re

from Part import Part
from PartStorage import PartStorage
from CheckPartStorage import CheckPartStorage

from ListeBrandDic import ListeBrandDic

class PartInfoProcess:
    def __init__(self, thread_id=0, start_brand=None, start_year=None, start_model=None, start_elem_X=None, start_elem_XX=None, start_part_name=None, end_brand=None,end_year=None,end_model=None,end_elem_X=None,end_elem_XX=None,end_part_name=None, PROXY_HOST=None, PROXY_PORT=None, PROXY_USER=None, PROXY_PASS=None, use_proxy=False, with_selenium_grid=False, workerThread=None, is_for_extract_models=False):

        self.workerThread = workerThread
        self.use_proxy = use_proxy
        if self.use_proxy :
            # proxys from : https://www.webshare.io/
            
            # for run webdriver using a proxy without Authentication
            # define the proxy address and port
            # proxy = "45.127.248.127:5128"
            # options = Options()
            # options.add_argument(f"--proxy-server={proxy}")
            # self.driver = webdriver.Chrome(options=options)
    
            # for run webdriver using a proxy with Authentication
            self.PROXY_HOST = PROXY_HOST  # rotating proxy or host
            self.PROXY_PORT = PROXY_PORT # port
            self.PROXY_USER = PROXY_USER # username
            self.PROXY_PASS = PROXY_PASS # password
            
            self.options = self.init_proxy_and_get_chrome_options()
        else:
            self.options = webdriver.ChromeOptions()
            
        self.with_selenium_grid = with_selenium_grid
        if self.with_selenium_grid:
            self.HUB_HOST = "selenium_hub_mham_project1"
            self.HUB_PORT = 4444
            self.server = f"http://{self.HUB_HOST}:{self.HUB_PORT}/wd/hub"
            self.driver=None
            with self.workerThread.lock_selenium_grid:
                self.driver = webdriver.Remote(command_executor=self.server, options=self.options)
                time.sleep(2)
        else:
            self.driver = webdriver.Chrome(options=self.options)
        
        self.url = "https://www.rockauto.com/"
        self.driver.get(self.url)
        self.elements = None
        time.sleep(3)
        self.get_web_site()
        self.elem_state = {}
        self.check_part = {}
        self.init_check_elem_state( start_brand, start_year, start_model, start_elem_X, start_elem_XX, start_part_name, end_brand,end_year,end_model,end_elem_X,end_elem_XX,end_part_name)
        print(f"in PartInfoPro : {start_brand}")
        
        # Créer le dossier 'images et results' s'il n'existe pas
        if not os.path.exists('images'):
            os.makedirs('images')
        if not os.path.exists('results'):
            os.makedirs('results')
        
        self.thread_id = thread_id

        if is_for_extract_models:
            self.extract_liste_brand_dic()
        else:
            self.start_scraping()
        
        self.driver.quit()
        print(f"%"*500)
        print(f"end of thread : {self.thread_id} | {start_brand}")
        print(f"%"*500)

    def init_proxy_and_get_chrome_options(self): 
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """
        
        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (self.PROXY_HOST, self.PROXY_PORT, self.PROXY_USER, self.PROXY_PASS)
        
        def get_chrome_options(use_proxy=True, user_agent=None):
            # path = os.path.dirname(os.path.abspath(_file_))
            chrome_options = webdriver.ChromeOptions()
            if use_proxy:
                pluginfile = 'proxy_auth_plugin.zip'
        
                with zipfile.ZipFile(pluginfile, 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr("background.js", background_js)
                chrome_options.add_extension(pluginfile)
            if user_agent:
                chrome_options.add_argument('--user-agent=%s' % user_agent)
            return chrome_options
        return get_chrome_options()
    
    def get_web_site(self):
        time.sleep(5)
        g2004 = self.driver.find_elements(By.XPATH, '//span/label/input')
        [ x for x in g2004 if x.get_attribute("name") == "cbxYearFilter"][0].click()
        print("g2004 clicked")
        select_en = self.driver.find_elements(By.XPATH, '//span/select/option')
        [ x for x in select_en if x.text == "English"][0].click()
        print("select_en clicked")
        # modal_x = self.driver.find_elements(By.XPATH, '//table/tbody/tr[1]/td/span')
        # [ x for x in modal_x if x.get_attribute("onclick") == "hideOverlay();"][0].click()

        time.sleep(3)
        
        self.elements = self.driver.find_elements(By.XPATH, '/html/body/div/div/div/div[1]/main/table/tbody/tr/td[1]/div[1]/div/div[2]/div/div/div[4]/div/div')
        print(len(self.elements))
        
        elem = self.elements[10].find_elements(By.XPATH, "./*")
        print(len(elem))
        
        self.elements = [e for e in self.elements if "ra-hide" not in e.get_attribute("class")]
        print(len(self.elements))

    def init_check_elem_state(self, start_brand, start_year, start_model, start_elem_X, start_elem_XX, start_part_name, end_brand, end_year,end_model,end_elem_X,end_elem_XX,end_part_name):
        elems_name = ['brand', 'year', 'model', 'elem_X', 'elem_XX', 'part_name']
        for e_name in elems_name:
            self.elem_state["start_"+e_name] = None
            self.elem_state["end_"+e_name] = None
            self.elem_state["check_start_"+e_name] = False
            self.elem_state["check_end_"+e_name] = False
            self.check_part[e_name] = None
        
        self.elem_state["start_brand"]= start_brand
        self.elem_state["start_year"]= start_year
        self.elem_state["start_model"]= start_model
        self.elem_state["start_elem_X"]= start_elem_X
        self.elem_state["start_elem_XX"]= start_elem_XX
        self.elem_state["start_part_name"]= start_part_name
        
        self.elem_state["end_brand"]= end_brand
        self.elem_state["end_year"]= end_year
        self.elem_state["end_model"]= end_model
        self.elem_state["end_elem_X"]= end_elem_X
        self.elem_state["end_elem_XX"]= end_elem_XX
        self.elem_state["end_part_name"]= end_part_name
        #print(f"in init_check_elem_state : {self.elem_state['start_brand']}")

    def nom_valide(self, chaine):
        # Supprimer les espaces au début et à la fin
        chaine = chaine.strip()
        # Remplacer les espaces multiples par un seul tiret bas
        chaine = re.sub(r'\s+', '_', chaine)
        # Supprimer les caractères non autorisés (garde les lettres, chiffres, tirets bas et points)
        chaine = re.sub(r'[^\w.-]', '_', chaine)
        return chaine
        
    def click_elem(self, click_elem):
        t=2
        check = 0
        i = 0
        while not check and i<5:
            try:
                click_elem.click()
                time.sleep(t) ######
                check = 1
            except Exception as e:
                check = 0
            i += 1
        # time.sleep(t)
    
    def show_childs(self, elem, path_show_childs, pere_elem, path_show_pere):
        t = 1
        check_view = 0
        try:
            button_show_childs = elem.find_element(By.XPATH, path_show_childs)
            self.click_elem(button_show_childs)
            #time.sleep(t) ######
            check_view = 1
        except Exception as e:
            check_view = 0
    
        if check_view == 0:
            try:
                button_show_pere = pere_elem.find_element(By.XPATH, path_show_pere)
                button_show_pere.click()
                time.sleep(t) ######
                button_show_childs = elem.find_element(By.XPATH, path_show_childs)
                button_show_childs.click()
                time.sleep(t) ######
                check_view =1
            except Exception as e:
                check_view = 0
            
        return check_view
        
    ####################################################################################################################
    def extract_childs(self, elem, path_to_childs, path_to_name):
        childs = elem.find_elements(By.XPATH, path_to_childs)
        check_childs = self.check_extract_childs(childs, path_to_name)
        i=0 
        while len(childs) == 0 and i<5 and not check_childs:
            childs = elem.find_elements(By.XPATH, path_to_childs)
            check_childs = self.check_extract_childs(childs, path_to_name)
            i += 1
            time.sleep(2)
        if check_childs:
            new_childs=[]
            for e in childs:
                if len(e.find_elements(By.XPATH, "./*")) > 3:
                    e_name = e.find_element(By.XPATH, path_to_name).text
                    if(e_name != None and e_name != ""):
                        new_childs.append(e)
            return new_childs
        return []
        
    def check_extract_childs(self, childs, path_to_name):
        try:
            t=False
            for e in childs:
                if len(e.find_elements(By.XPATH, "./*")) > 3:
                    t=True
                    e_name = e.find_element(By.XPATH, path_to_name).text
                    if(e_name == None or e_name == ""):
                        return False
                    else:
                        return True
            return t
        except Exception as e:
            print("error at check_extract_childs : ", e)
            return False
    ####################################################################################################################
    
    def extract_img_src(self, ligne_info):
        try:
            wait = WebDriverWait(ligne_info, 3) # Wait for a maximum of 3 seconds
            element = wait.until(EC.visibility_of_element_located((By.XPATH, "./tr[1]/td[2]/div/table/tbody/tr/td[2]/img")))
            img = ligne_info.find_element(By.XPATH, "./tr[1]/td[2]/div/table/tbody/tr/td[2]/img")
            img_src = img.get_attribute('src')
        except Exception as e:
            img_src = None
        return img_src
    
    def save_img(self, img_src, brand, model, part_name, code):
        try:
            if self.use_proxy :
                # Construct the proxy URL with authentication
                proxy = f"http://{self.PROXY_USER}:{self.PROXY_PASS}@{self.PROXY_HOST}:{self.PROXY_PORT}"

                # Set up the proxies dictionary
                proxies = {
                    "http": proxy,
                    "https": proxy,
                }
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
                img_data = requests.get(img_src, headers=headers, proxies=proxies, timeout=3).content
            else:
                img_data = requests.get(img_src).content

            new_img_src = f'./images/{self.nom_valide(brand)}/{self.nom_valide(brand)}___{self.nom_valide(model)}___{self.nom_valide(part_name)}___{self.nom_valide(code)}.jpg'

            with open(new_img_src, 'wb') as handler:
                handler.write(img_data)
            return  new_img_src, img_src
        except Exception as e:
            print(e)
            return  None, img_src
                    
    def extract_img(self, ligne_info, brand, part_name, code):
        # code = manufacturer_part_number
        try:
            wait = WebDriverWait(ligne_info, 3) # Wait for a maximum of 3 seconds
            element = wait.until(EC.visibility_of_element_located((By.XPATH, "./tr[1]/td[2]/div/table/tbody/tr/td[2]/img")))

            img = ligne_info.find_element(By.XPATH, "./tr[1]/td[2]/div/table/tbody/tr/td[2]/img")
            img_src = img.get_attribute('src')
            try:
                if self.use_proxy :
                    # Construct the proxy URL with authentication
                    proxy = f"http://{self.PROXY_USER}:{self.PROXY_PASS}@{self.PROXY_HOST}:{self.PROXY_PORT}"

                    # Set up the proxies dictionary
                    proxies = {
                        "http": proxy,
                        "https": proxy,
                    }
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
                    img_data = requests.get(img_src, headers=headers, proxies=proxies, timeout=3).content
                else:
                    img_data = requests.get(img_src).content

                new_img_src = f'./images/{brand.replace(" ", "_")}/{brand.replace(" ", "_")}___{part_name.replace(" ", "_")}___{code.replace(" ", "_")}.jpg'

                with open(new_img_src, 'wb') as handler:
                    handler.write(img_data)
            except Exception as e:
                img = None
                new_img_src = None

        except Exception as e:
            img = None
            img_src = None
            new_img_src = None
            
        return  new_img_src, img_src
    
    def extract_price(self, ligne_info):
        try:
            price = ligne_info.find_element(By.XPATH, "./tr[1]/td[3]/span/span/span").text
            if price.strip() == "Choose Type at Left":
                prices_elem = ligne_info.find_elements(By.XPATH, "./tr[1]/td[1]/div[4]/div/span[2]/span[2]/table/tbody/tr/td[1]/div/div/ul/li")
                dic_prices = {}
                for k, p_elem in enumerate(prices_elem):
                    if k > 0:
                        p_text = p_elem.find_element(By.XPATH, "./div/div/span/b").text
                        p_float = float("".join([c for c in p_text.split("") if c.isdigit() or '.']))
                        dic_prices[p_float] = p_elem
                dic_prices[max(dic_prices.keys())].click()
        except Exception as e:
            print(f"price (Choose Type at Left): {e}")
            price = None
    
        try:
            price = ligne_info.find_element(By.XPATH, "./tr[1]/td[3]/span/span/span").text
        except Exception as e:
            price = None
            
        return price
    
    def extract_code(self, ligne_info):
        try:
            manufacturer_part_number = ligne_info.find_element(By.XPATH, "./tr[1]/td[1]/div[2]/span[2]").text
        except Exception as e:
            manufacturer_part_number = None
        return manufacturer_part_number
    
    def extract_info_type(self, ligne_info,j):
        type= "none"
        try:
            type = ligne_info.find_element(By.XPATH, "./tr[2]/td/div").text
            #if type != "Related Parts":
                #print(f"Line have Type : {j}")
        except Exception as e:
            try:
                type = ligne_info.find_element(By.XPATH, "./tr/td/div").text
                #if type != "Related Parts":
                    # print(f"Line have Type : {j}")
            except Exception as e:
                print("Line doesn't have information and type.")
        finally:
            if type == "Related Parts":
                # print("Line doesn't have information and type.: Related Parts")
                type= "none"
        return type

    def extract_frontOrRear(self, ligne_info):
        try:
            frontOrRear = ligne_info.find_element(By.XPATH, "./tr[1]/td[1]/div[3]/span/span").text
        except Exception as e:
            frontOrRear = None
        return frontOrRear

    def extract_description(self, ligne_info):
        description = []
        try:
            manufacturer_part_number = ligne_info.find_element(By.XPATH, "./tr[1]/td[1]/div[2]/span[2]")
            self.click_elem(manufacturer_part_number)
            trs = self.driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[2]/div/div/table/tbody/tr")
            for tr in trs:
                tds = tr.find_elements(By.XPATH, "./td")
                for td in tds:
                    description.append(td.text)
            close_button = self.driver.find_element(By.XPATH, "/html/body/div[1]/div/div[3]")
            self.click_elem(close_button)
        except Exception as e:
            description = []
            
        return str(description)
    
    # Fonction de transformation
    def transform_price(self, value):
        conversion_rate = 0.31
        # Vérifier si la valeur contient un chiffre
        if any(char.isdigit() for char in value):
            # Extraire le montant en utilisant une expression régulière
            amount = float(re.findall(r"[-+]?\d*\.\d+|\d+", value)[0])
            # Multiplier par 2
            amount *= 2
            # Convertir en Dinar Koweitien
            amount *= conversion_rate
            # Arrondir à l'entier le plus proche
            return math.ceil(amount)
        else:
            # Retourner None si la valeur ne contient pas de chiffre
            return value
    
    def clean_front_or_rear(self, value):
        # Liste des motifs de correspondance
        patterns = {
            'Front Right': r'\bFront Right\b',
            'Front Left': r'\bFront Left\b',

            'Rear Right': r'\bRear Right\b',
            'Rear Left': r'\bRear Left\b',

            'Front': r'\bFront\b',
            'Rear': r'\bRear\b',

            'Left': r'\bLeft\b',
            'Right': r'\bRight\b',
        }

        # Vérifier et retourner la première correspondance trouvée
        for key, pattern in patterns.items():
            if re.search(pattern, str(value), re.IGNORECASE):
                return key

        # Si aucune correspondance trouvée, retourner None
        return ""

    def group_and_select(self, data):
        # Convertir les prix en entier et regrouper par "frontOrRear"
        groups = defaultdict(list)
        for item in data:
            item['price'] = int(item['price'])
            groups[item['frontOrRear']].append(item)

        result = []

        for key, items in groups.items():
            # Trier les éléments dans chaque groupe par "price" décroissant
            items.sort(key=lambda x: x['price'], reverse=True)

            # Prendre le premier élément (ayant le plus grand prix)
            selected_item = items[0]

            # Si l'image du dictionnaire sélectionné est vide, chercher une autre image
            if not selected_item['img_src']:
                for item in items[1:]:
                    if item['img_src']:
                        selected_item['img_src'] = item['img_src']
                        break
                # Si aucune image n'est trouvée dans le groupe, chercher dans d'autres groupes
                if not selected_item['img_src']:
                    for other_key, other_items in groups.items():
                        if other_key != key:
                            for other_item in other_items:
                                if other_item['img_src']:
                                    selected_item['img_src'] = other_item['img_src']
                                    break
                            if selected_item['img_src']:
                                break

            result.append(selected_item)

        return result

    def extract_info(self, elem_info, brand, model, part_name):
        try:
            print("appel extract_info")
            liste_info = elem_info.find_elements(By.XPATH, "./div[2]/div/form/div/div/table/tbody")
            print(f"=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=> {len(liste_info)}")
            
            liste_ligne_info_dic = []
            
            for j, ligne_info in enumerate(liste_info):
                # print("ligne_info")
                if "listing-inner" in ligne_info.get_attribute("class"):      # tbody have info

                    first_price = self.extract_price(ligne_info)
                    manufacturer_part_number = self.extract_code(ligne_info)
                    frontOrRear = self.extract_frontOrRear(ligne_info)
                    img_src = self.extract_img_src(ligne_info)
                    
                    price = self.transform_price(first_price)
                    frontOrRear = self.clean_front_or_rear(frontOrRear)
                    
                    pass_ = False
                    try:
                        if price == 'Out of Stock':
                            price = 0
                        else:
                            if isinstance(int(price), int):
                                price = int(price)
                            else:
                                pass_ = True
                    except Exception as e:
                        pass_ = True
                        
                    if not pass_ :
                        ligne_info_dic = {
                            "manufacturer_part_number" : manufacturer_part_number,
                            "type" : type_,
                            "price" : price,
                            "first_price" : first_price,
                            "frontOrRear" : frontOrRear,
                            "img_src" : img_src,
                            "elem" : ligne_info
                        }
                        liste_ligne_info_dic.append(ligne_info_dic)
           
                else:
                    type_ = self.extract_info_type(ligne_info, j)
                    
            liste_ligne_info_dic = self.group_and_select(liste_ligne_info_dic)
            
            print(f"=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=> Right: {len(liste_ligne_info_dic)}")
            info_list = []
            for ligne_info_dic in liste_ligne_info_dic:
               
                description = self.extract_description(ligne_info_dic["elem"])
                
                if ligne_info_dic["img_src"]:
                    img_src, first_img_src = self.save_img(ligne_info_dic["img_src"], brand, model, part_name, ligne_info_dic["manufacturer_part_number"])
                else:
                    img_src, first_img_src = None, img_src
                    
                print(f"************=t=> {ligne_info_dic['type']}")
                print(f"************=i=> {img_src}")
                print(f"************=p=> {ligne_info_dic['first_price']}")
                print(f"************=m=> {ligne_info_dic['manufacturer_part_number']}")
                print(f"************=f=> {ligne_info_dic['frontOrRear']}")
                print(f"************=d=> {description}")
                
                if int(ligne_info_dic["price"]) == 0:
                    ligne_info_dic["price"] = ligne_info_dic["first_price"]
                    
                info = {
                    "manufacturer_part_number" : ligne_info_dic["manufacturer_part_number"],
                    "type" : ligne_info_dic['type'],
                    "price" : ligne_info_dic["price"],
                    "description" : description,
                    "frontOrRear" : ligne_info_dic["frontOrRear"],
                    "products_img" : img_src,
                    "first_img_src" : first_img_src
                }
                info_list.append(info)
                
            return info_list
        except Exception as e:
            print(e)
            return []

    def check_state(self, current_state, start, end, check_start, check_end):
        if start == None and end == None:                        # None
            return True, False  # check_start, check_end
        
        if current_state.strip() != start and not check_start and not check_end:   # before
                return False, False
        
        if current_state.strip() == start and current_state.strip() != end: # start
            return True, False  # check_start, check_end
        
        if current_state.strip() == start and current_state.strip() == end: # start and end
            return True, True  # check_start, check_end
        
        if check_start and current_state != end and not check_end:                 # between
            return True, False  # check_start, check_end
        
        if check_start and current_state == end :                # end
            return True, True
        
        if check_end and current_state != end :                  # after
            return False, True
        else:
            return False, True
            
    def verify_start_elem(self, current_state, start, end, check_start, check_end, level, elem_state):
        # leval => 0, 1, 2, 3, 4, 5
        if level == 0:
            return self.check_state(current_state, start, end, check_start, check_end)
        if level == 1:
            if elem_state["check_end_brand"]: # check previous level
                return self.check_state(current_state, start, end, check_start, check_end)
            else:
                if elem_state["check_start_brand"] and (not start or start==current_state.strip() or check_start):
                    return True, check_end
                else:
                    return check_start, check_end
        if level == 2:
            if elem_state["check_end_year"] : # check previous level
                return self.check_state(current_state, start, end, check_start, check_end)
            else:
                if elem_state["check_start_year"] and (not start or start==current_state.strip() or check_start):
                    return True, check_end
                else:
                    return check_start, check_end
        if level == 3:
            if elem_state["check_end_model"]: # check previous level
                return self.check_state(current_state, start, end, check_start, check_end)
            else:
                print(elem_state["check_start_model"],start, start==current_state.strip(), check_start)
                
                if elem_state["check_start_model"] and (not start or start==current_state.strip() or check_start):
                    return True, check_end
                else:
                    return check_start, check_end
        if level == 4:
            if elem_state["check_end_elem_X"]: # check previous level
                return self.check_state(current_state, start, end, check_start, check_end)
            else:
                if elem_state["check_start_elem_X"] and (not start or start==current_state.strip() or check_start):
                    return True, check_end
                else:
                    return check_start, check_end
        if level == 5:
            if elem_state["check_end_elem_XX"]: # check previous level
                return self.check_state(current_state, start, end, check_start, check_end)
            else:
                if elem_state["check_start_elem_XX"] and (not start or start==current_state.strip() or check_start):
                    return True, check_end
                else:
                    return check_start, check_end
    
    ####################################################################################################################
    def refresh_page(self, url, level=0,i=0,j=0,k=0,n=0,m=0,z=0):
        print("refresh_page started")
        if level == 0 or level == 1 or level == 2 or level == 3 or level == 4 or level == 5 :
            self.driver.get(url)
            time.sleep(3)
            self.elements = self.driver.find_elements(By.XPATH, '/html/body/div/div/div/div[1]/main/table/tbody/tr/td[1]/div[1]/div/div[2]/div/div/div[4]/div/div')
            self.elements = [e for e in self.elements if "ra-hide" not in e.get_attribute("class")]
        if level == 1 or level == 2 or level == 3 or level == 4 or level == 5 :
            years_elem = self.extract_childs(self.elements[i], "./div[2]/*","./div[1]/div/table/tbody/tr/td[3]/a")
            if level == 1:
                return years_elem
        if level == 2 or level == 3 or level == 4 or level == 5 :
            elems_in_year = self.extract_childs(years_elem[j], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[4]/a")
            if level == 2:
                return years_elem, elems_in_year
        if level == 3 or level == 4 or level == 5 :
            elems_in_elem_in_year = self.extract_childs(elems_in_year[k], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[5]/a")
            if level == 3:
                return years_elem, elems_in_year, elems_in_elem_in_year
        if level == 4 or level == 5 :
            elems_in_elem_in_elem_in_year = self.extract_childs(elems_in_elem_in_year[n], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[6]/a")
            if level == 4:
                return years_elem, elems_in_year, elems_in_elem_in_year, elems_in_elem_in_elem_in_year
        if level == 5 :
            elems_in_elem_in_elem_in_elem_in_year = self.extract_childs(elems_in_elem_in_elem_in_year[m], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[7]/a")
            if level == 5:
                return years_elem, elems_in_year, elems_in_elem_in_year, elems_in_elem_in_elem_in_year, elems_in_elem_in_elem_in_elem_in_year

    ####################################################################################################################
    
    def start_scraping(self):
        previous_is_error = False
        i=0
        while i < len(self.elements):
            try:
                part = Part()

                if len(self.elements[i].find_elements(By.XPATH, "./*")) > 3:
                    part.brand_name = self.elements[i].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[2]/a").text
                    part.Brand = part.brand_name
                    print(part.brand_name)

                    self.elem_state["check_start_brand"], self.elem_state["check_end_brand"] = self.verify_start_elem(part.brand_name, self.elem_state["start_brand"], self.elem_state["end_brand"], self.elem_state["check_start_brand"], self.elem_state["check_end_brand"], 0, self.elem_state)
                    if not self.elem_state["check_start_brand"] and self.elem_state["check_end_brand"]:
                        break
                    if self.elem_state["check_start_brand"]:
                        # print("----->valid_brand")
                        self.url = self.driver.current_url
                        # Créer le dossier 'images/BRAND' s'il n'existe pas
                        if not os.path.exists(f'images/{self.nom_valide(part.Brand)}'):
                            os.makedirs(f'images/{self.nom_valide(part.Brand)}')
                        if not os.path.exists(f'results/{self.nom_valide(part.Brand)}'):
                            os.makedirs(f'results/{self.nom_valide(part.Brand)}')

                        get_years_elem = self.elements[i].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[1]/a")
                        self.click_elem(get_years_elem)
                        time.sleep(1) ######
                        
                        years_elem = self.extract_childs(self.elements[i], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[3]/a")

                        self.check_part['brand'] = part.Brand
                        if len(years_elem) == 0:
                            with self.workerThread.lock_file_check_part:
                                check_part_storage = CheckPartStorage()
                                check_part_storage.insert_check_part(self.check_part)
                                check_part_storage.close_file()
                        j=0
                        while j < len(years_elem):
                            try:
                                part.Year = years_elem[j].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[3]/a").text
                                print(f"**{part.Year}")

                                self.elem_state["check_start_year"], self.elem_state["check_end_year"] = self.verify_start_elem(part.Year, self.elem_state["start_year"], self.elem_state["end_year"], self.elem_state["check_start_year"], self.elem_state["check_end_year"], 1, self.elem_state)
                                if not self.elem_state["check_start_year"] and self.elem_state["check_end_year"]:
                                    break
                                if self.elem_state["check_start_year"]:
                                    # print("-----> valid_year")
                                    self.url = self.driver.current_url
                                    check = False
                                    t = 0
                                    while not check and len(years_elem)>1 and t<5:
                                        check = self.show_childs(years_elem[j], "./div[1]/div/table/tbody/tr/td[2]/a", self.elements[i], "./div[1]/div/table/tbody/tr/td[1]/a")
                                        t+=1

                                    elems_in_year = self.extract_childs(years_elem[j], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[4]/a")
                                    self.check_part['year'] = part.Year
                                    if len(elems_in_year) == 0:
                                        with self.workerThread.lock_file_check_part:
                                            check_part_storage = CheckPartStorage()
                                            check_part_storage.insert_check_part(self.check_part)
                                            check_part_storage.close_file()
                                    k=0
                                    while k < len(elems_in_year):
                                        try:
                                            part.Model = elems_in_year[k].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[4]/a").text
                                            print(f"****{part.Model}")

                                            self.elem_state["check_start_model"], self.elem_state["check_end_model"] = self.verify_start_elem(part.Model, self.elem_state["start_model"], self.elem_state["end_model"], self.elem_state["check_start_model"], self.elem_state["check_end_model"], 2, self.elem_state)
                                            if not self.elem_state["check_start_model"] and self.elem_state["check_end_model"]:
                                                break
                                            if self.elem_state["check_start_model"]:
                                                #print("-----> valid_model")
                                                self.url = self.driver.current_url
                                                check = False
                                                t = 0
                                                while not check and len(elems_in_year)>1 and t<5:
                                                    check = self.show_childs(elems_in_year[k], "./div[1]/div/table/tbody/tr/td[3]/a", years_elem[j], "./div[1]/div/table/tbody/tr/td[2]/a")
                                                    t+=1

                                                elems_in_elem_in_year = self.extract_childs(elems_in_year[k], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[5]/a")

                                                self.check_part['model'] = part.Model
                                                if len(elems_in_elem_in_year) == 0:
                                                    with self.workerThread.lock_file_check_part:
                                                        check_part_storage = CheckPartStorage()
                                                        check_part_storage.insert_check_part(self.check_part)
                                                        check_part_storage.close_file()
                                                n=0
                                                while n < len(elems_in_elem_in_year):
                                                    try:
                                                        elem_X = elems_in_elem_in_year[n].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[5]/a").text
                                                        print(f"******{elem_X}")

                                                        self.elem_state["check_start_elem_X"], self.elem_state["check_end_elem_X"] = self.verify_start_elem(elem_X, self.elem_state["start_elem_X"], self.elem_state["end_elem_X"], self.elem_state["check_start_elem_X"], self.elem_state["check_end_elem_X"], 3, self.elem_state)
                                                        if not self.elem_state["check_start_elem_X"] and self.elem_state["check_end_elem_X"]:
                                                            break
                                                        if self.elem_state["check_start_elem_X"]:
                                                            # print("-----> valid_elem_X")
                                                            self.url = self.driver.current_url
                                                            check = False
                                                            t = 0
                                                            while not check and len(elems_in_elem_in_year)>1 and t<5:
                                                                check = self.show_childs(elems_in_elem_in_year[n], "./div[1]/div/table/tbody/tr/td[4]/a", elems_in_year[k], "./div[1]/div/table/tbody/tr/td[3]/a")
                                                                t+=1

                                                            elems_in_elem_in_elem_in_year = self.extract_childs(elems_in_elem_in_year[n], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[6]/a")

                                                            self.check_part['elem_X'] = elem_X
                                                            if len(elems_in_elem_in_elem_in_year) == 0:
                                                                with self.workerThread.lock_file_check_part:
                                                                    check_part_storage = CheckPartStorage()
                                                                    check_part_storage.insert_check_part(self.check_part)
                                                                    check_part_storage.close_file()
                                                            m=0
                                                            while m < len(elems_in_elem_in_elem_in_year):
                                                                try:
                                                                    if len(elems_in_elem_in_elem_in_year[m].find_elements(By.XPATH, "./*")) > 3:

                                                                        elem_XX = elems_in_elem_in_elem_in_year[m].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[6]/a").text
                                                                        print(f"********{elem_XX}")

                                                                        self.elem_state["check_start_elem_XX"], self.elem_state["check_end_elem_XX"] = self.verify_start_elem(elem_XX, self.elem_state["start_elem_XX"], self.elem_state["end_elem_XX"], self.elem_state["check_start_elem_XX"], self.elem_state["check_end_elem_XX"], 4, self.elem_state)
                                                                        if not self.elem_state["check_start_elem_XX"] and self.elem_state["check_end_elem_XX"]:
                                                                            break
                                                                        if self.elem_state["check_start_elem_XX"]:
                                                                            # print("-----> valid_elem_XX")
                                                                            self.url = self.driver.current_url
                                                                            check = False
                                                                            t = 0
                                                                            while not check and len(elems_in_elem_in_elem_in_year)> 1 and t<5:
                                                                                check = self.show_childs(elems_in_elem_in_elem_in_year[m], "./div[1]/div/table/tbody/tr/td[5]/a", elems_in_elem_in_year[n], "./div[1]/div/table/tbody/tr/td[4]/a")
                                                                                t+=1

                                                                            partStorage = PartStorage(file_path= f'results/{self.nom_valide(part.Brand)}/{self.nom_valide(part.Brand)}_{self.thread_id}')

                                                                            elems_in_elem_in_elem_in_elem_in_year = self.extract_childs(elems_in_elem_in_elem_in_year[m], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[7]/a")

                                                                            self.check_part['elem_XX'] = elem_XX
                                                                            if len(elems_in_elem_in_elem_in_elem_in_year) == 0:
                                                                                with self.workerThread.lock_file_check_part:
                                                                                    check_part_storage = CheckPartStorage()
                                                                                    check_part_storage.insert_check_part(self.check_part)
                                                                                    check_part_storage.close_file()
                                                                            z=0
                                                                            while z < len(elems_in_elem_in_elem_in_elem_in_year):
                                                                                try:
                                                                                    part_name = elems_in_elem_in_elem_in_elem_in_year[z].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[7]/a").text
                                                                                    print(f"**********{part_name}")
                                                                                    
                                                                                    self.elem_state["check_start_part_name"], self.elem_state["check_end_part_name"] = self.verify_start_elem(part_name, self.elem_state["start_part_name"], self.elem_state["end_part_name"], self.elem_state["check_start_part_name"], self.elem_state["check_end_part_name"], 5, self.elem_state)
                                                                                    if not self.elem_state["check_start_part_name"] and self.elem_state["check_end_part_name"]:
                                                                                        break
                                                                                    if self.elem_state["check_start_part_name"]:
                                                                                        # print("-----> valid_part_name")
                                                                                        self.url = self.driver.current_url
                                                                                        if len(elems_in_elem_in_elem_in_elem_in_year) > 1:
                                                                                            check = False
                                                                                            t = 0
                                                                                            while not check and len(elems_in_elem_in_elem_in_elem_in_year)>1 and t<5:
                                                                                                check = self.show_childs(elems_in_elem_in_elem_in_elem_in_year[z], "./div[1]/div/table/tbody/tr/td[6]/a", elems_in_elem_in_elem_in_year[m], "./div[1]/div/table/tbody/tr/td[5]/a")
                                                                                                t+=1

                                                                                        info_list = self.extract_info(elems_in_elem_in_elem_in_elem_in_year[z], part.Brand, part.Model, part_name)

                                                                                        self.check_part['part_name'] = part_name
                                                                                        if len(info_list) == 0:
                                                                                            with self.workerThread.lock_file_check_part:
                                                                                                check_part_storage = CheckPartStorage()
                                                                                                check_part_storage.insert_check_part(self.check_part)
                                                                                                check_part_storage.close_file()
                                                                                        
                                                                                        for info in info_list:
                                                                                            part.products_name = part_name # + " " + info["manufacturer_part_number"]
                                                                                            part.price = info["price"]
                                                                                            part.manufacturer_part_number = info["manufacturer_part_number"]
                                                                                            part.description = elem_X + " " + elem_XX + " " + info["description"]
                                                                                            part.products_img = info["products_img"]
                                                                                            part.frontOrRear = info["frontOrRear"]
                                                                                            part.first_img_src = info["first_img_src"]
                                                                                            part.type = info["type"]
                                                                                            partStorage.insert_part(part)


                                                                                        ##############################
                                                                                        self.check_part['part_name'] = None
                                                                                        get_info = elems_in_elem_in_elem_in_elem_in_year[z].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[6]/a")
                                                                                        self.click_elem(get_info)
                                                                                    z=z+1
                                                                                    previous_is_error = False
                                                                                except Exception as e:
                                                                                    print("error in level 5 : ",e)
                                                                                    if not previous_is_error :
                                                                                        previous_is_error = True
                                                                                        print(self.url)
                                                                                        years_elem, elems_in_year, elems_in_elem_in_year, elems_in_elem_in_elem_in_year, elems_in_elem_in_elem_in_elem_in_year = self.refresh_page(self.url, level=5,i=i,j=j,k=k,n=n,m=m,z=z)
                                                                                        print("refresh_page finished z==",z)
                                                                                    else:
                                                                                        z+=1
                                                                            partStorage.close_file()
                                                                            self.check_part['elem_XX'] = None
                                                                            get_elems_in_elem_in_elem_in_elem_in_year = elems_in_elem_in_elem_in_year[m].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[5]/a")
                                                                            self.click_elem(get_elems_in_elem_in_elem_in_elem_in_year)
                                                                            
                                                                    m=m+1
                                                                    previous_is_error = False
                                                                except Exception as e:
                                                                    print("error in level 4 : ",e)
                                                                    if not previous_is_error :
                                                                        previous_is_error = True
                                                                        print(self.url)
                                                                        years_elem, elems_in_year, elems_in_elem_in_year, elems_in_elem_in_elem_in_year = self.refresh_page(self.url, level=4,i=i,j=j,k=k,n=n,m=m)
                                                                        print("refresh_page finished m==",m)
                                                                    else:
                                                                        m+=1
                                                            self.check_part['elem_X'] = None
                                                            get_elems_in_elem_in_elem_in_year = elems_in_elem_in_year[n].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[4]/a")
                                                            self.click_elem(get_elems_in_elem_in_elem_in_year)
                                                        n=n+1
                                                        previous_is_error = False
                                                    except Exception as e:
                                                        print("error in level 3 : ",e)
                                                        if not previous_is_error :
                                                            previous_is_error = True
                                                            print(self.url)
                                                            years_elem, elems_in_year, elems_in_elem_in_year = self.refresh_page(self.url, level=3,i=i,j=j,k=k,n=n)
                                                            print("refresh_page finished n==",n)
                                                        else:
                                                            n+=1
                                                self.check_part['model'] = None
                                                get_elems_in_elem_in_year = elems_in_year[k].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[3]/a")
                                                self.click_elem(get_elems_in_elem_in_year)
                                            k=k+1
                                            previous_is_error = False
                                        except Exception as e:
                                            print("error in level 2 : ",e)
                                            if not previous_is_error :
                                                previous_is_error = True
                                                print(self.url)
                                                years_elem, elems_in_year = self.refresh_page(self.url, level=2,i=i,j=j,k=k)
                                                print("refresh_page finished k==",k)
                                            else:
                                                k+=1
                                    self.check_part['year'] = None
                                    get_elems_in_year = years_elem[j].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[2]/a")
                                    self.click_elem(get_elems_in_year)
                                j=j+1
                                previous_is_error = False
                            except Exception as e:
                                print("error in level 1 : ",e)
                                if not previous_is_error :
                                    previous_is_error = True
                                    print(self.url)
                                    years_elem = self.refresh_page(self.url, level=1,i=i,j=j)
                                    print("refresh_page finished j==",j)
                                else:
                                    j+=1
                        get_years_elem = self.elements[i].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[1]/a")
                        self.click_elem(get_years_elem)
                
                i=i+1
                previous_is_error = False
            except Exception as e:
                print("error in level 0 : ",e)
                if not previous_is_error :
                    previous_is_error = True
                    print(self.url)
                    self.refresh_page(self.url, level=0,i=i)
                    print("refresh_page finished i==",i)
                else:
                    i+=1

    def extract_liste_brand_dic(self):
        previous_is_error = False
        i=0
        while i < len(self.elements):
            try:
                part = Part()

                if len(self.elements[i].find_elements(By.XPATH, "./*")) > 3:
                    part.brand_name = self.elements[i].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[2]/a").text
                    part.Brand = part.brand_name
                    print(part.brand_name)

                    self.elem_state["check_start_brand"], self.elem_state["check_end_brand"] = self.verify_start_elem(part.brand_name, self.elem_state["start_brand"], self.elem_state["end_brand"], self.elem_state["check_start_brand"], self.elem_state["check_end_brand"], 0, self.elem_state)
                    if not self.elem_state["check_start_brand"] and self.elem_state["check_end_brand"]:
                        break
                    if self.elem_state["check_start_brand"]:
                        # print("----->valid_brand")
                        self.url = self.driver.current_url
                        # Créer le dossier 'images/BRAND' s'il n'existe pas
                        if not os.path.exists(f'images/{self.nom_valide(part.Brand)}'):
                            os.makedirs(f'images/{self.nom_valide(part.Brand)}')
                        if not os.path.exists(f'results/{self.nom_valide(part.Brand)}'):
                            os.makedirs(f'results/{self.nom_valide(part.Brand)}')

                        get_years_elem = self.elements[i].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[1]/a")
                        self.click_elem(get_years_elem)
                        time.sleep(1) ######
                        
                        years_elem = self.extract_childs(self.elements[i], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[3]/a")

                        self.check_part['brand'] = part.Brand
                        if len(years_elem) == 0:
                            with self.workerThread.lock_file_check_part:
                                check_part_storage = CheckPartStorage()
                                check_part_storage.insert_check_part(self.check_part)
                                check_part_storage.close_file()
                        j=0
                        while j < len(years_elem):
                            try:
                                part.Year = years_elem[j].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[3]/a").text
                                print(f"**{part.Year}")

                                self.elem_state["check_start_year"], self.elem_state["check_end_year"] = self.verify_start_elem(part.Year, self.elem_state["start_year"], self.elem_state["end_year"], self.elem_state["check_start_year"], self.elem_state["check_end_year"], 1, self.elem_state)
                                if not self.elem_state["check_start_year"] and self.elem_state["check_end_year"]:
                                    break
                                if self.elem_state["check_start_year"]:
                                    # print("-----> valid_year")
                                    self.url = self.driver.current_url
                                    check = False
                                    t = 0
                                    while not check and len(years_elem)>1 and t<5:
                                        check = self.show_childs(years_elem[j], "./div[1]/div/table/tbody/tr/td[2]/a", self.elements[i], "./div[1]/div/table/tbody/tr/td[1]/a")
                                        t+=1

                                    elems_in_year = self.extract_childs(years_elem[j], "./div[2]/*", "./div[1]/div/table/tbody/tr/td[4]/a")
                                    self.check_part['year'] = part.Year
                                    if len(elems_in_year) == 0:
                                        with self.workerThread.lock_file_check_part:
                                            check_part_storage = CheckPartStorage()
                                            check_part_storage.insert_check_part(self.check_part)
                                            check_part_storage.close_file()
                                            
                                    liste_brand_dic = []
                                    k=0
                                    while k < len(elems_in_year):
                                        try:
                                            part.Model = elems_in_year[k].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[4]/a").text
                                            print(f"****{part.Model}")

                                            brand_dic ={}
                                            brand_dic["start_brand"]= part.Brand
                                            brand_dic["start_year"]= part.Year
                                            brand_dic["start_model"]= part.Model
                                            brand_dic["end_brand"]= part.Brand
                                            brand_dic["end_year"]= part.Year
                                            brand_dic["end_model"]= part.Model
                                            
                                            liste_brand_dic.append(brand_dic)
                                            
                                            k=k+1
                                            previous_is_error = False
                                        except Exception as e:
                                            print("error in level 2 : ",e)
                                            if not previous_is_error :
                                                previous_is_error = True
                                                print(self.url)
                                                years_elem, elems_in_year = self.refresh_page(self.url, level=2,i=i,j=j,k=k)
                                                print("refresh_page finished k==",k)
                                            else:
                                                k+=1
                                    self.check_part['year'] = None
                                    get_elems_in_year = years_elem[j].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[2]/a")
                                    self.click_elem(get_elems_in_year)
                                    
                                    listeBrandDic = ListeBrandDic(part.Brand)
                                    listeBrandDic.insert_liste_brand_dic(liste_brand_dic)
                                    
                                j=j+1
                                previous_is_error = False
                            except Exception as e:
                                print("error in level 1 : ",e)
                                if not previous_is_error :
                                    previous_is_error = True
                                    print(self.url)
                                    years_elem = self.refresh_page(self.url, level=1,i=i,j=j)
                                    print("refresh_page finished j==",j)
                                else:
                                    j+=1
                        get_years_elem = self.elements[i].find_element(By.XPATH, "./div[1]/div/table/tbody/tr/td[1]/a")
                        self.click_elem(get_years_elem)
                
                i=i+1
                previous_is_error = False
            except Exception as e:
                print("error in level 0 : ",e)
                if not previous_is_error :
                    previous_is_error = True
                    print(self.url)
                    self.refresh_page(self.url, level=0,i=i)
                    print("refresh_page finished i==",i)
                else:
                    i+=1