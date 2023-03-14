
from flask import Flask, request
import psycopg2
import sqlparse
import requests
import base64
import os
import datetime
from kubernetes import client, config

app = Flask(__name__)

repo_owner = "brunobrn"
repo_name = "dba-bot"
path_to_sql_file = "sql.sql"

# Connect to PostgreSQL database
def connect_to_db():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST"),
        port=os.environ.get("POSTGRES_PORT"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        database=os.environ.get("POSTGRES_DB")
    )

db_config = connect_to_db()

# Authenticate with GitHub and download SQL commands
def get_sql_commands(repo_name, repo_owner, path_to_sql_file):
    headers = {"Authorization": f"Bearer {os.environ.get('GITHUB_ACCESS_TOKEN')}"}
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path_to_sql_file}"
    response = requests.get(url, headers=headers)
    sql_commands = response.json()["content"]
    sql_commands = base64.b64decode(sql_commands).decode("utf-8")
    return sql_commands

sql = get_sql_commands(repo_name,repo_owner,path_to_sql_file)

# Execute SQL commands
def execute_sql(sql, db_config):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"SQL command executed in database (colocar a env correta aqui) bug ? ")


# Create Kubernetes pod
def create_pod(sql_command, db_config):
    config.load_kube_config()
    api = client.CoreV1Api()

    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "a"
            # "name": f"sql-runner-{db_config['database']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        },
        "spec": {
            "containers": [
                {
                    "name": "sql-runner",
                    "image": "postgres:14.4",
                    "env": [
                        {
                            "name": "POSTGRES_HOST",
                            "value": db_config["host"]
                        },
                        {
                            "name": "POSTGRES_PORT",
                            "value": db_config["port"]
                        },
                        {
                            "name": "POSTGRES_USER",
                            "value": db_config["user"]
                        },
                        {
                            "name": "POSTGRES_PASSWORD",
                            "value": db_config["password"]
                        },
                        {
                            "name": "POSTGRES_DB",
                            "value": db_config["database"]
                        },
                        {
                            "name": "SQL_COMMAND",
                            "value": sql_command
                        }
                    ]
                }
            ]
        }
    }

    api.create_namespaced_pod(body=pod_manifest, namespace="dba-bot")
    print(f"Pod created for database {db_config['database']}")

# Listen for GitHub webhooks
@app.route("/", methods=["POST"])
def handle_webhook():
    event = request.headers.get("X-GitHub-Event")
    if event == "push":
        repo_name = request.json["repository"]["name"]
        repo_owner = request.json["repository"]["owner"]["login"]
        path_to_sql_file = request.json["commits"][0]["added"][0]
        sql_commands = get_sql_commands(repo_name, repo_owner, path_to_sql_file)
        sql_commands = sqlparse.split(sql_commands)
        db_configs = [
            {
                "host": "dba-pg-tools.homolog.stone.credit",
                "port": "5432",
                "database": "dba_pg_tools_database",
                "user": "dba_pg_tools_username",
                "password": "123456"
             }#,
            # {
            #     "host": "dba-pg-tools.homolog.stone.credit",
            #     "port": "5432",
            #     "database": "dba_pg_tools_database",
            #     "user": "dba_pg_tools_username",
            #     "password": "123456"
            # }
        ]
        for db_config in db_configs:
            for sql_command in sql_commands:
                create_pod(sql_command, db_config)
    return "OK"

# print(get_sql_commands(repo_name,repo_owner,path_to_sql_file)) ok
# handle_webhook()


# handle_webhook()



# execute_sql(sql, db_config)

# print(db_config)
# create_pod(sql,  db_config)
