import datetime
import json
import requests
import threading
import yaml

from requests.auth import HTTPBasicAuth


class RESTCONFAutomation:

    def __init__(self, host_ip, host_port, username, password):
        self.uri = f'https://{host_ip}:{host_port}/'
        self.auth = HTTPBasicAuth(username, password)

    # Helper method to format the uris correctly
    def uri_formatter(self, data_uri):
        return f'{self.uri}restconf/data/{data_uri}'

    # Performs an HTTP GET method on the specified uri
    # and returns the payload
    def get_data(self, data_uri, rec_format='json'):
        headers = {'Accept': f'application/yang-data+{rec_format}'}

        http_request = requests.get(url=self.uri_formatter(data_uri=data_uri), headers=headers, verify=False,
                                    auth=self.auth)

        return http_request.text

    # Helper method that extracts the second line for a given YAML file
    # and returns only the key without extra characters such as brackets.
    @staticmethod
    def read_second_line(filename):
        with open(filename) as file:
            line = file.read().split("\n")[1]
            key = line[1:(len(line) - 2)]

        return key

    # Helper method which transforms YAML data into JSON
    # before returning it
    @staticmethod
    def yaml_to_json(yaml_file):
        with open(yaml_file) as file:
            return json.dumps(yaml.full_load(file))

    # Pushes a PATCH petition using the data yaml file
    # If headers is not defined, expected payload data will be in JSON (this method supports JSON data only)
    def modify_configuration(self, yaml_conf_filename, headers=None):
        file_loc = f'confFiles/{yaml_conf_filename}'

        key = RESTCONFAutomation.read_second_line(file_loc)
        formatted_uri = self.uri_formatter(data_uri=key)
        payload = RESTCONFAutomation.yaml_to_json(file_loc)

        if not headers:
            headers = {'Accept': 'application/yang-data+json', 'Content-Type': 'application/yang-data+json'}

        http_request = requests.patch(url=formatted_uri, headers=headers, auth=self.auth,
                                      verify=False, data=payload)
        if http_request.ok:
            print(f'PATCH Transaction for {yaml_conf_filename} file applied successfully.')
        else:
            print(f'PATCH Transaction for {yaml_conf_filename} file failed.')

    # Creates a RESTCONFAutomation instance with the given host_data
    # and process each configuration file defined in the host_data
    # before passing it to the modify_configuration method
    @staticmethod
    def create_connection_instance(host_data):
        new_connection = RESTCONFAutomation(host_data['ip'], host_data['port'], host_data['username'],
                                            host_data['password'])

        for section, conf_files in host_data['conf_files'].items():
            for conf_file in range(len(conf_files)):
                new_connection.modify_configuration(f'{section}/{conf_files[conf_file]}')

    # Read the hosts file and starts a new thread per host defined
    # targetting the create_connection_instance static method
    @staticmethod
    def load_hosts(hosts_file):
        yaml_hosts_file = yaml.full_load(open(hosts_file))

        for host in yaml_hosts_file['hosts'].values():
            new_thread = threading.Thread(target=RESTCONFAutomation.create_connection_instance, args=[host])
            new_thread.start()
