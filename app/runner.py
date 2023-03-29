import os
import time
import subprocess
import requests
import psycopg2
import json
import base64
import urllib.request
import random
from kubernetes import client, config
from github import Github

from get_secret import get_secret
from create_cron_job import create_pod


# host = os.environ['POSTGRES_HOST']
# port = os.environ['POSTGRES_PORT']
# name = os.environ['POSTGRES_DB']
# user = os.environ['POSTGRES_USER']
# password = os.environ['POSTGRES_PASSWORD']

# Set up Github credentials
github_token=""
# github_token = os.environ['GITHUB_ACCESS_TOKEN']
url = 'https://api.github.com/user'

# Specify the GitHub repository and path to the JSON files
repo_owner = 'brunobrn'
repo_name = 'dba-bot'
repo_path = 'commands'
json_path = 'commands/'



# Specify the k8s namespace
namespace = 'dba-bot'

headers = {'Authorization': f'token {github_token}'}
login = requests.get(url, headers=headers)

# if login.status_code == 200:
#     print('Authenticated')
# else:
#     print('Not authenticated')

g = Github(github_token)

req = urllib.request.Request(url)
req.add_header('Authorization', 'token ' + github_token)
response = urllib.request.urlopen(req)
response_data = response.read().decode('utf-8')
response_json = json.loads(response_data)

# if 'login' in response_json:
#     print('Authenticated')
# else:
#     print('Not authenticated')

# Make a GET request to the GitHub API to retrieve the latest commit for the repository

