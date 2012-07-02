ELB Stats
=========

This is a tool that shows you the stats of instances attached to an ELB.

Requirements
------------

You will need to install:

* PyYAML
* boto
* dns resolver
* argparse

How to use
----------

Export you AWS keys in your shell, the proceed to run the script. All configuration you need is made through the YAML file. After that you call the script. The additional arguments are:

* ping: to show the ping of each server and the Load Balancer.
* oneline: prints out the name of all servers under the Load Balancer in one line, comma separated. Useful if you need to pass a command to all of them via dsh, for example.
* hostname: show the internal IP of the instances.

Invoke it like:

    $ python elb-stats.py ping
