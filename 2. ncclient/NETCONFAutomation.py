import datetime
import os
import threading
import time
import xml.dom.minidom
import yaml

from jinja2 import Environment, FileSystemLoader
from ncclient import manager, xml_


class NETCONFAutomation:

    def __init__(self, connect_params):
        self.session = manager.connect(**connect_params)
        self.config_tasks = list()

    # Prints server capabilities
    def get_capabilities(self):
        for capability in self.session.server_capabilities:
            print(capability)

    # Applies all the configuration saved in the config_tasks instance variable onto the candidate datastore
    # on a device and commits it to make it effective on the running configuration
    def push_tasks(self):
        for task in self.config_tasks:
            self.session.edit_config(target='candidate', config=task)
            self.session.commit()

    # Returns current date in the following format:
    # DD.MM.YY-HH.MM.SS; Time is in 24h format
    @staticmethod
    def get_current_date():
        current_time = datetime.datetime.now()

        return f"{current_time.day}.{current_time.month}.{current_time.year}-{current_time.hour}." \
               f"{current_time.minute}.{current_time.second}"

    # Creates an xml file and stores in it the information contained
    # in the data parameter
    @staticmethod
    def save_to_file(hostname, data, folder_path=''):
        # XML data parse solution based on proposal found at:
        # https://www.fir3net.com/Networking/Protocols/how-to-operate-a-device-using-netconf-and-python.html
        pretty_data = xml.dom.minidom.parseString(str(data)).toprettyxml()

        if folder_path:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

        filepath = folder_path + f'/{hostname} {NETCONFAutomation.get_current_date()}.xml'
        out_file = open(filepath, 'w')
        out_file.writelines(pretty_data)
        out_file.close()

        print(f"Configuration data for {hostname} has been saved successfully as {filepath}.")

    # Parses all the information contained in each configuration file through its associated jinja2 template
    # and return all the parsed information as a list
    @staticmethod
    def parse_configuration(conf_file_list, hostname, template_path='./templates'):
        task_list = list()
        jinja2_environment = Environment(loader=FileSystemLoader(template_path), lstrip_blocks=True, trim_blocks=True)

        for conf_file in conf_file_list:
            conf_file_data = yaml.full_load(open(f'./confFiles/{hostname}/{conf_file}'))

            for template in conf_file_data["Template"]:
                jinja2_template = jinja2_environment.get_template(f'{template}')
                task_list.append(jinja2_template.render(conf_file_data))

        return task_list

    # Given the host data to start a NETCONF connection, the list of configuration devices in YAML, and the
    # hostname of a device, this method creates a new NETCONF connection, applies all the configuration to
    # a device and saves the running configuration on a device in a XML file.
    @staticmethod
    def load_full_data(host_data, config_files_list, hostname):

        new_connection = NETCONFAutomation(host_data)
        new_connection.config_tasks = NETCONFAutomation.parse_configuration(config_files_list, hostname)
        new_connection.push_tasks()

        if host_data['device_params']['name'] == 'csr':
            # IOS XE doesn't have a <startup> NETCONF datastore, so the following XML needs to be sent
            # to save the configuration in the startup_config
            # Source:
            # https://www.cisco.com/c/en/us/support/docs/storage-networking/management/200933-YANG-NETCONF-Configuration-Validation.html
            new_connection.session.dispatch(
                xml_.to_ele('<cisco-ia:save-config xmlns:cisco-ia="http://cisco.com/yang/cisco-ia"/>'))

        NETCONFAutomation.save_to_file(hostname, new_connection.session.get_config(source='running').data_xml,
                                       f'./OutputData/{hostname}')

    # Extracts each host information from the given hosts file and its configuration files
    # and starts passes that information to load_full_data() on a different thread
    @staticmethod
    def initiate_connections(hosts_file):
        devices = yaml.full_load(open(f'{hosts_file}'))

        for index, device in enumerate(devices['hosts']):
            time.sleep(3)
            host_data = {'device_params': {'name': device['device_type']},
                         'host': device['ip'],
                         'port': 830,
                         'username': device['ssh_user'],
                         'password': device['ssh_password'],
                         'hostkey_verify': False,
                         'manager_params': {"timeout": 90}}

            new_thread = threading.Thread(target=NETCONFAutomation.load_full_data,
                                          args=(host_data, device['config_files'], device['hostname']))
            new_thread.start()
