import os
import time
import subprocess
import requests
import psycopg2
import json
import urllib.request
from github import Github

# Set up database credentials
host = os.environ['POSTGRES_HOST']
port = os.environ['POSTGRES_PORT']
name = os.environ['POSTGRES_DB']
user = os.environ['POSTGRES_USER']
password = os.environ['POSTGRES_PASSWORD']

# Set up Github credentials
github_token = os.environ['GITHUB_ACCESS_TOKEN']

# Specify the GitHub repository and path to the JSON files
repo_owner = 'brunobrn'
repo_name = 'dba-bot'
repo_path = 'commands'
json_path = 'commands/'

headers = {'Authorization': 'token ' + github_token}

login = requests.get('https://api.github.com/brunobrn/dba-bot', headers=headers)
print(login.json())

g = Github(github_token)

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

    if latest_commit_sha != last_commit:
        print('New commit detected')

        comparison = repo.compare(commit_latest.parents[0].sha, commit_latest.sha)

        changed_files = comparison.files
        print("Arquivos alterados no ultimo commit")

        changed = []
        for t in changed_files:
                changed.append(t.filename[9:])
        print(changed)

        contents = repo.get_contents(repo_path)
        print("Arquivos dentro do repositório")
        print(contents)

        print('---------------')


        # Parse the JSON response into a list of dictionaries
        json_files = []
        file_url_tst = []
        for file_info in json_files_info:
            file_url = file_info['download_url']
            file_url_changed = file_url.split(json_path, 1)[1]
            file_url_tst.append(file_url_changed)

            if file_url_changed in changed:
                file_response = urllib.request.urlopen(file_url)
                file_data = file_response.read().decode('utf-8')
                json_files.append(json.loads(file_data))


        # Filter out the specified fields from each dictionary in the list
        filtered_fields = ['database', 'execution_time', 'sql_command']
        database_field = ['database']
        execution_time_field = ['execution_time']
        sql_command_field = ['sql_command']

        filtered_json_files = [{field: item[field] for field in filtered_fields} for item in json_files]
        filtered_database_field = [{field: item[field] for field in database_field} for item in json_files]
        filtered_execution_time_field = [{field: item[field] for field in execution_time_field} for item in json_files]
        filtered_sql_command_field = [{field: item[field] for field in sql_command_field} for item in json_files]

        each_command = []

        for i in filtered_sql_command_field:
                each_command.append(i['sql_command'])

        database = filtered_database_field[0]
        database_name = database.get("database")


        execution_time = filtered_execution_time_field[0]
        execution_time_date = execution_time.get("execution_time")

        sql_command = filtered_sql_command_field[0]
        sql_command_code = sql_command.get("sql_command")

        print(database_name)
        print(execution_time_date)

        print(sql_command)

        print('---------------------after')



        db_config = {
            "host": os.environ["POSTGRES_HOST"],
            "port": os.environ["POSTGRES_PORT"],
            "dbname": os.environ["POSTGRES_DB"],
            "user": os.environ["POSTGRES_USER"],
            "password": os.environ["POSTGRES_PASSWORD"]
                }

        def execute_sql_commands(commands, db_config):
            conn = psycopg2.connect(**db_config)
            cur = conn.cursor()
            cur.execute(commands)
            conn.commit()
            cur.close()
            conn.close()

        for i in each_command:
               execute_sql_commands(i, db_config)
               print(f"Executando comando {i}")
    last_commit = latest_commit_sha
    

    time.sleep(30)

    ## Fazer o for dentro do parser para o json