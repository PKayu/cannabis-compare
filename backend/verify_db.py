
from database import engine
from sqlalchemy import inspect

def verify_tables():
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("Tables found in the database:")
        for table in tables:
            print(f"- {table}")
        if not tables:
            print("No tables found in the database.")
    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")

if __name__ == "__main__":
    verify_tables()
