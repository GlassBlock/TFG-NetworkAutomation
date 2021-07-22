# Automating network device configuration with Python
## Description
This repository contains sample code in Python to automate the configuration of different network devices through three different libraries (netmiko, ncclient and requests).

## Motivation
Automation is becoming a fundamental part in networking, therefore, this project aims to provide code examples to automate device configuration in an easy way through Python with different the main three different current technologies: CLI automation through SSH (netmiko); NETCONF automation through SSH (ncclient) and RESTCONF automation (requests).

## How to use
Scripts are ready for use, just execute the main file found in each of the folders and make sure the remote devices to be configured are accessible. To define the target hosts, modify the corresponding hosts.yaml file (sample file is included for each script), for the netmiko script, to target a Cisco IOS device with IP 192.168.43.91, whose configuration file is "A1v2.yaml", the correct definition would be the following:

```
hosts:
  - ip: 192.168.43.91
    ssh_user: admin
    ssh_password: adminpassword
    device_type: cisco_ios
    config_file: A1v2.yaml
```

Configuration is defined in the config file(s) identified in the hosts file (depending on the script, one or more config files may be defined); the following snippet corresponds to part of the configuration file "A2v2.yaml", which contains all the configuration changes desired for this device:

```
# Templates to be loaded
Templates:
  - IOS-BasicConf.jinja2
  - IOS-Interfaces.jinja2
  - IOS-VLAN.jinja2
  - IOS-STP.jinja2


### DEVICE CONFIGURATION ###
# Basic Configuration
hostname: A2
secret: 'enablepassword'
domain: 'GNS3Lab'
...
```

Lastly, templates defined in the Templates list must be defined to give formatting to the configuration included in the configuration file(s), the following snippet corresponds to file "IOS-VLAN.jinja2", which gives format to VLAN configuration as per Cisco IOS syntax:
```
{% for vlan in layer_2.vlans %}
    vlan {{ vlan.vlan }}
    name {{ vlan.name }}
{% endfor %}

vtp domain name {{ layer_2.vtp.vtp_domain }}
vtp version {{ layer_2.vtp.version }}
vtp mode {{ layer_2.vtp.mode }}
```

Due to the complexity of NETCONF requests, and the necessity that they be performed in a given order (to avoid inconsistent states and thus, rejection of the applied configuration), configuration is defined in several files. Moreover, as RESTCONF allows JSON formatted data, templates are not needed as the configuration can be defined and formatted at the same time in YAML, so this last script lacks jinja templates.


## Built with

- [jinja](https://github.com/pallets/jinja)
- [ncclient](https://github.com/ncclient/ncclient)
- [netmiko](https://github.com/ktbyers/netmiko)
- [requests](https://github.com/psf/requests)
- [yaml](https://github.com/yaml)
