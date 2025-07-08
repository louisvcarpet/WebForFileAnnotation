from datetime import datetime
from mysql_connector import MySqlConnector
from dotenv import load_dotenv
import pandas as pd
import os
from sqlalchemy import text
load_dotenv()

def updateDB(newAuthor: str, newDescription: str, page_num: int, file_name: str, old_time: str):
    connector = MySqlConnector(
        host=os.getenv("MYSQL_HOST"),
        database=os.getenv("MYSQL_DATABASE"),
        userN=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD")
    )

    new_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = """
        UPDATE data
        SET author = :author, description = :newDescription, updated_time = :new_time
        WHERE file_name = :file_name AND page_num = :page_num and updated_time = :old_time
    """

    params = {
        "author": newAuthor,
        "newDescription": newDescription,
        "new_time": new_time,
        "file_name": file_name,
        "page_num": page_num,
        "old_time": old_time}
 
    connector.execution(query, params)

