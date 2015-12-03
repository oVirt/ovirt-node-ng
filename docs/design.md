# Design

## Principles

A few principles provide the frame for the upcoming design decisions:

* Re-use existing and mature technologies (anaconda, lvm, cockpit)
* Fix upstream to fit our design
* Keep it simple
* Separate areas of responsibility (image vs installation vs image management
  & upgrade)


## Life-cycle Overview

Before diving into the technical details let us get overview over how the life
of an image is envisioned. Once we are aware of this, we can see what
components[^1] can be used to fill these stations.

[^1] When speaking of components, it is referred to another software project.

![The life-cycle of an image.](imgs/ngn-flow.dot.png)

As seen in the diagram above, and image is build, tested and published. These
actions are normally performed by a vendor or project, providing the image.

The image is **build** from a set of packages, normally consisting of a set of
packages for the core operating system, and a couple of packages to provide the
payload (in the oVirt case, vdsm is the payload).

The **testing** can be considered to perform some sanity tests to i.e.

- Ensure that the image is not corrupted,
- Essential packages are installed,
- But can also cover basic functional testing.

Once the image is good, it is **published** for further user consumption.


The remaining steps are the performed by users.


If a user needs extra packages inside the image, he can **customize** the image
before installation.

Once he is satisfied, the image is **installed** onto a host and ready to use.

At runtime the image is **administrated** through a user friendly UI.

Eventually **upgrades** are available and get installed. These upgrades either
end up successful or they fail. In case of a failure the **rollback** mechanism
is used to roll back into the state prior to the upgrade, to return to a
functioning system.


## Core technologies & concepts

In the light of the principles, the following (mainly) already existing
technologies were chosen to realize the flows above:

* Build: livemedia-creator (or koji)
* Delivery format: liveimg compatible squashfs
* Customization: guestfish
* Installation: anaconda
* Upgrade & Rollback: imgbased and LVM
* Administration: Cockpit

The file-system layout and related concepts are not a technology, but are
crucial for data persistence and the stability of upgrades and rollbacks.
The layout and concept is aligned to what other projects like
[OSTree](https://github.com/GNOME/ostree) and
["Project Stateless"](http://0pointer.net/blog/projects/stateless.html) aim
for.


## Detailed Flow

Now that we are aware of the components which come together to form Node, the following diagram illustrates in what flows they are used.

You might notice that the diagram contains a few previously unnamed components, no worries, we'll speak about them later on.

![](imgs/ngn-flow-components.dot.png)

By now we assume that you got an idea of how the life-cycle of a Node looks, and what components are used in the specific flows.
