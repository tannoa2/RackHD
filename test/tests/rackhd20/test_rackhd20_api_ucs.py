'''
Copyright 2017, EMC, Inc.

Author(s):


'''

import fit_path
import os
import sys
import subprocess
import fit_common
import time


# Select test group here using @attr
from nose.plugins.attrib import attr
@attr(all=True, regression=True, smoke=True)
class rackhd20_api_nodes(fit_common.unittest.TestCase):

    UCS_IP = fit_common.fitcfg().get("ucs_ip")
    RACKHD_IP = fit_common.fitcfg().get("rackhd_host")
    MAX_WAIT = 20
    INITIAL_NODES = {}

    def wait_utility(self, id, counter ):
        """
        Recursevily wait for the ucs discovery workflow to finish
        :param id:
        :param counter:
        :return:
        """
        api_data = fit_common.rackhdapi('/api/2.0/workflows/' + id)
        status = api_data["json"]["status"]
        if status == "running" and counter < self.MAX_WAIT:
            time.sleep(1)
            if fit_common.VERBOSITY >= 1:
                print "status is {0} for the {1}'s run".format(status, counter)
            counter += 1
            self.wait_utility(id, counter)
        elif status == "running" and counter >= self.MAX_WAIT:
            if fit_common.VERBOSITY >= 1:
                print "status is {0} for the {1}'s run".format(status, counter)
            return False
        else:
            if fit_common.VERBOSITY >= 1:
                print "status is {0} for the {1}'s run".format(status, counter)
            return  True

    def get_nodes_utility(self):
        api_data = fit_common.rackhdapi('/api/2.0/nodes')
        self.assertEqual(api_data['status'], 200,
                         'Incorrect HTTP return code, expected 200, got:' + str(api_data['status']))

        for node in api_data['json']:
            self.INITIAL_NODES[node['id']]= node['type']

        if fit_common.VERBOSITY >= 1:
            print "Found {0} Nodes before cataloging the UCS".format(len(self.INITIAL_NODES))

    def restore_node_utility(self):
        api_data = fit_common.rackhdapi('/api/2.0/nodes')
        self.assertEqual(api_data['status'], 200,
                         'Incorrect HTTP return code, expected 200, got:' + str(api_data['status']))

        for node in api_data['json']:
            if node['id'] not in self.INITIAL_NODES:
                if fit_common.VERBOSITY >= 1:
                    print "Deleting Node: {0}".format(node['id'])
                api_data = fit_common.rackhdapi('/api/2.0/nodes/'+node['id'], action="delete")


    def test_api_20_ucs_discovery(self):
        self.get_nodes_utility()
        data_payload = { "name": "Graph.Ucs.Discovery",
                         "options":
                             {"defaults":
                                  { "username": "ucspe",
                                    "password": "ucspe",
                                    "ucs":self.UCS_IP,
                                    "uri": "http://" + self.RACKHD_IP +":7080/sys"
                                    }
                              }
                         }
        header = {"Content-Type": "application/json"}
        api_data = fit_common.rackhdapi("/api/2.0/workflows", action="post",
                                        headers=header, payload=data_payload)
        id = api_data["json"]["context"]["graphId"]
        self.assertEqual(api_data['status'], 201,
                         'Incorrect HTTP return code, expected 201, got:' + str(api_data['status']))


        self.wait_utility(id, 0)
        api_data = fit_common.rackhdapi('/api/2.0/nodes')
        self.assertEqual(api_data['status'], 200,
                         'Incorrect HTTP return code, expected 200, got:' + str(api_data['status']))

        counter = 0
        nodelist = []
        for node in api_data['json']:
            if node['obms'][0]["service"] == "ucs-obm-service":
                nodelist.append(node)


        self.restore_node_utility()


if __name__ == '__main__':
    fit_common.unittest.main()
