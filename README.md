# Item Catalog Web Application
This application provides a database of items within a variety of categories,
and is supported by a user registration and authentication system. Registered 
users have the ability to post, edit and delete their own items.

This project utilizes the following techniques:
* Flask Development Framework
* CRUD
* Third-party OAuth authentication

## How to Run
This application can be run from your local machine by following the steps
detailed below:

## Linux VM Installation
Setup can be performed via the steps below.

#### 1. Install VirtualBox
VirtualBox is the software that actually runs the virtual machine. You can
download it from virtualbox.org, [here](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1). Install the platform package for your operating system.

#### 2. Install Vagrant
Vagrant is the software that configures the VM and lets you share files
between your host computer and the VM's filesystem. Download and install
the version for your operating system [here.](https://www.vagrantup.com/downloads.html)

#### 3. Download the VM configuration
Download and unzip the following: [FSND-Virtual-Machine.zip.](https://s3.amazonaws.com/video.udacity-data.com/topher/2018/April/5acfbfa3_fsnd-virtual-machine/fsnd-virtual-machine.zip)
Inside of this directory is another called vagrant. `cd` into vagrant and
enter the command, `vagrant up`, to download and install the Linux operating
system.

Once the installation concludes, run `vagrant ssh` to run the the newly
installed VM.

## Initialize the database
Once the VM is up and running, `cd` into the `vagrant` directory and create
the database instance _catalog.db_ with the following command:
* `python database_setup.py`

Then, you may load some inital data entries with the following command:
* `python database_init.py`

Table names for this database: _Category_, _CatalogItem_, _User_


## Instructions to run this program:
Run the application with the following command:
* `python project.py`

The application is set by default to run at port 5000 from your local machine.
This may be altered by changing the designated port on _line 414_ of the `project.py` file.

In your browser navigate to the following; `http://localhost:5000/home`

## License
License information is available in the LICENSE.txt file.
