import json

class ListeBrandDic:
    def __init__(self, file_path="liste_brand_dic"):
        self.file_path = f"results/ListBrandDic/{file_path}.json"
        
        # Try to read the existing data from the JSON file
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            # If file doesn't exist, initialize an empty list
            self.data = []

    def insert_liste_brand_dic(self, liste_brand_dic):
        # Append the new parts to the data list
        self.data.extend(liste_brand_dic)
        
        # Write the updated data list back to the JSON file
        with open(self.file_path, 'w', encoding='utf-8-sig') as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)
            
    def load_data(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            # If file doesn't exist, initialize an empty list
            self.data = []
        return self.data