from helper.config import get_settings, Settings
import os
import string
import random

class BaseControlls:
    def __init__(self):
        self.app_settings = get_settings()
        self.base_path = os.path.dirname(os.path.dirname(__file__))
        self.file_dir = os.path.join(self.base_path, "assets/","files")

        self.database_dir = os.path.join(
            self.base_path,
            "assets/","database"
            )
    
    def genertate_random_string(self,length: int = 12):
 
        letters_and_digits = string.ascii_letters + string.digits
        result_str = ''.join(random.choice(letters_and_digits) for i in range(length))
        return result_str
    

    def get_database_path(self, db_name: str):
        database_path = os.path.join(
            self.database_dir,
              db_name)
        if not os.path.exists(database_path):
            os.makedirs(database_path)
        return database_path
    


