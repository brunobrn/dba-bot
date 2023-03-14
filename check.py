import os
import time
import subprocess
import requests
from github import Github

# Set up Github credentials
github_token = os.environ['GITHUB_ACCESS_TOKEN']
g = Github(github_token)

# Set up database credentials
db_host = os.environ['POSTGRES_HOST']
db_port = os.environ['POSTGRES_PORT']
db_name = os.environ['POSTGRES_DB']
db_user = os.environ['POSTGRES_USER']
db_password = os.environ['POSTGRES_PASSWORD']

# Set up SQL command to execute
command = "psql -h {} -p {} -d {} -U {} -f {}"

# Set up repository details
repo_owner = 'brunobrn'
repo_name = 'dba-bot'
repo_path = 'sql'

# Set up last commit SHA
last_commit_sha = None

while True:
    # Get latest commit on repository
    repo = g.get_user(repo_owner).get_repo(repo_name)
    commits = repo.get_commits()
    latest_commit_sha = commits[0].sha
    
    # If the latest commit SHA is different from the last commit SHA
    # then a new commit has been made
    if latest_commit_sha != last_commit_sha:
        print('New commit detected')
        
        # Get list of files in the repository folder
        contents = repo.get_contents(repo_path)
        files = [f for f in contents if f.type == 'file']
        
        # For each file that was newly pushed to the repository
        for f in files:
            if f.sha != last_commit_sha:
                print(f'downloading and parsing file: {f.name}')
                
                # Download the file contents and parse the SQL commands
                file_contents = requests.get(f.download_url).text
                sql_commands = file_contents.split(';')
                
                # Execute each SQL command against the database
                for command in sql_commands:
                    if command.strip() != '':
                        subprocess.call(command.format(
                            db_host, db_port, db_name, db_user, db_password, f.name
                        ), shell=True)
                
        last_commit_sha = latest_commit_sha
    
    time.sleep(30)