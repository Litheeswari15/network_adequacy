import os
import psycopg2
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

def get_db_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        print("✅ PostgreSQL connected successfully!")
        return connection

    except Exception as e:
        print("❌ PostgreSQL connection failed!")
        print("Error:", e)
        return None


if __name__ == "__main__":
    connection = get_db_connection()

    if connection:
        print("✅ Database test successful!")
        connection.close()
        print("✅ Connection closed successfully!")
    else:
        print("❌ Database test failed!")