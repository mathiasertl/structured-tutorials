###########################
Run a tutorial with Vagrant
###########################

You can use `Vagrant <https://developer.hashicorp.com/vagrant>`_ to run a tutorial inside one (or more)
virtual machines. This approach is slow and resource intensive, but ensures maximum isolation and allows you
to write and test tutorials that you would not want to run on the local system.

***************
Getting started
***************

Assuming you have Vagrant installed, getting started is very simple.

First, let's write a trivial tutorial file and tell `structured-tutorials` to use the Vagrant runner:

.. literalinclude:: /tutorials/vagrant-simple/tutorial.yaml
    :caption: tutorial.yaml
    :language: yaml

Then, in same folder as your :file:`tutorial.yaml`, place a simple :file:`Vagrantfile`:

.. literalinclude:: /tutorials/vagrant-simple/Vagrantfile
    :caption: Vagrantfile

.. structured-tutorial:: vagrant-simple/tutorial.yaml

You can now run your tutorial in Vagrant:

.. code-block:: console

   user@host:~$ structured-tutorial tutorial.yaml

Configure Vagrant environment
=================================

You can configure `environment variables used by Vagrant <https://developer.hashicorp
.com/vagrant/docs/other/environmental-variables>`_ invocation by using the `environment` option.

The most common example is to configure a different `VAGRANT_CWD <https://developer.hashicorp
.com/vagrant/docs/other/environmental-variables>`_. The default is the same directory as your tutorial YAML
file. For example, if you have the Vagrantfile in a subdirectory:

.. literalinclude:: /tutorials/vagrant-subdir/tutorial.yaml
    :caption: example/tutorial.yaml
    :language: yaml

.. literalinclude:: /tutorials/vagrant-subdir/subdir/Vagrantfile
    :caption: example/subdir/Vagrantfile

Use multiple VMs
================

Vagrant allows you to `define multiple VMs in a single Vagrantfile <https://developer.hashicorp
.com/vagrant/docs/multi-machine>`_. `structured-tutorials` allows you to
specify in which machine a particular part should run in via the `options` directive:

.. literalinclude:: /tutorials/vagrant-machines/tutorial.yaml
    :caption: tutorial.yaml
    :language: yaml

In this example the Vagrantfile specifies two VMs:

.. literalinclude:: /tutorials/vagrant-machines/Vagrantfile
    :caption: Vagrantfile

.. structured-tutorial:: vagrant-machines/tutorial.yaml

The first `commands` block will run in the `foo` VM:

.. structured-tutorial-part::

... while the second block will run in the `bar` VM:

.. structured-tutorial-part::

Prepare a custom base box
=========================

Sometimes you need to prepare a custom base box for the main tutorial. Known use cases are preparing a box
that already has some tools installed or changing the VM so that it connects using a different user.

The following tutorial is a contrived example showing a user how to set up PostgreSQL on a "db" host and
Nginx on a "web" host. VMs are started from a custom-built "base" box that already has some common tools
installed and allows SSH access as root:

.. literalinclude:: /tutorials/vagrant-prepare-box/tutorial.yaml
    :caption: tutorial.yaml
    :language: yaml

As per the `prepare_box` directive, we have to specify a Vagrantfile for the base box in the ``box/`` folder:

.. literalinclude:: /tutorials/vagrant-prepare-box/box/Vagrantfile
    :caption: box/Vagrantfile

And the provisioning script in the same location:

.. literalinclude:: /tutorials/vagrant-prepare-box/box/provision.sh
    :caption: box/provision.sh

And finally the main Vagrantfile specifying the `db` and `web` VMs from the tutorial configuration file:

.. literalinclude:: /tutorials/vagrant-prepare-box/Vagrantfile
    :caption: Vagrantfile

.. structured-tutorial:: vagrant-prepare-box/tutorial.yaml

The first `commands` block will run in the `web` VM:

.. structured-tutorial-part::

... while the second block will run in the `db` VM:

.. structured-tutorial-part::
