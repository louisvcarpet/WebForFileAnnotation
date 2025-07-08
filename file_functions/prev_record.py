from mysql_connector import MySqlConnector
from dotenv import load_dotenv
import pandas as pd
import os
load_dotenv()

def get_previous_record(file_name: str, page_num: int):
    """
    Retrieve the most recent record for a specific file and page number.
    If no record exists for the given file and page, return None.
    """
    connector = MySqlConnector(
        host=os.getenv("MYSQL_HOST"),
        database=os.getenv("MYSQL_DATABASE"),
        userN=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD") 
    )
    
    df = pd.read_sql_table("annotation_data", connector.engine)
    filtered = df[(df["file_name"] == file_name) & (df["page_num"] == page_num)]
    filtered = filtered.sort_values("updated_time", ascending=False)
  
    if not filtered.empty:
        return filtered.head(1)

    return None