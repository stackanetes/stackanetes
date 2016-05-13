# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import mock
import unittest
import os
from oslo_config import cfg
import yaml

from kolla_k8s.service import (_get_mount_path, _get_external_ip, _render_yml,
    _generate_generic_control, _generate_generic_init,
    _generate_generic_network_node, _generate_generic_compute_node)

RC_PATH = os.path.join(os.path.dirname(__file__), "../../rc")


class TestGetMountPath(unittest.TestCase):

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_both_path_are_specifed(self, mock_conf):
        mock_conf.return_value = "/foo/bar/host:/foo/bar/container"

        returned_dict = _get_mount_path("test")
        expected_dict = {"host_path": "/foo/bar/host",
                         "container_path": "/foo/bar/container"}
        self.assertEqual(expected_dict, returned_dict)

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_host_path_is_specifed(self, mock_conf):
        mock_conf.return_value = "/foo/bar/host:"

        returned_dict = _get_mount_path("test")
        expected_dict = {"host_path": "/foo/bar/host",
                         "container_path": ""}
        self.assertEqual(expected_dict, returned_dict)

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_opt_does_not_exist(self, mock_conf):
        mock_conf.side_effect = cfg.NoSuchOptError("")

        returned_dict = _get_mount_path("test")
        expected_dict = {}
        self.assertEqual(expected_dict, returned_dict)

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_invalid_type(self, mock_conf):
        mock_conf.return_value = 1

        self.assertRaises(AttributeError, _get_mount_path, "test")

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_if_service_name_is_changed(self, mock_conf):
        mock_conf.return_value = "test:test"

        _get_mount_path("foo-bar")
        mock_conf.assert_called_with("foo_bar_mpath")


class TestGetExternalIp(unittest.TestCase):

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_external_ip_exist(self, mock_conf):
        mock_conf.return_value = "10.10.10.10"

        returned_dict = _get_external_ip("test")
        expected_dict = {"external_ip": "10.10.10.10"}
        self.assertEqual(expected_dict, returned_dict)

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_external_ip_doesnt_exist(self, mock_conf):
        mock_conf.side_effect = cfg.NoSuchOptError("")

        returned_dict = _get_external_ip("test")
        expected_dict = {}
        self.assertEqual(expected_dict, returned_dict)

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_if_service_name_is_changed(self, mock_conf):
        mock_conf.return_value = "10.10.10.10"

        _get_external_ip("foo-bar")
        mock_conf.assert_called_with("foo_bar_external_ip")


class TestRenderYml(unittest.TestCase):

    def setUp(self):
        self.control_variables = {
            "service_name": "service-name",
            "service_type": "service",
            "image_version": "image_version",
            "memory": "1Mi",
            "ports": ["1"],
            "docker_registry": "docker_registry",
            "external_ip": None,
            "host_path": None,
            "container_path": None,

        }
        self.init_variables = {
            "service": "service",
            "service_name": "service-init",
            "image_version": "image_version",
            "docker_registry": "docker_registry",
        }

        self.nodes_variables = {
            "image_version": "image_version",
            "docker_registry": "docker_registry",
            "memory": "1Mi",
            "host_interface": "host_interface",
        }

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_with_one_port(self, mock_conf):
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.control_variables)
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/one_port.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare services
            self.assertEqual(expected_files.next(), generated_files.next())
            # compare ReplicationController
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_with_multiple_ports(self, mock_conf):
        self.control_variables["ports"] = ["1", "2"]
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.control_variables)
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/multiple_ports.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare services
            self.assertEqual(expected_files.next(), generated_files.next())
            # compare ReplicationController
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_with_external_ip(self, mock_conf):
        self.control_variables["external_ip"] = "1.2.3.4"
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.control_variables)
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/external_ip.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare services
            self.assertEqual(expected_files.next(), generated_files.next())
            # compare ReplicationController
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_with_external_ip(self, mock_conf):
        self.control_variables["external_ip"] = "1.2.3.4"
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.control_variables)
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/external_ip.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare services
            self.assertEqual(expected_files.next(), generated_files.next())
            # compare ReplicationController
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_without_service_type(self, mock_conf):
        self.control_variables["service_type"] = None
        self.control_variables["service_name"] = "service"
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.control_variables)
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/no_service_type.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare services
            self.assertEqual(expected_files.next(), generated_files.next())
            # compare ReplicationController
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_without_ports(self, mock_conf):
        self.control_variables["ports"] = ['']
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.control_variables)
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/no_ports.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare ReplicationController
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_with_mount_path(self, mock_conf):
        self.control_variables["host_path"] = "/foo/bar/host"
        self.control_variables["container_path"] = "/foo/bar/container"
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.control_variables)
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/mount_path.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare ReplicationController
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_with_emprtDir_path(self, mock_conf):
        self.control_variables["host_path"] = None
        self.control_variables["container_path"] = "/foo/bar/container"
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.control_variables)
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/emptyDir.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare ReplicationController
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_simple_init(self, mock_conf):
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.init_variables, "generic-init.yml.j2")
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/simple-init.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare pod
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_compute_node(self, mock_conf):
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.nodes_variables,
                               "generic-compute-node.yml.j2")
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/compute-node.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare pod
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")

    @mock.patch('kolla_k8s.service.CONF.k8s')
    def test_generating_network_node(self, mock_conf):
        mock_conf.yml_dir_path = RC_PATH
        yml_path = _render_yml(self.nodes_variables,
                               "generic-network-node.yml.j2")
        with open(yml_path, 'r') as stream:
            generated_files = yaml.load_all(stream.read())
        with open("./fake_templates/network-node.yml", 'r') as stream:
            expected_files = yaml.load_all(stream.read())
        try:
            # compare pod
            self.assertEqual(expected_files.next(), generated_files.next())

        except StopIteration:
            self.fail("Incorrect type of generated yml")


