
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

 

# MySQL Connector class using SQLAlchemy        


class MySqlConnector:
  
    def __init__(self, host, database, userN, password):
        self.host = host
        self.database = database
        self.userN = userN
        self.password = password
        self.engine = None
        self.connection = None
        try:
            # Automatically use the MySQL Connector driver with SQLAlchemy when the object is created
            engine_url = f"mysql+mysqlconnector://{self.userN}:{self.password}@{self.host}/{self.database}"
            self.engine = create_engine(engine_url)
            self.connection = self.engine.connect()
            print("Connected to MySQL database using SQLAlchemy")
        except SQLAlchemyError as e:
            print("Error while connecting to MySQL:", e)
        


    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("MySQL connection is closed")

    def execution(self, query, parameters=None):
        if self.connection is None:
            print("Connection is not established.")
            return None

        # Automatically detect the operation type
        operation_type = query.strip().split()[0].lower()

        try:
            result = self.connection.execute(text(query), parameters or {})

            if operation_type in ["insert", "update", "delete"]:
                self.connection.commit()
                print(f"{operation_type.capitalize()} operation successful.")
                return None
            elif operation_type == "select":
                data = result.fetchall()
                print("Read operation successful.")
                return data
            else:
                print("Unrecognized operation. No action committed.")
                return None

        except SQLAlchemyError as e:
            print(f"Error during {operation_type.upper()} operation:", e)
            return None
