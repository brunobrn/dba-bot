import time
import os
import requests
import json
import base64
import urllib.request
from github import Github

from config import repo_owner,repo_name,repo_path,json_path,headers,github_token,url
from get_secret import get_secret
from create_cron_job import create_pod

# Login/Add Header of github token into app.
login           = requests.get(url, headers=headers)
g               = Github(github_token)
req             = urllib.request.Request(url)
req.add_header('Authorization', 'token ' + github_token)
response        = urllib.request.urlopen(req)
response_data   = response.read().decode('utf-8')
response_json   = json.loads(response_data)

# Make a GET request to the GitHub API to retrieve the latest commit for the repository
repo        = g.get_user(repo_owner).get_repo(repo_name)
response    = urllib.request.urlopen(f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits/main')

# THIS 3 rows are for production, to test localy comment rows 27,28 and 29 and uncomment rows 32,33 and34
commits     = json.loads(response.read().decode('utf-8'))
last_commit = commits['sha']
commit_sha  = commits['sha']

# Block for localy tests
# commits     = repo.get_commits()
# last_commit = commits[1].sha
# commit_sha  = commits[1].sha

#####

while True:
    # Make a GET request to retrieve the contents of the JSON files at the specified commit SHA
    response            = urllib.request.urlopen(f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{json_path}?ref={commit_sha}')
    json_files_info     = json.loads(response.read().decode('utf-8'))
    commits             = repo.get_commits()
    latest_commit_sha   = commits[0].sha
    commit_latest       = repo.get_commit(latest_commit_sha)

    print(f'Data do ultimo commit: {commit_latest.commit.author.date}')
    print(f'SHA do ultimo commit: {latest_commit_sha}')

    if latest_commit_sha != last_commit:
        print('Novo commit detectado!')
        comparison      = repo.compare(commit_latest.parents[0].sha, commit_latest.sha)
        changed_files   = comparison.files
        changed         = []

        for t in changed_files:
                changed.append(t.filename[9:])
        print(f"Arquivos alterados no ultimo commit: {changed}")

        if changed == ['']:
            last_commit = latest_commit_sha
            print(f'Houve commit, porem fora do diretório {repo_name}/{repo_path}/, ignorando arquivos desnecessários')
        else:
            contents            = repo.get_contents(repo_path)
            json_files          = []
            file_url_download   = []

            for file_info in json_files_info:
                file_url            = file_info['download_url']
                file_url_changed    = file_url.split(json_path, 1)[1]
                file_url_download.append(file_url_changed)

                if file_url_changed in changed:
                    file_response   = urllib.request.urlopen(file_url)
                    file_data       = file_response.read().decode('utf-8')
                    json_files.append(json.loads(file_data))
                    
            for i in json_files:
                json_filtered = i
                multiple = []
                if len(i) >= 2:
                    for x in i:
                        multiple.append(x)
                        database_field = x["database"]
                        namespace_field = x["namespace"]
                        execution_time_field    = x["execution_time"]
                        sql_command_field       = x["sql_command"]
                        secrets                 = get_secret(namespace=namespace_field, name=f'db-{database_field}')
                        host                    = base64.b64decode(secrets["DATABASE_HOST"]).decode('utf-8')
                        name                    = base64.b64decode(secrets["DATABASE_NAME"]).decode('utf-8')
                        password                = base64.b64decode(secrets["DATABASE_PASSWORD"]).decode('utf-8')
                        port                    = base64.b64decode(secrets["DATABASE_PORT"]).decode('utf-8')
                        user                    = base64.b64decode(secrets["DATABASE_USERNAME"]).decode('utf-8')
                        db_config               = {
                                                    "host"      : host,
                                                    "port"      : port,
                                                    "dbname"    : name,
                                                    "user"      : user,
                                                    "password"  : password
                                                    }
                        create_pod(database_field, execution_time_field, host, port, user, password, name, github_token, sql_command_field)
                        # print(f"Comando agendado para a database: {database_field}, com o host: {host} no horário: {execution_time_field} com o comando: {sql_command_field}")
                        print("Comando agendado para a database:", db_config["dbname"],"com o host: ", db_config["host"], "no horário: ",execution_time_field," com o comando: ", sql_command_field)
                
                else:
                    database_field          = i[0]["database"]
                    namespace_field         = i[0]["namespace"]
                    execution_time_field    = i[0]["execution_time"]
                    sql_command_field       = i[0]["sql_command"]
                    secrets                 = get_secret(namespace=namespace_field, name=f'db-{database_field}')
                    host                    = base64.b64decode(secrets["DATABASE_HOST"]).decode('utf-8')
                    name                    = base64.b64decode(secrets["DATABASE_NAME"]).decode('utf-8')
                    password                = base64.b64decode(secrets["DATABASE_PASSWORD"]).decode('utf-8')
                    port                    = base64.b64decode(secrets["DATABASE_PORT"]).decode('utf-8')
                    user                    = base64.b64decode(secrets["DATABASE_USERNAME"]).decode('utf-8')
                    db_config               = {
                                                "host"      : host,
                                                "port"      : port,
                                                "dbname"    : name,
                                                "user"      : user,
                                                "password"  : password
                                                }
                    cronjob = create_pod(database_field, execution_time_field, host, port, user, password, name, github_token, sql_command_field)
                    print(f"Comando agendado para a database: {database_field} no horário cron: {execution_time_field} com o comando: {sql_command_field}", "e o nome da cronjob é: ", cronjob )

        last_commit = latest_commit_sha
        
        time.sleep(120)
    time.sleep(120)
