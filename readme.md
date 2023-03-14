To execute SQL commands in a Kubernetes environment when someone pushes a new SQL command into a GitHub repository with some data, you can use a combination of GitHub webhooks, Kubernetes API, and Python.

Here are the general steps to implement this:

Create a Kubernetes deployment and service: You will need to create a Kubernetes deployment and service to run the Python script that will listen for GitHub webhooks and create pods to execute SQL commands.

Create a Python script: You will need to create a Python script that listens for GitHub webhooks and creates pods to execute SQL commands. You can use the GitHub API to authenticate and download the repository, parse the SQL commands, and use the Kubernetes API to create pods.

Configure GitHub webhook: You will need to configure a webhook on your GitHub repository to trigger the Python script whenever a new SQL command is pushed.

Create a Kubernetes pod: You will need to create a Kubernetes pod to execute the SQL command. The pod can use a container image that has PostgreSQL and any necessary tools installed.


Here is an example of how you could implement this:

Create a Kubernetes deployment and service:

export POSTGRES_MAIN_HOST=dba-pg-tools.homolog.stone.credit
export POSTGRES_MAIN_DB=dba_pg_tools_database
export POSTGRES_MAIN_USER=dba_pg_tools_username
export POSTGRES_MAIN_PASSWORD=123456
export POSTGRES_MAIN_PORT=5432

``` yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dba-runner
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dba-runner
  template:
    metadata:
      labels:
        app: dba-runner
    spec:
      containers:
        - name: dba-runner
          image: postgres:14.4
          ports:
            - containerPort: 5000
          env:
            - name: POSTGRES_HOST
              value: <postgres-host>
            - name: POSTGRES_PORT
              value: <postgres-port>
            - name: POSTGRES_USER
              value: <postgres-user>
            - name: POSTGRES_PASSWORD
              value: <postgres-password>
            - name: POSTGRES_DB
              value: <postgres-db>
            - name: GITHUB_ACCESS_TOKEN
              value: <github-access-token>
---
apiVersion: v1
kind: Service
metadata:
  name: sql-runner
spec:
  selector:
    app: sql-runner
  ports:
    - protocol: TCP
      port: 5000
      targetPort: 5000
```
Create a Python script:

``` python

from flask import Flask, request
import psycopg2
import sqlparse
import os
from kubernetes import client, config

app = Flask(__name__)

# Connect to PostgreSQL database
def connect_to_db():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST"),
        port=os.environ.get("POSTGRES_PORT"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        database=os.environ.get("POSTGRES_DB")
    )

# Authenticate with GitHub and download SQL commands
def get_sql_commands(repo_name, repo_owner, path_to_sql_file):
    headers = {"Authorization": f"Bearer {os.environ.get('GITHUB_ACCESS_TOKEN')}"}
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path_to_sql_file}"
    response = requests.get(url, headers=headers)
    sql_commands = response.json()["content"]
    sql_commands = base64.b64decode(sql_commands).decode("utf-8")
    return sql_commands

# Execute SQL commands
def execute_sql(sql, db_config):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"SQL command executed in database {db_config['database']}")

# Create Kubernetes pod
def create_pod(sql_command, db_config):
    config.load_kube_config()
    api = client.CoreV1Api()

    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": f"sql-runner-{db_config['database']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        },
        "spec": {
            "containers": [
                {
                    "name": "sql-runner",
                    "image": "<your-postgres-image>",
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

    api.create_namespaced_pod(body=pod_manifest, namespace="<your-namespace>")
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
                "host": "<your-postgres-host-1>",
                "port": "<your-postgres-port-1>",
                "user": "<your-postgres-user-1>",
                "password": "<your-postgres-password-1>",
                "database": "<your-postgres-database-1>"
            },
            {
                "host": "<your-postgres-host-2>",
                "port": "<your-postgres-port-2>",
                "user": "<your-postgres-user-2>",
                "password": "<your-postgres-password-2>",
                "database": "<your-postgres-database-2>"
            }
            # Add more database configurations as needed
        ]
        for db_config in db_configs:
            for sql_command in sql_commands:
                create_pod(sql_command, db_config)
    return "OK"

```

This Python script listens for GitHub webhooks and downloads SQL commands from a specific file in the repository. It then creates a Kubernetes pod for each database configuration specified in the script and executes the SQL commands in each pod. The script uses the sqlparse library to split the SQL commands into individual statements. You can customize this script to fit your specific needs.









``` py

import os
import subprocess
import git
import yaml
from kubernetes import client, config
from flask import Flask, request

app = Flask(__name__)

def get_sql_commands(repo_owner, repo_name, sql_path):
    repo_url = f"https://github.com/{repo_owner}/{repo_name}"
    git.Repo.clone_from(repo_url, f"/tmp/{repo_name}")
    with open(f"/tmp/{repo_name}/{sql_path}", "r") as f:
        sql_commands = f.read().split(";")
    sql_commands = [command.strip() for command in sql_commands if command.strip()]
    return sql_commands

def execute_sql_commands(sql_commands, db_config):
    psql_args = [
        "psql",
        f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}",
    ]
    subprocess.run(psql_args, input="\n".join(sql_commands), text=True, check=True)

def create_pod(sql_commands, db_config):
    with open("postgres-pod.yaml", "r") as f:
        pod_manifest = yaml.safe_load(f)
    pod_manifest["metadata"]["name"] = f"postgresql-{db_config['database']}"
    pod_manifest["metadata"]["namespace"] = "<your-namespace>"
    pod_manifest["spec"]["containers"][0]["image"] = "<your-postgres-image>"
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
    api.create_namespaced_pod(body=pod_manifest, namespace="<your-namespace>")

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.json
    repo_owner = data["repository"]["owner"]["name"]
    repo_name = data["repository"]["name"]
    sql_path = data["path"]
    sql_commands = get_sql_commands(repo_owner, repo_name, sql_path)
    db_configs = [
            {
                "host": "<your-postgres-host-1>",
                "port": "<your-postgres-port-1>",
                "database": "database_a",
                "user": "<your-postgres-user>",
                "password": "<your-postgres-password>"
            },
            {
                "host": "<your-postgres-host-2>",
                "port": "<your-postgres-port-2>",
                "database": "database_b",
                "user": "<your-postgres-user>",
                "password": "<your-postgres-password>"
            },
            {
                "host": "<your-postgres-host-3>",
                "port": "<your-postgres-port-3>",
                "database": "database_c",
                "user": "<your-postgres-user>",
                "password": "<your-postgres-password>"
            }
        ]

    for db_config in db_configs:
        execute_sql_commands(sql_commands, db_config)
        create_pod(sql_commands, db_config)
        print(f"SQL commands scheduled for execution in database {db_config['database']}")
    return "Web
```

