#!/usr/bin/python

"""
Copyright 2019 Pystol (pystol.org).

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cpu_stress_pod

short_description: A module that stress cpu pods

version_added: "2.8"

description:
    - "A module that stress cpu pods."


options:
    namespace:
        default: default
    pod:
        default: random poisson
    amount:
        default: 10
    duration:
        default: 5

author:
    - "Carlos Camacho (@ccamacho)"
    - "Thomas Alfonso (@thomasaab)"
    - "Oscar Gerdel (@gerdeloscar)"
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  cpu_stress_pod:
    namespace: default
    distribution: poisson
    pod: random poisson
    amount: 10
    duration: 5
'''

RETURN = '''
fact:
    description: Actual facts
    type: str
    sample: Jane Doe is a smart cookie.
'''

FACTS = [
    "{name} is looking great today!",
    "{name} is a smart cookie.",
    "I’d choose {name}'s company over pizza anytime."
]


import matplotlib
matplotlib.use('Agg')
import random
from ansible.module_utils.basic import AnsibleModule
from scipy.stats import poisson
import matplotlib.pyplot as plt
from kubernetes import client
from kubernetes.client.rest import ApiException
import time
from kubernetes.stream import stream
import datetime
import os 
import subprocess

from ansible_collections.pystol.actions.plugins.module_utils.k8s_common import load_kubernetes_config


global_available = []
global_unavailable = []
global_kill = []


def inyect_cpu(name, namespace, module, duration):
    api_instance = client.CoreV1Api()
    module.log(msg="pod: " + name)
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
        'apt update; apt-get install -y stress-ng; stress-ng --version; stress-ng --cpu 8 --io 4 --vm 2 --vm-bytes 128M --timeout '+str(duration)+'m',
        ]
    resp = stream(api_instance.connect_get_namespaced_pod_exec,
                  name,
                  namespace,
                  command=exec_command,
                  stderr=True, stdin=False,
                  stdout=True, tty=False)

    print("Response: " + resp)
    module.log(msg="Response: " + resp)

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

def get_pod_by_name(namespace='',name=''):
    api_instance = client.CoreV1Api()
    try:
        resp = api_instance.read_namespaced_pod(name=name, namespace=namespace)
        return resp
    except ApiException as e:
        print("CoreV1Api->read_namespaced_pod: %s\n" % e)   

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        namespace=dict(type='str', required=True),
        pod=dict(type='str', required=True),
        amount=dict(type='int', required=True),
        duration=dict(type='int', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    rc = 0
    stderr = "err"
    stderr_lines = ["errl1", "errl2"]
    stdout = "out"
    stdout_lines = ["outl1", "outl1"]

    module.log(msg='test!!!!!!!!!!!!!!!!!')

    namespace = module.params['namespace']
    amount = module.params['amount']

    result = dict(
        changed=True,
        stdout=stdout,
        stdout_lines=stdout_lines,
        stderr=stderr,
        stderr_lines=stderr_lines,
        rc=rc,
    )

    result['fact'] = random.choice(FACTS).format(
        name=module.params['namespace']
    )


    # random numbers from poisson distribution
    n = amount
    a = 0
    duration = module.params['duration']
    load_kubernetes_config()
    configuration = client.Configuration()
    configuration.assert_hostname = False
    client.api_client.ApiClient(configuration=configuration)

    podName = module.params['pod']
    if(podName == 'random poisson'):
        data_poisson = poisson.rvs(mu=10, size=n, loc=a)
        counts, bins, bars = plt.hist(data_poisson)
        plt.close()
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
                to_be_cpu = random.sample(pod_list, len(pod_list))
            else:
                to_be_cpu = random.sample(pod_list, int(experiment))

            for pod in to_be_cpu:
                inyect_cpu(pod.metadata.name, pod.metadata.namespace, module, duration)
            global_kill.append((datetime.datetime.now(), int(experiment)))
            # time.sleep(10)
            print(datetime.datetime.now())
    else:
        pod = get_pod_by_name(namespace=namespace,name=podName)
        inyect_cpu(pod.metadata.name, pod.metadata.namespace, module, duration)
    print("Ending histogram execution")

    if module.check_mode:
        return result

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
