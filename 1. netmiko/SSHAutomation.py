import datetime
import netmiko
import os
import threading
import yaml

from jinja2 import Environment, FileSystemLoader


class SSHAutomation:

    # Starts a new SSH connection instance and an empty list where configuration data
    # will be saved before being pushed to the network device
    def __init__(self, connect_params):
        self.connection = netmiko.ConnectHandler(**connect_params)
        self.tasks = list()

    # Loads all the commands from a variable containing valid configuration
    # in python type data (list and dict) and turns it into valid IOS commands
    # through the use of Jinja2 templates. It then adds the data to self.tasks.
    def load_configuration(self, config_data, template, path='./templates'):
        if not os.path.isdir(path):
            raise Exception('The given path does not exist.')

        jinja2_environment = Environment(loader=FileSystemLoader(path), lstrip_blocks=True, trim_blocks=True)
        jinja2_template = jinja2_environment.get_template(f'{template}')

        self.tasks.append(jinja2_template.render(config_data))

    # Commits all the specified configuration done on this script
    # through the SSH tunnel to make the changes effective on the device
    def push_tasks(self):
        for task in self.tasks:
            try:
                self.connection.send_config_set(task)
            except netmiko.ssh_exception.NetMikoTimeoutException:
                self.connection.clear_buffer()

    # Returns all the startup data configured on the network device.
    # If startup param is False, running data is returned instead
    def get_config(self, startup=True):
        if self.connection.check_config_mode():
            self.connection.exit_config_mode()

        if startup:
            return self.connection.send_command('show startup-config')

        return self.connection.send_command('show running-config')

    # Saves the configuration data on the network device
    def save_config(self):
        if self.connection.check_config_mode():
            self.connection.exit_config_mode()

        self.connection.send_command('write memory')

    # Returns current date in the following format:
    # DD.MM.YY-HH.MM.SS; Time is in 24h format
    @staticmethod
    def get_current_date():
        current_time = datetime.datetime.now()

        return f"{current_time.day}.{current_time.month}.{current_time.year}-{current_time.hour}." \
               f"{current_time.minute}.{current_time.second}"

    # Creates a text file where and appends to in all the information
    # contained in the data parameter
    @staticmethod
    def save_to_file(hostname, data, folder=''):
        path = './'

        if folder:
            if not os.path.exists(folder):
                os.mkdir(f'./{folder}')

            path += f'{folder}/'

        path += f'{hostname} {SSHAutomation.get_current_date()}.txt'
        out_file = open(path, 'w')
        out_file.writelines(data)
        out_file.close()
        print(f"Configuration data for {hostname} has been saved successfully at {path}.")

    # Starts a new connection and process all formats all the data given a list of templates
    # defined in the configuration file. Then, pushes all the commands to the device through push_tasks
    # saves the the configuration in the startup file and closes the connection.
    @staticmethod
    def load_full_config(host, config_file, save_config=True, save_config_to_file=True):
        new_connection = SSHAutomation(host)
        config_file_yaml = yaml.full_load(open(f'./confFiles/{config_file}'))

        for template in config_file_yaml['templates']:
            new_connection.load_configuration(config_file_yaml, template)

        new_connection.push_tasks()

        if save_config:
            new_connection.save_config()

        if save_config_to_file:
            SSHAutomation.save_to_file(config_file_yaml['hostname'], new_connection.get_config(), 'OutputData')

        new_connection.connection.cleanup()
        print(f"{config_file_yaml['hostname']} has been configured successfully.")

    # Extracts each host information from the given hosts file and its configuration filename
    # and passes that information to load_full_config() on a different thread
    @staticmethod
    def initiate_connections(hosts_file):
        devices = yaml.full_load(open(f'{hosts_file}'))

        for index, device in enumerate(devices['hosts']):
            host = {'device_type': device['device_type'],
                    'ip': device['ip'],
                    'username': device['ssh_user'],
                    'password': device['ssh_password']}

            new_thread = threading.Thread(target=SSHAutomation.load_full_config, args=(host, device['config_file']))
            new_thread.start()
