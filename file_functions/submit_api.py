from fastapi import FastAPI 
from enum import Enum 
from pydantic import BaseModel
from typing import Annotated, Optional, Dict, Any
from fastapi import Query
from datetime import datetime
from mysql_connector import MySqlConnector
from dotenv import load_dotenv
import pandas as pd
import os
load_dotenv()


app = FastAPI()
connector = MySqlConnector(
    host=os.getenv("MYSQL_HOST"),
    database=os.getenv("MYSQL_DATABASE"),
    userN=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD") 
)
@app.post("/submit")
def submit(file_name: str,author:str, page_num:str, description: str):


    """
    update into my dataframe in pandas and then upload to MySQL database
    """
   
    # df = pd.read_sql("data", connector.engine)
    # print(df)
    # Create a new row with the provided data
    new_row = {
        "file_name": file_name,
        "author": author,
        "page_num": page_num,
        "description": description,
        "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Append the new row to the DataFrame
    
    # df = pd.concat([df, pd.DataFrame(new_row)], axis=)
    df = pd.DataFrame([new_row])
    
    # Upload the updated DataFrame to MySQL
    df.to_sql("annotation_data", connector.engine, if_exists='append', index=False)
    return {"message": "Data submitted successfully", "annotation_data": new_row}


@app.post("/addFile")
def file_upload(author:str,file_name: str, file: bytes):

    """
    add file as data bytes into my dataframe in pandas and then upload to MySQL source_file table
    """
   
    # df = pd.read_sql("data", connector.engine)
    # print(df)
    # Create a new row with the provided data
    new_row = {
        "file_name": file_name,
        "author": author,
        "file":file
    }
    
    # Append the new row to the DataFrame
    
    # df = pd.concat([df, pd.DataFrame(new_row)], axis=)
    df = pd.DataFrame([new_row])
    
    # Upload the updated DataFrame to MySQL
    df.to_sql("source_file", connector.engine, if_exists='append', index=False)
    return {"message": "Data submitted successfully", "source_file": new_row}

@app.get("/showFiles")
def GetFile(userN:str):
    df = pd.read_sql_table("source_file", connector.engine)
    files_from_SameUser= df[df["author"] == userN]["file_name"]
    files_from_SameUser.reset_index(drop=True, inplace=True)
    files_from_SameUser.index = files_from_SameUser.index + 1
    files_from_SameUser.index.name = "Number"
    return files_from_SameUser 
        

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8070)