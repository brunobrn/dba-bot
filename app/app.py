import os
import subprocess
import git
import yaml
import shutil
from kubernetes import client, config
from flask import Flask, request

host        = os.environ['POSTGRES_MAIN_HOST']
dbname      = os.environ['POSTGRES_MAIN_DB']
user        = os.environ['POSTGRES_MAIN_USER']
password    = os.environ['POSTGRES_MAIN_PASSWORD']
port        = os.environ['POSTGRES_MAIN_PORT']

repo_owner = "brunobrn"
repo_name = "dba-bot"
sql_path = "sql.sql"

git_user = "brunobrn"
git_repo = "dba-bot"
sql_file = "sql.sql"

app = Flask(__name__)

def get_sql_commands(repo_owner, repo_name, sql_path):
    repo_url = f"https://github.com/{repo_owner}/{repo_name}"
    git.Repo.clone_from(repo_url, f"/tmp/{repo_name}")
    with open(f"/tmp/{repo_name}/{sql_path}", "r") as f:
        sql_commands = f.read().split(";")
    sql_commands = [command.strip() for command in sql_commands if command.strip()]
    return sql_commands

def execute_sql_commands(sql_commands):
    psql_args = [
        "psql",
        # f"postgresql://{db_config['dba_pg_tools_username']}:{db_config['123456']}@{db_config['dba-pg-tools.homolog.stone.credit']}:{db_config['5432']}/{db_config['dba_pg_tools_database']}",
        f"postgresql://dba_pg_tools_username:123456@dba-pg-tools.homolog.stone.credit:5432/dba_pg_tools_database",
    ]
    subprocess.run(psql_args, input="\n".join(sql_commands), text=True, check=True)

def create_pod(sql_commands, db_config):
    with open("postgres-pod.yaml", "r") as f:
        pod_manifest = yaml.safe_load(f)
    pod_manifest["metadata"]["name"] = f"postgresql-{db_config['database']}"
    pod_manifest["metadata"]["namespace"] = "dba-bot"
    pod_manifest["spec"]["containers"][0]["image"] = "postgres:14.4"
    pod_manifest["spec"]["containers"][0]["env"] = [
        {
            "name": "POSTGRES_USER",
            "value": db_config["user"],
        },
        {
            "name": "POSTGRES_PASSWORD",
            "value": db_config["password"],
        },
        {
            "name": "POSTGRES_DB",
            "value": db_config["database"],
        },
        {
            "name": "SQL_COMMANDS",
            "value": "\n".join(sql_commands),
        },
        {
            "name": "SQL_HOST",
            "value": db_config["host"],
        },
        {
            "name": "SQL_PORT",
            "value": db_config["port"],
        },
    ]
    api = client.CoreV1Api()
    api.create_namespaced_pod(body=pod_manifest, namespace="dba-bot")

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.json
    repo_owner = data["repository"]["owner"]["name"]
    repo_name = data["repository"]["name"]
    sql_path = data["path"]
    sql_commands = get_sql_commands(repo_owner, repo_name, sql_path)
    db_configs = [
            {
                "host": "dba-pg-tools.homolog.stone.credit",
                "port": "5432",
                "database": "dba_pg_tools_database",
                "user": "dba_pg_tools_username",
                "password": "123456"
            },
            {
                "host": "dba-pg-tools.homolog.stone.credit",
                "port": "5432",
                "database": "dba_pg_tools_database",
                "user": "dba_pg_tools_username",
                "password": "123456"
            }
        ]

    for db_config in db_configs:
        execute_sql_commands(sql_commands, db_config)
        create_pod(sql_commands, db_config)
        print(f"SQL commands scheduled for execution in database {db_config['database']}")
    return "Web"

# execute_sql_commands(get_sql_commands(git_user, git_repo, sql_file))
handle_webhook()


shutil.rmtree("/tmp/dba-bot")