repo = g.get_user(repo_owner).get_repo(repo_name)
response = urllib.request.urlopen(f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits/main')
commits = json.loads(response.read().decode('utf-8'))
# last_commit = commits['sha']
# commit_sha = commits['sha']
# print(last_commit)
# print(commit_sha)

# isso é só para testar commit -1
repo = g.get_user(repo_owner).get_repo(repo_name)
commits = repo.get_commits()
last_commit = commits[1].sha
commit_sha = commits[1].sha
#

#####

while True:
    # Make a GET request to retrieve the contents of the JSON files at the specified commit SHA
    response = urllib.request.urlopen(f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{json_path}?ref={commit_sha}')
    json_files_info = json.loads(response.read().decode('utf-8'))

    repo = g.get_user(repo_owner).get_repo(repo_name)
    commits = repo.get_commits()

    latest_commit_sha = commits[0].sha
    commit_latest = repo.get_commit(latest_commit_sha)

    print(f'Data do ultimo commit: {commit_latest.commit.author.date}')
    print(f'SHA do ultimo commit: {latest_commit_sha}')
    print('---------------')

    if latest_commit_sha != last_commit:
        print('Novo commit detectado!')

        comparison = repo.compare(commit_latest.parents[0].sha, commit_latest.sha)

        changed_files = comparison.files

        changed = []
        for t in changed_files:
                changed.append(t.filename[9:])
        print(f"Arquivos alterados no ultimo commit: {changed}")

        if changed == ['']:
            last_commit = latest_commit_sha
            print(f'Houve commit, porem fora do diretório {repo_path}, ignorando arquivos desnecessários')
            # testar push com um arquivo fora, mais um dentro
        else:
            contents = repo.get_contents(repo_path)
            # print(f"Arquivos dentro do repositório: {contents}")
            # print('---------------')

            # Parse the JSON response into a list of dictionaries
            json_files = []
            file_url_download = []

            for file_info in json_files_info:
                file_url = file_info['download_url']
                # print(type(file_url))
                # print(f"file_url: {file_url}")
                file_url_changed = file_url.split(json_path, 1)[1]
                file_url_download.append(file_url_changed)

                if file_url_changed in changed:
                    file_response = urllib.request.urlopen(file_url)
                    # print(f"file_response: {file_response}")
                    file_data = file_response.read().decode('utf-8')
                    # print(f"file_data: {file_data}")
                    json_files.append(json.loads(file_data))
                    # print(f"json_files: {json_files}")
                    
            print("--11--")
            for i in json_files:
                json_filtered = i
                multiple = []
                if len(i) >= 2:
                    for x in i:
                         multiple.append(x)
                    print("json com 2 ou mais comandos")
                    print(len(multiple))
                else:
                    print("json com 1 comando")
                    database_field = i[0]["database"]
                    namespace_field = i[0]["namespace"]
                    execution_time_field = i[0]["execution_time"]
                    sql_command_field = i[0]["sql_command"]
                    # print(database_field)
                    # print(namespace_field)
                    # print(execution_time_field)
                    # print(sql_command_field)
                    secrets = get_secret(namespace=namespace_field, name=f'db-{database_field}')
                    host = base64.b64decode(secrets["DATABASE_HOST"]).decode('utf-8')
                    name = base64.b64decode(secrets["DATABASE_NAME"]).decode('utf-8')
                    password = base64.b64decode(secrets["DATABASE_PASSWORD"]).decode('utf-8')
                    port = base64.b64decode(secrets["DATABASE_PORT"]).decode('utf-8')
                    user = base64.b64decode(secrets["DATABASE_USERNAME"]).decode('utf-8')
                    db_config = {
                        "host": host,
                        "port": port,
                        "dbname": name,
                        "user": user,
                        "password": password
                        }
                    create_pod(database_field, execution_time_field, host, port, user, password, name, github_token, sql_command_field)
                    print(f"Comando agendado para a database: {database_field} no horário: {execution_time_field} com o comando: {sql_command_field}")


                print("-----")

            print("--22--")
            # Filter out the specified fields from each dictionary in the list
            # filtered_fields = ['database','execution_time', 'sql_command']
            # # filtered_fields = ['database','namespace','execution_time', 'sql_command']
            # database_field = ['database']
            # # namespace_field = ['namespace']
            # execution_time_field = ['execution_time']
            # sql_command_field = ['sql_command']

            # filtered_json_files = [{field: item[field] for field in filtered_fields} for item in json_files]
            # print('teste here')
            # print(filtered_json_files[0])
            # print(len(filtered_json_files))
            # print(filtered_json_files)
            # print('teste here')
            # filtered_database_field = [{field: item[field] for field in database_field} for item in json_files]
            # # filtered_namespace_field = [{field: item[field] for field in namespace_field} for item in json_files]
            # filtered_execution_time_field = [{field: item[field] for field in execution_time_field} for item in json_files]
            # filtered_sql_command_field = [{field: item[field] for field in sql_command_field} for item in json_files]
            print('----------------- here')

            each_command = []
            # for i in filtered_sql_command_field:
            #         each_command.append(i['sql_command'])

            # database = filtered_database_field[0]
            # database_name = database.get("database")

            # namespace = filtered_namespace_field[0]
            # namespace_name = namespace.get("namespace")

            # execution_time = filtered_execution_time_field[0]
            # execution_time_date = execution_time.get("execution_time")

            # sql_command = filtered_sql_command_field[0]
            # sql_command_code = sql_command.get("sql_command")

            # print(f"Database: {database_name}")
            # # print(f"Namespace: {namespace_name}")
            # print(f"Agendamento cron: {execution_time_date}")
            # print(f"Comando a ser executado: {sql_command}")

            # Get secrets from k8s
            # def get_secret(namespace, name):
            #     """
            #     Get a Kubernetes Secret with the specified name in the specified namespace.

            #     Args:
            #         namespace (str): The name of the Kubernetes namespace to retrieve the Secret from.
            #         name (str): The name of the Kubernetes Secret to retrieve.

            #     Returns:
            #         A dictionary containing the data stored in the Secret.
            #     """

            #     # Load the Kubernetes configuration from the default location.
            #     # config.load_incluster_config()
            #     config.load_kube_config()

            #     # Create a Kubernetes API client.
            #     api_client = client.CoreV1Api()

            #     # Get the Secret object from Kubernetes.
            #     secret = api_client.read_namespaced_secret(name=name, namespace=namespace)
            #     # print(secret)

            #     # Extract the data from the Secret object.
            #     data = secret.data

            #     # Convert the data from bytes to strings.
            #     for key, value in data.items():
            #         data[key] = value.encode('utf-8')

            #     return data
            
            

            # Set up database credentials
            # host = base64.b64decode(secrets["DATABASE_HOST"]).decode('utf-8')
            # name = base64.b64decode(secrets["DATABASE_NAME"]).decode('utf-8')
            # password = base64.b64decode(secrets["DATABASE_PASSWORD"]).decode('utf-8')
            # port = base64.b64decode(secrets["DATABASE_PORT"]).decode('utf-8')
            # user = base64.b64decode(secrets["DATABASE_USERNAME"]).decode('utf-8')

            # db_config = {
            #     "host": host,
            #     "port": port,
            #     "dbname": name,
            #     "user": user,
            #     "password": password
            #         }
            
            # Specify the name of CronJob And Pods
            



            # def create_pod(sql_command, db_config):
            #     # config.load_incluster_config()
            #     config.load_kube_config()
            #     api = client.BatchV1Api()
            #     random_id=random.randint(1,99999)
            #     cronjob_name = f"dba-runner-{database_name}-{random_id}"
            #     pod_manifest = {
            #         "apiVersion": "batch/v1",
            #         "kind": "CronJob",
            #         "metadata": {
            #             "name": cronjob_name
            #         },
            #         "spec": {
            #         # "schedule": "*/10 * * * *", # para testes manuais
            #         "schedule": execution_time_date,
            #             "jobTemplate":
            #             { "spec" : { 
            #                     "ttlSecondsAfterFinished": 600,
            #                 "template": {
            #                     "spec" : {
            #             "restartPolicy": "Never",
            #             "serviceAccountName": "dba-runner-sa",
            #             "nodeName": "ip-10-9-34-197.ec2.internal",
            #             "containers": [
            #                 {
            #                     "name": "dba-runner",
            #                     "image": "dlpco/dba-runner",
            #                     "env": [
            #                         {
            #                             "name": "POSTGRES_HOST",
            #                             "value": host
            #                         },
            #                         {
            #                             "name": "POSTGRES_PORT",
            #                             "value": port
            #                         },                        
            #                         {
            #                             "name": "POSTGRES_USER",
            #                             "value": user
            #                         },
            #                         {
            #                             "name": "POSTGRES_PASSWORD",
            #                             "value": password
            #                         },
            #                         {
            #                             "name": "POSTGRES_DB",
            #                             "value": name
            #                         },
            #                         {
            #                             "name": "GITHUB_ACCESS_TOKEN",
            #                             "value": github_token
            #                         },
            #                         {
            #                             "name": "SQL_COMMAND",
            #                             "value": sql_command
            #                         }
            #                     ],
            #                     "command": ["python"],
            #                     "args": ["runner_exec_sql.py"]
            #                 }
            #             ]
            #             # ,


            #             #                         "nodeSelector": [
            #             #     {
            #             # "beta.kubernetes.io/arch": "amd64"
            #             #         }
            #             #     ]
                            
            #         }
            #             }
                
            #     }}}}

            #     api.create_namespaced_cron_job(body=pod_manifest, namespace="dba-bot")

            # for i in json_files:
            #     create_pod(sql_command_code, db_config)
            #     print(f"Comando agendado para a database: {database_name} no horário: {execution_time_date} com o comando: {i}")
        print('---------------')
        last_commit = latest_commit_sha
        

        time.sleep(120)
    time.sleep(120)

## separar create pod function e get secrets em duas funcions diferentes e chamar dentro do if e else cada caso.