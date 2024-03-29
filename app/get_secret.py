from kubernetes import client, config

def get_secret(namespace, name):
    """
    Get a Kubernetes Secret with the specified name in the specified namespace.

    Args:
        namespace (str): The name of the Kubernetes namespace to retrieve the Secret from.
        name (str): The name of the Kubernetes Secret to retrieve.

    Returns:
        A dictionary containing the data stored in the Secret.
    """

    # Load the Kubernetes configuration from the default location.
    # If you are doing test localy, use load_kube_config instead of load_incluster_config.
    config.load_incluster_config()
    # config.load_kube_config()

    # Create a Kubernetes API client.
    api_client  = client.CoreV1Api()

    # Get the Secret object from Kubernetes.
    secret      = api_client.read_namespaced_secret(name=name, namespace=namespace)
    # print(secret)

    # Extract the data from the Secret object.
    data        = secret.data

    # Convert the data from bytes to strings.
    for key, value in data.items():
        data[key] = value.encode('utf-8')

    return data