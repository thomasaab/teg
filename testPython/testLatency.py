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

def inyect_latency(pod):
    print("%s\t%s\t%s" % (pod.status.pod_ip, pod.metadata.namespace, pod.metadata.name))
    
    for p in pod.status.container_statuses:  
       
        f = os.popen("docker inspect --format '{{ .State.Pid }}' " + p.container_id.replace('docker://', ''))
        now = f.read()
        # module.log(msg="test: " + "docker inspect --format '{{ .State.Pid }}' " + p.container_id.replace('docker://', ''))
        print("esperiment: "+ p.name  + " " + p.container_id.replace('docker://', ''))
        # res = os.system('echo %s|sudo -S %s' % ("toor", "sudo -S nsenter -t " + now + " -n tc qdisc add dev eth0 root netem delay 100ms"))
        # now2 = res.read()
        print(now)
        # list_files = subprocess.run(["sudo", "-S", "nsenter", "-t", str(int(now)), "-n", "tc", "qdisc", "add" , "dev" , "eth0" , "root" , "netem" , "delay" , "100ms" ])
        # print(list_files.returncode)
        res = os.popen("sudo nsenter -t " + now.rstrip("\n") + " -n tc qdisc add dev eth0 root netem delay 100ms")
        print("sudo nsenter -t " + now.rstrip("\n") + " -n tc qdisc add dev eth0 root netem delay 100ms")
        now2 = res.read()
        print("msj: " + now2)
        

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
            to_be_latency = random.sample(pod_list, len(pod_list))
        else:
            to_be_latency = random.sample(pod_list, int(experiment))

        for pod in to_be_latency:
            inyect_latency(pod)
        # time.sleep(10)
        print(datetime.datetime.now())


if __name__ == '__main__':
    main()