class TestGenerateGenericControl(unittest.TestCase):
    @mock.patch('kolla_k8s.service.CONF.kolla.tag', "test_image")
    @mock.patch('kolla_k8s.service.CONF.service.memory', "4Mi")
    @mock.patch('kolla_k8s.service.CONF.service.get')
    @mock.patch('kolla_k8s.service.CONF.k8s.docker_registry', "test_registry")
    @mock.patch('kolla_k8s.service._get_mount_path')
    @mock.patch('kolla_k8s.service._get_external_ip')
    @mock.patch('kolla_k8s.service._render_yml')
    def test_parsing(self, mock_render, mock_externalip, mock_mpath, mock_get):
        mock_get.return_value = ['1']
        mock_mpath.return_value = {}
        mock_externalip.retun_value = {}
        expected_dir = {
            "service_name": "service-api",
            "service_type": "service",
            "image_version": "test_image",
            "memory": "4Mi",
            "ports": ["1"],
            "docker_registry": "test_registry",
        }

        _generate_generic_control("service-api")
        mock_render.assert_called_once_with(expected_dir)


class TestGenerateGenericInit(unittest.TestCase):
    @mock.patch('kolla_k8s.service.CONF.kolla.tag', "test_image")
    @mock.patch('kolla_k8s.service.CONF.k8s.docker_registry', "test_registry")
    @mock.patch('kolla_k8s.service._render_yml')
    def test_parsing(self, mock_render):
        expected_dict = {
            "service_name": "service-init",
            "service": "service",
            "image_version": "test_image",
            "docker_registry": "test_registry",
        }

        _generate_generic_init("service-init")
        mock_render.assert_called_once_with(expected_dict,
                                            "generic-init.yml.j2")


class TestGenerateGenericNetworkNode(unittest.TestCase):
    @mock.patch('kolla_k8s.service.CONF.kolla.tag', "test_image")
    @mock.patch('kolla_k8s.service.CONF.k8s.docker_registry', "test_registry")
    @mock.patch('kolla_k8s.service.CONF.service.memory', "4Mi")
    @mock.patch('kolla_k8s.service.CONF.network.host_interface', "host_if")
    @mock.patch('kolla_k8s.service._render_yml')
    def test_parsing(self, mock_render):
        expected_dict = {
            "image_version": "test_image",
            "docker_registry": "test_registry",
            "memory": "4Mi",
            "host_interface": "host_if",
        }

        _generate_generic_network_node()
        mock_render.assert_called_once_with(expected_dict,
                                            "generic-network-node.yml.j2")


class TestGenerateGenericComputeNode(unittest.TestCase):
    @mock.patch('kolla_k8s.service.CONF.kolla.tag', "test_image")
    @mock.patch('kolla_k8s.service.CONF.k8s.docker_registry', "test_registry")
    @mock.patch('kolla_k8s.service.CONF.service.memory', "4Mi")
    @mock.patch('kolla_k8s.service.CONF.network.host_interface', "host_if")
    @mock.patch('kolla_k8s.service._render_yml')
    def test_parsing(self, mock_render):
        expected_dict = {
            "image_version": "test_image",
            "docker_registry": "test_registry",
            "memory": "4Mi",
            "host_interface": "host_if",
        }

        _generate_generic_compute_node()
        mock_render.assert_called_once_with(expected_dict,
                                            "generic-compute-node.yml.j2")


class TestGetNountPath(unittest.TestCase):
    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_both_paths(self, mock_get):
        mock_get.return_value = "/foo/bar/host:/foo/bar/container"

        returned_dict = _get_mount_path("service-init")
        expected_dict = {"host_path": "/foo/bar/host",
                         "container_path": "/foo/bar/container"}
        self.assertEqual(expected_dict, returned_dict)

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_only_container_path(self, mock_get):
        mock_get.return_value = ":/foo/bar/container"

        returned_dict = _get_mount_path("service-init")
        expected_dict = {"host_path": "",
                         "container_path": "/foo/bar/container"}
        self.assertEqual(expected_dict, returned_dict)

    @mock.patch('kolla_k8s.service.CONF.service.get')
    def test_only_host_path(self, mock_get):
        mock_get.return_value = "/foo/bar/host:"

        returned_dict = _get_mount_path("service-init")
        expected_dict = {"host_path": "/foo/bar/host",
                         "container_path": ""}
        self.assertEqual(expected_dict, returned_dict)
