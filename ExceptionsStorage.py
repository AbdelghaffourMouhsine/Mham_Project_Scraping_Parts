import csv
import threading

class ExceptionsStorage:
    def __init__(self, file_path="results/exceptions"):
        self.file_path = f"{file_path}.csv"
        self.fieldnames = ['thread_id',
                            'exception',
                            'brand_dic',
                            'proxy']
        self.lock = threading.Lock()
        
        self.file = open(self.file_path, 'a', newline='', encoding='utf-8-sig')
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
        
        # Check if the file is empty, then write the header
        if self.file.tell() == 0:
            self.writer.writeheader()

    def insert_exception(self, exception):
        data = {
            'thread_id' : exception['thread_id'],
            'exception' : exception['exception'],
            'brand_dic' : exception['brand_dic'],
            'proxy' : exception['proxy']
        }
        self.writer.writerow(data)

    def close_file(self):
        self.file.close()