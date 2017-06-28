# hyvar for reconfiguring gentoo

**IMPORTANT: THE TRANSLATOR BRANCH IS BROKEN FOR NOW**

**TODO:**
* apply the profile to the data (need to define the functions, and call them)
* generate modularily the ids
* perform the smt translation to the spls that need it

## Structure of the repository:

Note that this structure is configurable in the main script hyportage.sh

* guest/hyvar: contains the script to save in the gentoo VM
    1. clean.sh: clean the guest VM off the installed scripts
    2. configuration.py: definition and manipulation functions of configuration data
    3. load_make_defaults.sh: bash script to load a make.defaults or make.conf portage file
    4. setup.sh: bash script to setup the right environment for the scripts
    5. sync.py: main script that extract variability information from the portage packages (no support for the repos.conf file yet)

* host: contains the code needed for the translation and computation of the new configuration
   - data
      * portage: contains all the data extracted from the guest gentoo VM
         1. packages/portage-tree: a copy of the egencache folder of the portage repository
         2. packages/deprecated: generated egencache files from the installed packages that are not available in portage anymore
         3. installed_packaes.json: lists the packages that are installed on the guest VM, with the selected use flags
         4. profile_configuration.json: stores the packages variability information stored in the guest VM profile
         5. user_configuration.json: stores the packages variability information defined by the user in the guest VM
      * hyportage: contains our translation of the gentoo packages with information related to their variability, and some annex usefull data
        1. hyportage.enc: contains the main information
        2. annex.enc: contains some annex data to speed up the update of the translation with a new version of portage
   - scripts: contains all the scripts for translating portage into hyportage, and for installing new packages.
      In particular:
      * translate-portage.py: translate the portage related information in host/data/portage into the corresponding hyportage representation
      * reconfigure.py: similar to gentoo's "emerge -vp", except that it also generates files to send to the guest VM to actually perform the package installation
   - hyportage.sh: the main script of this implementation. documentation of the commands is included



How to prepare the VM 
----------------------
Tor this example we consider the Gentoo VM available from https://www.osboxes.org/gentoo/

In particular the system was tested with Gentoo 201703 (CLI Minimal) - 64bit.

Our script will use ssh to connect to the VM. For this reason sshd demon needs to be started on the VM.
To do so please make sure that sshd is started and if not run the following command.
```
sudo service sshd start
```

Note that the credential to use the VM are the following.
``` 
Username: osboxes
Password: osboxes.org
Password for Root account: osboxes.org
```

To access the machine for the remaing of the running example we assume that it could be reached with the ssh protocol
at port 9022 (if VirtualBox is used this can be configured with a port forwarding).
Please verity to have access to the VM. As example this can be obtained as follows.
```
ssh -p 9022 -o PubkeyAuthentication=no osboxes@localhost
```

If the VM is reachable then run the following command that will install the necessary script in the VM and configurint 
portage to be in testing mode.
```
sh setup-guest.sh osboxes@localhost 9022
```



Getting data from the VM 
----------------------

To get the required information from the VM please run the following scripts.
```
sh get-configuration.sh osboxes@localhost 9022
sh get-portage.sh osboxes@localhost 9022
```

Note that this script for safety does not override existing data.
Please run the following script to delete local data TODO

The get-portage.sh script translates all the portage structure and it may take a lot of time (possibly hours).
However, this script needs to be executed only the portage tree is updated (previous the execution of the cleanup
scrip).

Reconfigure
----------------------

To run the reconfiguration run the following script.
```
sh reconfigure <request file> <keyword>
```

For example, to install git execute the following script.
```
sh reconfigure world amd64
```
where the world file is the following JSON file.
```
{
	"app-admin/sudo":{},
	"app-admin/syslog-ng":{},
	"sys-apps/dbus":{},
	"sys-boot/grub":{},
	"sys-kernel/genkernel":{},
	"sys-kernel/gentoo-sources":{},
	"dev-vcs/git":{}
}
```

Updating the VM
----------------------
To update the VM run the following script.
```
sh update-guest.sh osboxes@localhost 9022
```
This script move to the VM in the user home folder the installation script update.sh and set the configuration file
for the packages. The update script needs to be run on the VM by the user as follows.
```
sudo update.sh
```


Assumptions
----------------------
Packages installed that are not in the portage tree are not considered (working in progress to overcome this limitation).

fm, runtime, and local dependencies are all considered 

User can impose either constraint on slot + subslot or package versions when requiring packages (work in progress by
using the dependecies systax to ask for desiderata)

We work on testing mode of portage (e.g., we treat ~amd64 as amd64)

Package that are always visible (**) are treated as packages visible if they are stable on any architecture (*)

When the keyword is not specified for a package we do not consider its installation

Slot Operators
 - := is treated as :*
 - :SLOT= is treated as :SLOT

TODO:
------------------------ 
 sys-apps/kbd-2.0.3 can not be disinstalled
 
 makefile that will clean and all operations
 
 amd64 as default in script sh setup-guest.sh
 
 Both: change world structure file to allow user to disinstall packages + extend capabilities (version,slots)
 
 Michael: correct generation of world from gentoo also translating the profile in hyvarrec

 Both: find a way to deal with necessary packages (should be easy), and global use flags preference (more complex)
 
 Michael:  (packages are not separted by space for jacopo)
 The constraint in md5-cache are well translated (new lines and commas)
 
 Michael: refactor of the translation
 Note that here some dependencies are duplicated
   (e.g., dev-lang/perl:=[-build(-)] in app-text/po4a-0.45-r3)
 To minimize the work these repetitions should be removed

 Michael: handle the deprecated packages after an update
 
 Jacopo: remove slot o subslot variables in encoding
 
 Jacopo: install world of kde version into minimal gentoo version and check what happens
 
 Jacopo: incrementality of translation into hyvarrec
 
 Jacopo: try to unify both parsing of dependencies (talk with Michael)
 
 Michael: contact gentoo community
 
 Password in scripts

Python Requirements
-------------------

click
 
Task:
------------------------ 
Find configuration from which installing something can not be done in portage easily

