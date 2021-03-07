import matplotlib
matplotlib.use('Agg')
import random

from scipy.stats import poisson
import matplotlib.pyplot as plt
from kubernetes import client
from kubernetes.client.rest import ApiException
import time
from kubernetes.stream import stream
import datetime
import time
import os 
from kubernetes import config
import subprocess

def inyect_stress(name, namespace):
    api_instance = client.CoreV1Api()
    print("pod:" + name)
    try:
        resp = api_instance.read_namespaced_pod(name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            print("Unknown error: %s" % e)
            exit(1)
        # Calling exec and waiting for response
    exec_command = [
        '/bin/sh',
        '-c',
        'apt update; apt-get install -y stress-ng; stress-ng --version; stress-ng --vm 1 --vm-bytes 75% --vm-method all --verify -t 2m -v',
        ]
    resp = stream(api_instance.connect_get_namespaced_pod_exec,
                  name,
                  'default',
                  command=exec_command,
                  stderr=True, stdin=False,
                  stdout=True, tty=False)
    print("Response: " + resp)
   

        

def get_pods(namespace=''):
    api_instance = client.CoreV1Api()
    try:
        if namespace == '':
            api_response = api_instance.list_pod_for_all_namespaces()
        else:
            api_response = api_instance.list_namespaced_pod(
                namespace,
                field_selector='status.phase=Running')
        return api_response
    except ApiException as e:
        print("CoreV1Api->list_pod_for_all_namespaces: %s\n" % e)

def main():
    # contexts, active_context = config.list_kube_config_contexts()
    # if not contexts:
    #     print("Cannot find any context in kube-config file.")
    #     return
    # contexts = [context['name'] for context in contexts]
    # active_index = contexts.index(active_context['name'])
    # option, _ = pick(contexts, title="Pick the context to load",
    #                  default_index=active_index)

    namespace = 'default'
    amount = 1
    n = amount
    a = 0
    data_poisson = poisson.rvs(mu=10, size=n, loc=a)
    counts, bins, bars = plt.hist(data_poisson)
    plt.close()

    config.load_kube_config(os.getenv('KUBECONFIG'))
    configuration = client.Configuration()
    configuration.assert_hostname = False
    client.api_client.ApiClient(configuration=configuration)

    for experiment in counts:
        pod_list = get_pods(namespace=namespace)
        aux_li = []
        for fil in pod_list.items:
            if fil.status.phase == "Running":
                aux_li.append(fil)
        pod_list = aux_li

        # From the Running pods I randomly choose those to die
        # based on the histogram length
        print("-------")
        print("Pod list length: " + str(len(pod_list)))
        print("Number of pods to get: " + str(int(experiment)))
        print("-------")
        # In the case of the experiment being longer than the pod list,
        # then the maximum will be the lenght of the pod list
        if (int(experiment) > len(pod_list)):
            to_be_stress = random.sample(pod_list, len(pod_list))
        else:
            to_be_stress = random.sample(pod_list, int(experiment))

        for pod in to_be_stress:
            inyect_stress(pod.metadata.name,
                       pod.metadata.namespace)
        # time.sleep(10)
        print(datetime.datetime.now())


if __name__ == '__main__':
    main()