import urllib3

from RESTCONFAutomation import RESTCONFAutomation


def main():
    # This first line disables error messages when reuqests detects an insecure connection
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    RESTCONFAutomation.load_hosts(f'./hosts/hosts.yaml')


if __name__ == '__main__':
    main()
