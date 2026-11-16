import psycopg2
from config.config import DB_CONFIG

class DatabaseManager:
    @staticmethod
    def get_connection():
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO gameverse, public;")
        return conn

    @staticmethod
    def test_connection():
        try:
            conn = DatabaseManager.get_connection()
            conn.close()
            return True, "Connected to GameVerse database successfully."
        except psycopg2.Error as e:
            return False, f"Database connection failed: {e.pgerror or str(e)}"

    @staticmethod
    def execute_query(query, params=None, fetch=False):
        conn = None
        cur = None
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute(query, params or ())
            if fetch:
                result = cur.fetchall()
                conn.commit()
                return True, result
            conn.commit()
            return True, None
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            err_msg = (e.pgerror or str(e)).split("\n")[0].replace("ERROR:  ", "")
            return False, err_msg
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
