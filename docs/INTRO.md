# Overview

[oVirt Node](http://www.ovirt.org/Node) is a small scale operating system
acting as a hypervisor under the oVirt umbrella.
In general Node will behave more like a firmware than a general purpose
operating system.

This guide is intended for developers, it describes the design and
implementation of Node, to learn how to use and contribute to Node.

Node tries to meet a couple of goals:

+ **Stability** is a main goal. We want a reliable hypervisor.
+ **Ease of use** because it provides everything needed and is easy to administrate
+ **Upgrades & Rollback** to rollback if an upgrade fails or leads to an unstable environment
+ **Online & Offline Customization** for installing debugging packages and extending the base image
+ **Testable** to support the goal of being stable

Node is not aiming for the following goals:

+ General purpose operating system
+ Flexible
+ Package based
+ Minimal (tho we try to have an eye on bloat)


To read about Node's future or speak to other Node users you can check the
[wiki pages](http://www.ovirt.org/Node) and join our
[IRC channel](irc://irc.oftc.net/#ovirt).

