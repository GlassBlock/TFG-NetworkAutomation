from SSHAutomation import SSHAutomation


def main():
    SSHAutomation.initiate_connections('./hostFiles/hosts.yaml')


if __name__ == '__main__':
    main()
