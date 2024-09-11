import threading
from PartInfoProcess import PartInfoProcess
from ExceptionsStorage import ExceptionsStorage

class WorkerThread(threading.Thread):
    lock_file_check_part = threading.Lock()
    lock_file_exceptions = threading.Lock()
    
    def __init__(self, thread_id, shared_list=None, proxyLoader=None,start_brand=None, start_year=None, start_model=None, start_elem_X=None, start_elem_XX=None, start_part_name=None, end_brand=None,end_year=None,end_model=None,end_elem_X=None,end_elem_XX=None,end_part_name=None, is_for_extract_models=False):
        
        super(WorkerThread, self).__init__()
        
        self.thread_id = thread_id
        self.shared_list = shared_list
        self.proxyLoader = proxyLoader
        
        self.brand_dic = None
        self.start_brand=start_brand
        self.start_year=start_year
        self.start_model=start_model
        self.start_elem_X=start_elem_X
        self.start_elem_XX=start_elem_XX
        self.start_part_name=start_part_name
        self.end_brand=end_brand
        self.end_year=end_year
        self.end_model=end_model
        self.end_elem_X=end_elem_X
        self.end_elem_XX=end_elem_XX
        self.end_part_name=end_part_name
        
        self.with_selenium_grid = True
        self.use_proxy = True
        
        self.proxy = None
        self.PROXY_HOST = '161.123.152.67' # rotating proxy or host
        self.PROXY_PORT =  6312 # port
        self.PROXY_USER = '*************' # username
        self.PROXY_PASS = '*************' # password

        self.is_for_extract_models = is_for_extract_models
        if self.is_for_extract_models :
            self.with_selenium_grid = False
            self.use_proxy = False
    def run(self):
        if self.is_for_extract_models:
            self.start_scraping()
        else:
            while True:
                try:
                    # Access the shared list synchronously
                    with self.shared_list.lock:
                        if not self.shared_list.data:
                            break  # The list is empty, the thread ends
    
                        self.brand_dic = self.shared_list.data.pop(0)
                        
                    with self.proxyLoader.lock:
                        self.proxy = self.proxyLoader.get_proxy(self.thread_id-1)
                    
                    self.init_start_end()
                    self.init_proxy()
                    
                    print(f"*"*100)
                    print(f"start brand_dic_item = {self.brand_dic} ||| by_thread_id = {self.thread_id} ||| with_proxy = {self.proxy}")
                    print(f"*"*100)
    
                    self.start_scraping()
    
                except Exception as e:
                    print(e)
                    with WorkerThread.lock_file_exceptions :
                        exceptionsStorage = ExceptionsStorage()
                        exceptionsStorage.insert_exception({"thread_id":self.thread_id,"exception":e,"brand_dic":self.brand_dic,"proxy":self.proxy})
                        exceptionsStorage.close_file()
                    
    
    def init_start_end(self):
        self.start_brand = self.brand_dic["start_brand"]
        self.start_year = self.brand_dic["start_year"]
        self.start_model = self.brand_dic["start_model"]
        self.end_brand = self.brand_dic["end_brand"]
        self.end_year = self.brand_dic["end_year"]
        self.end_model = self.brand_dic["end_model"]
        
    def init_proxy(self):
        self.PROXY_HOST = self.proxy["PROXY_HOST"] # rotating proxy or host
        self.PROXY_PORT = self.proxy["PROXY_PORT"] # port
        self.PROXY_USER = self.proxy["PROXY_USER"] # username
        self.PROXY_PASS = self.proxy["PROXY_PASS"] # password
        
    def start_scraping(self):
        partInfoProcess = PartInfoProcess(thread_id=self.thread_id, start_brand=self.start_brand, start_year=self.start_year, start_model=self.start_model, start_elem_X=self.start_elem_X, start_elem_XX=self.start_elem_XX, start_part_name=self.start_part_name, end_brand=self.end_brand, end_year=self.end_year, end_model=self.end_model, end_elem_X=self.end_elem_X, end_elem_XX=self.end_elem_XX, end_part_name=self.end_part_name, PROXY_HOST=self.PROXY_HOST, PROXY_PORT=self.PROXY_PORT, PROXY_USER=self.PROXY_USER, PROXY_PASS=self.PROXY_PASS, use_proxy=self.use_proxy, with_selenium_grid=self.with_selenium_grid, workerThread=self, is_for_extract_models=self.is_for_extract_models)
        