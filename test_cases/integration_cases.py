#!/usr/bin/python
'''
Faraday Penetration Test IDE - Community Version
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''
from unittest import TestCase
import unittest
import sys
sys.path.append('.')
import model.controller as controller
import plugins.core as plcore
from mockito import mock
from model import api
from model.hosts import Host, Interface, Service
from model.workspace import WorkspaceOnCouch, WorkspaceManager, WorkspaceOnFS
import random

def new_random_workspace_name():
    return ("aworkspace" + "".join(random.sample([chr(i) for i in range(65, 90) ], 10 ))).lower() 

def create_host(self, host_name="pepito", os="linux"):
    host = Host(host_name, os)
    self.model_controller.addHostSYNC(host)
    return host

def create_interface(self, host, iname="coqiuto", mac="00:03:00:03:04:04"):
    interface = Interface(name=iname, mac=mac)
    self.model_controller.addInterfaceSYNC(host.getName(), interface)
    return interface

def create_service(self, host, interface, service_name = "coquito"):
    service = Service(service_name)
    self.model_controller.addServiceToInterfaceSYNC(host.getID(),
                                interface.getID(), service)
    return service

class TestModelObjectCRUD(TestCase):
    """docstring for TestModelObjectCRUD"""

    @classmethod
    def setUpClass(cls):
        cls.model_controller = controller.ModelController(mock())
        api.setUpAPIs(cls.model_controller)

    def setUp(self):
        self.wm = WorkspaceManager(self.model_controller, mock(plcore.PluginController))
        workspace = self.wm.createWorkspace(new_random_workspace_name(), workspaceClass=WorkspaceOnCouch) 
        self.wm.setActiveWorkspace(workspace)

    def tearDown(self):
        # c = self.wm.removeWorkspace('test_workspace')
        pass


    def test_create_and_remove_host_from_controller(self):
        host1 = create_host(self, "coquito")
        hosts_ids = [ h.getID() for h in self.model_controller.getAllHosts() ]

        self.assertIn(host1.getID(), hosts_ids,
                                "Host not in controller")

        self.model_controller.delHostSYNC(host1.name)

        hosts_ids = [ h.getID() for h in self.model_controller.getAllHosts() ]
        self.assertNotIn(host1.getID(), hosts_ids,
                                "Host not deleted")

    def test_delete_interface(self):
        host1 = create_host(self, "coquito")
        interface1 = create_interface(self, host1, iname = "pepito")

        hosts_ids = [h.getID() for h in self.model_controller.getAllHosts()] 
        self.assertIn(host1.getID(), hosts_ids,
                                "Host not in controller")

        host1 = self.model_controller.getHost(host1.getID())

        import ipdb; ipdb.set_trace()
        interfaces_ids = [i.getID() for i in host1.getAllInterfaces()]
        self.assertIn(interface1.getID(), interfaces_ids,
                                "Interface not in host!")

        self.model_controller.delInterfaceSYNC(host1.getID(), "pepito")

        
        interfaces_ids = [i.getID() for i in
                self.model_controller.getHost(host1.getID()).getAllInterfaces()]

        self.assertNotIn(interface1.getID(), interfaces_ids,
                                "Interface not in host!")


    def test_delete_service(self):
        host1 = create_host(self, "coquito")
        interface1 = create_interface(self, host1, iname="pepito")
        service1 = create_service(self, host1, interface1)

        hosts_ids = [h.getID() for h in self.model_controller.getAllHosts()] 
        self.assertIn(host1.getID(), hosts_ids,
                                "Host not in controller")

        host1 = self.model_controller.getHost(host1.getID())
        interfaces_ids = [i.getID() for i in host1.getAllInterfaces()]
        self.assertIn(interface1.getID(), interfaces_ids,
                                "Interface not in host!")

        services_ids = [s.getID() for s in self.model_controller.getHost(host1.getID())
                        .getInterface(interface1.getID()).getAllServices() ]

        self.assertIn(service1.getID(), services_ids,
                                "Service not in Interface!")

        self.model_controller.delServiceFromInterfaceSYNC(host1.getID(),
                                    interface1.getID(), service1.getID())

        services_ids = [s.getID() for s in self.model_controller.getHost(host1.getID())
                        .getInterface(interface1.getID()).getAllServices() ]

        self.assertNotIn(service1.getID(), services_ids, \
                        "Service not deleted")

class TestWorkspaceCRUD(TestCase):
    """docstring for TestWorspace"""
    @classmethod
    def setUpClass(cls):
        cls.model_controller = controller.ModelController(mock())
        api.setUpAPIs(cls.model_controller)
    def setUp(self):
        self.wm = WorkspaceManager(self.model_controller,
                            mock(plcore.PluginController))

    def _test_switch_workspace_with_objects(self):
        workspace = self.wm.createWorkspace(new_random_workspace_name(),
                            workspaceClass=WorkspaceOnCouch)
        self.wm.setActiveWorkspace(workspace)

        host1 = create_host(self, "coquito")
        interface1 = create_interface(self, host1, iname="pepito")
        service1 = create_service(self, host1, interface1)


        self.assertIn(host1, self.model_controller.getAllHosts(),
                                "Host not in controller")
        self.assertIn(interface1, host1.getAllInterfaces(),
                                "Interface not in host!")
        self.assertIn(service1, interface1.getAllServices(),
                                "Service not in Interface!")

        workspace2 = self.wm.createWorkspace(new_random_workspace_name(),
                            workspaceClass=WorkspaceOnCouch)
        self.wm.setActiveWorkspace(workspace2)

        self.assertNotIn(host1, self.model_controller.getAllHosts(),
                                "Host in controller, should be removed when \
                                switching workspaces")

        self.wm.setActiveWorkspace(workspace)
        self.assertIn(host1, self.model_controller.getAllHosts(),
                                "Host not in controller")
        self.assertIn(interface1, host1.getAllInterfaces(),
                                "Interface not in host!")
        self.assertIn(service1, interface1.getAllServices(),
                                "Service not in Interface!")

    def test_remove_active_workspace(self):
        workspace = self.wm.createWorkspace(new_random_workspace_name(),
                            workspaceClass=WorkspaceOnCouch)

        self.wm.setActiveWorkspace(workspace)
        host1 = create_host(self, "coquito")

        self.wm.removeWorkspace(workspace.name)

        hosts_ids = [h.getID() for h in self.model_controller.getAllHosts()]
        self.assertNotIn(host1.getID(), hosts_ids,
            'Host not removed while removing active workspace')

    def _test_remove_active_workspace_fs(self):
        workspace = self.wm.createWorkspace(new_random_workspace_name(),
                            workspaceClass=WorkspaceOnFS)
        self.wm.setActiveWorkspace(workspace)
        host1 = create_host(self, "coquito")

        self.wm.removeWorkspace(workspace.name)

        self.assertNotIn(host1, self.model_controller.getAllHosts(),
            'Host not removed while removing active workspace')

    def _test_remove_another_workspace(self):
        workspace = self.wm.createWorkspace(new_random_workspace_name(),
                            workspaceClass=WorkspaceOnCouch)

        workspace2 = self.wm.createWorkspace(new_random_workspace_name(),
                            workspaceClass=WorkspaceOnCouch)

        self.wm.setActiveWorkspace(workspace)
        create_host(self, "coquito")
        self.wm.setActiveWorkspace(workspace2)
        self.wm.removeWorkspace(workspace.name)

        self.assertNotIn(workspace.name, self.wm.getWorkspacesNames(),
                        "Workspace not removed")
        self.assertIn(workspace2.name, self.wm.getWorkspacesNames(),
                        "Workspace removed while removing another workspace")


if __name__ == '__main__':
    unittest.main()

