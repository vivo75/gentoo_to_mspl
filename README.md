# hyvar for reconfiguring gentoo

Structure of the repository:

* guest: contains the script to save in the gentoo VM

* host: contains the code needed for the translation and computation of the new configuration
   - portage
      * portage.tar.bz2: copied from guest
      * usr: generated by uncompress-portage.sh
      * json
         1. mspl: generated by uncompress-portage.sh
         2. spl: generated by uncompress-portage.sh
         3. hyvarrec: generated by ....
   - configuration:
      * configuration.gz: copied from guest
      * world.gz: copied from guest 
      * json
         1. configuration.json: generated by uncompress-configuration.sh (current configuration)
         2. world: generated by uncompress-configuration.sh (this is the concatenation of user requests)
   - scripts: directory containing ulitity scripts and src 
   - uncompress-portage.sh
   - uncompress-configuration.sh
   - portage2hyvarrec.sh
   - run-hyvarrec.sh
      

 
  




TODO
----------------------
The VM of Gentoo used is available from https://www.osboxes.org/gentoo/

In particular the system was tested with Gentoo 201703 (CLI Minimal) - 64bit.

Note that the sshd service in the virtual machine needs to be started

```
service sshd start
```

``` 
Username: osboxes
Password: osboxes.org
Password for Root account: osboxes.org
```

Then to access the machine configure VirtualBox with a NAT and use ssh.
Assuming that the port 22 of the VM has been redirected to port 9022

```
ssh -p 9022 -o PubkeyAuthentication=no osboxes@localhost
```

To copy the files and extract the configuration and the portage tree structure the following commands need to be
executed from the gentoo_to_mspl directory.
```
scp -o PubkeyAuthentication=no -P 9022  -r guest/*  osboxes@localhost:
ssh -p 9022 -o PubkeyAuthentication=no osboxes@localhost 'echo osboxes.org | sudo -S ~/hyvar/compress-configuration.sh'
ssh -p 9022 -o PubkeyAuthentication=no osboxes@localhost 'echo osboxes.org | sudo -S ~/hyvar/compress-portage.sh'

scp -o PubkeyAuthentication=no -P 9022  osboxes@localhost:/home/osboxes/hyvar/gen/portage.tar.bz2 host/portage
scp -o PubkeyAuthentication=no -P 9022  osboxes@localhost:/home/osboxes/hyvar/gen/world.gz host/configuration
scp -o PubkeyAuthentication=no -P 9022  osboxes@localhost:/home/osboxes/hyvar/gen/configuration.gz host/configuration
```

Then when the files are saved to translate the files the following commands need to be exectued.
```
cd host
./uncompress-portage.sh
./uncompress-configuration.sh
./portage2hyvarrec.sh --no_opt

```

Remove the directory /etc/portage/package.use in the guest if present.
```
ssh -p 9022 -o PubkeyAuthentication=no osboxes@localhost 'echo osboxes.org | sudo -S rm -rf /etc/portage/package.use'
```

Then run
```
scp -o PubkeyAuthentication=no -P 9022  host/configuration/package.use host/configuration/update.sh osboxes@localhost:
ssh -p 9022 -o PubkeyAuthentication=no osboxes@localhost 'echo osboxes.org | sudo -S mv ~/package.use /etc/portage/'
ssh -p 9022 -o PubkeyAuthentication=no osboxes@localhost 'echo osboxes.org | sudo -S sh update.sh'
```

For the test in the VM for removing a package the following commands need to be performed.



TODO:
 
 world file needs to be transformed in json format
 check why some packages that can stay are removed (preferences???)
 generate the list of use flags for packages installed and removed (what do do with circular dependencies)
 sys-apps/kbd-2.0.3 can not be disinstalled
 

