import csv

class CheckPartStorage:
    def __init__(self, file_path="results/check_parts"):
        self.file_path = f"{file_path}.csv"
        self.fieldnames = [ 'brand',
                            'year',
                            'model',
                            'elem_X',
                            'elem_XX',
                            'part_name']
        
        self.file = open(self.file_path, 'a', newline='', encoding='utf-8-sig')
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
        
        # Check if the file is empty, then write the header
        if self.file.tell() == 0:
            self.writer.writeheader()

    def insert_check_part(self, check_part):
        data = {
            'brand' : check_part['brand'],
            'year' : check_part['year'],
            'model' : check_part['model'],
            'elem_X' : check_part['elem_X'],
            'elem_XX' : check_part['elem_XX'],
            'part_name' : check_part['part_name']
        }
        self.writer.writerow(data)

    def close_file(self):
        self.file.close()