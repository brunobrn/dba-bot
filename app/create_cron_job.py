import random
from kubernetes import client, config

def create_pod(database_name, execution_time_date, host, port, user, password, name, github_token, sql_command_field):
    # If you are testing localy, use load_kube_config instead of load_incluster_config.
    config.load_incluster_config()
    # config.load_kube_config()
    api             = client.BatchV1Api()
    random_id       = random.randint(1,999999)
    cronjob_name    = f"dba-runner-{database_name}-{random_id}"
    pod_manifest    = {
                        "apiVersion": "batch/v1",
                        "kind": "CronJob",
                        "metadata": {
                            "name": cronjob_name
                        },
                        "spec": {
                        # "schedule": "*/10 * * * *", # para testes manuais
                        "schedule": execution_time_date,
                            "jobTemplate":
                            { "spec" : { 
                                    "ttlSecondsAfterFinished": 600,
                                "template": {
                                    "spec" : {
                            "restartPolicy": "Never",
                            "serviceAccountName": "dba-runner-sa",
                            "nodeName": "ip-10-9-34-197.ec2.internal",
                            "containers": [
                                {
                                    "name": "dba-runner",
                                    "image": "dlpco/dba-runner",
                                    "env": [
                                        {
                                            "name": "POSTGRES_HOST",
                                            "value": host
                                        },
                                        {
                                            "name": "POSTGRES_PORT",
                                            "value": port
                                        },                        
                                        {
                                            "name": "POSTGRES_USER",
                                            "value": user
                                        },
                                        {
                                            "name": "POSTGRES_PASSWORD",
                                            "value": password
                                        },
                                        {
                                            "name": "POSTGRES_DB",
                                            "value": name
                                        },
                                        {
                                            "name": "GITHUB_ACCESS_TOKEN",
                                            "value": github_token
                                        },
                                        {
                                            "name": "SQL_COMMAND",
                                            "value": sql_command_field
                                        }
                                    ],
                                    "command": ["python"],
                                    "args": ["runner_exec_sql.py"]
                                }
                            ]
                            # ,


                            #                         "nodeSelector": [
                            #     {
                            # "beta.kubernetes.io/arch": "amd64"
                            #         }
                            #     ]
                                
                                                }
                                            }
                                        }
                                    }
                                }
                            }

    api.create_namespaced_cron_job(body=pod_manifest, namespace="dba-bot")
    return cronjob_name