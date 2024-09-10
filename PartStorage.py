import csv

class PartStorage:
    def __init__(self, file_path="results/parts"):
        self.file_path = f"{file_path}.csv"
        self.fieldnames = ['trader_id', 'description', 'manufacturer_part_number',
       'brand_name', 'address', 'products_img', 'madeIn', 'price', 'is_offer',
       'offer_price', 'offer_start_date', 'offer_end_date', 'rating',
       'review_count', 'type', 'is_best_seller', 'is_mobilawy', 'assembly_kit',
       'product_line', 'frontOrRear', 'tyre_speed_rate', 'maximum_tyre_load',
       'tyre_engraving', 'rim_diameter', 'tyre_height', 'tyre_width',
       'kilometer', 'oil_type', 'battery_replacement_available', 'volt',
       'ampere', 'liter', 'color', 'Number_spark_pulgs', 'created_at',
       'businessCategories_id', 'enabled', 'products_name', 'warranty',
       'disabled_at', 'updated_at', 'status', 'qtyInStock', 'deletedAt',
       'Brand', 'Year', 'Model', 'first_img_src']
        
        self.file = open(self.file_path, 'a', newline='', encoding='utf-8-sig')
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
        
        # Check if the file is empty, then write the header
        if self.file.tell() == 0:
            self.writer.writeheader()

    def insert_part(self, part):
        data = {
            'trader_id' : part.trader_id, 
            'description' : part.description, 
            'manufacturer_part_number' : part.manufacturer_part_number,
            'brand_name' : part.brand_name, 
            'address' : part.address, 
            'products_img' : part.products_img, 
            'madeIn' : part.madeIn, 
            'price' : part.price, 
            'is_offer' : part.is_offer,
            'offer_price' : part.offer_price, 
            'offer_start_date' : part.offer_start_date, 
            'offer_end_date' : part.offer_end_date, 
            'rating' : part.rating,
            'review_count' : part.review_count, 
            'type' : part.type, 
            'is_best_seller' : part.is_best_seller, 
            'is_mobilawy' : part.is_mobilawy, 
            'assembly_kit' : part.assembly_kit,
            'product_line' : part.product_line, 
            'frontOrRear' : part.frontOrRear, 
            'tyre_speed_rate' : part.tyre_speed_rate, 
            'maximum_tyre_load' : part.maximum_tyre_load,
            'tyre_engraving' : part.tyre_engraving, 
            'rim_diameter' : part.rim_diameter, 
            'tyre_height' : part.tyre_height, 
            'tyre_width' : part.tyre_width,
            'kilometer' : part.kilometer, 
            'oil_type' : part.oil_type, 
            'battery_replacement_available' : part.battery_replacement_available, 
            'volt' : part.volt,
            'ampere' : part.ampere, 
            'liter' : part.liter, 
            'color' : part.color, 
            'Number_spark_pulgs' : part.Number_spark_pulgs, 
            'created_at' : part.created_at,
            'businessCategories_id' : part.businessCategories_id, 
            'enabled' : part.enabled, 
            'products_name' : part.products_name, 
            'warranty' : part.warranty,
            'disabled_at' : part.disabled_at, 
            'updated_at' : part.updated_at, 
            'status' : part.status, 
            'qtyInStock' : part.qtyInStock, 
            'deletedAt' : part.deletedAt,
            'Brand' : part.Brand, 
            'Year' : part.Year, 
            'Model' : part.Model,
            'first_img_src' : part.first_img_src
        }
        self.writer.writerow(data)

    def close_file(self):
        self.file.close()