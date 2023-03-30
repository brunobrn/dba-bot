import os
import psycopg2

# Set up database credentials
host = os.environ['POSTGRES_HOST']
port = os.environ['POSTGRES_PORT']
name = os.environ['POSTGRES_DB']
user = os.environ['POSTGRES_USER']
password = os.environ['POSTGRES_PASSWORD']
sql_command = os.environ['SQL_COMMAND']

db_config = {
    "host": host,
    "port": port,
    "dbname": name,
    "user": user,
    "password": password
            }

def execute_sql_commands(commands, db_config):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute(commands)
    conn.commit()
    cur.close()
    conn.close()

execute_sql_commands(sql_command, db_config)
print(f"Comando executado com sucesso no database: {name}, com o host: {host} e username: {user} - Comando executado: {sql_command} ")