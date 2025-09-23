# wait_for_db.py
import time
import psycopg2
from psycopg2 import OperationalError

while True:
    try:
        conn = psycopg2.connect(
            host="db",
            database="dashboard",
            user="postgres",
            password="postgres",
            port=5432
        )
        conn.close()
        print("Postgres pronto!")
        break
    except OperationalError:
        print("Aguardando Postgres...")
        time.sleep(2)
