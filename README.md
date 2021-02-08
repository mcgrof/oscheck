# oscheck

oscheck is a framework to let you easily get
[fstests ](git://git.kernel.org/pub/scm/fs/xfs/xfstests-dev.git)
going, and running with the correct set of parameters for a specific
distribution / stable kernels.

oscheck relies on vagrant, terraform and ansible to get you going
with whatever your virtualization / bare metal / cloud provisioning
environment easily. The vagrant / terraform setup is completely
optional, however ansible *is* used to run oscheck across all hosts.

The nuts and bolts of deploying vagrant / terraform / and ansible to
get Linux through a git tree using a tag, compile Linux, and boot into
that kernel are all things which can obviously be shared with other projects.
As such this part of oscheck is now its own independent project,
[kdevops](https://gitlab.com/mcgrof/kdevops).

This project *shares* all components which other projects can benefit from
through [kdevops](https://gitlab.com/mcgrof/kdevops).

There are seven parts to the long terms ideals for oscheck:

1. Provisioning required virtual hosts for fstests purposes (filesystem
   specific). This is now folded into
   [kdevops](https://gitlab.com/mcgrof/kdevops)
2. Getting Linux, compiling and booting into it, also now folded into
   [kdevops](https://gitlab.com/mcgrof/kdevops).
3. Provisioning requirements for building fstests and installing oscheck
4. Running oscheck
5. Collecting results
6. Processing results
7. Updating expunge lists to detect regressions

Vagrant or terraform can optionally be used for the first part. Vagrant and
terraform are also used to kick off ansible basic machine configuration.
The expectation is that you stop using these utilities, vagrant or terraform,
after this step. After this you can use ansible for the later goals.

You then use ansible directly to get oscheck, requirements, build and install
it, along with partition setup for the systems.

Since oscheck has its own set of expunge lists, it is then used to let you run
fstests as easily as possible against the target test guests you have just
created. By default it should in theory never crash *iff* the distro you are
testing has the respective expunge files set for the filesystem you are
testing. This should let you run fstests against a custom kernel, for example,
to ensure you don't introduce regressions for changes.

Collecting results is next. oscheck uses xunit output files, but also processes
test `*.bad` files to determine where issues are found. A summary of results
by looking at xunit files for all sections run can be found in the file
`ansible/xunit_results.txt`. A summary of results by looking at all `*.bad`
files can be found on `bad_results.txt`.

The last step is to update the expunge list for your kernel, this done
automatically, so at the end of the `copy_results` tag for ansible you'd
end able to just run the following command to determine if you have found
regressions on the kernel you are testing:

```
git diff
```

Ideally each failure is properly tracked with a bz# (redhat) bsc# (suse) or a
respective kernel.org bugzilla (kz#) entry. It is expected someone should be
working on these issues.

## Features

What works:

  * Full vagrant provisioning
  * Initial terraform provisioning on different cloud providers
  * Deploy bare bones requirements on systems
  * If using vagrant, automatically update your ~/.ssh/config with the
    provisioned set of hosts so you can then use ansible directly.
  * If using terraform on OpenStack you'll get your ~/.ssh/config updated
    automatically as well.
  * Running ansible to get any Linux git repo, using a tag, compiling Linux,
    and booting into it
  * Running ansible to install dependencies on debian
  * Running oscheck to install dependencies on other distros
  * Running ansible for running oscheck or building a custom kernel and booting into it
  * Running oscheck with a set of expunge files
  * Collecting results
  * Processing them
  * Giving you a convenient way to determine if you have any regressions

## TODO

What's missing?

  * Storage setup when terraform is used in a consistent way for both /data and
    /media/truncated drives we can use for fstests. Right now the oscheck
    ansible playbook relies on at least two nvme drives to be available. This
    should be possible to just modify the tag used for the target label we
    look for to set up the truncated files on top of.
  * Provided you have a baseline and a development kernel with a set of
    of respective hosts, when a delta exists between a baseline kernel and
    a development kernel implies either regressions or that a fix was made.

    Fixes:

    However, since certain tests require running multiple times before a
    a failure, the fact that a test runs successfully during one shot fstests
    run does not imply a test is fixed. To verify fixes then, the only proper
    way to confirm a fix is to have a new task which can run against an input
    set of target tests to confirm a regressions. This task for instance would
    run for a count set number of times, say 1000 times. Only if a test did not
    fail after this count, would one consider a test fixed. The task could
    just use naggy-check.sh, which runs a test with a provided set number of
    counts or can run forever until a failure is detected.

    Regressions:

    We could re-use the same task as to confirm fixes to confirm regressions
    against the baseline kernel.

By default Debian testing is used where possible. Support for other
distributions has been added, however upkeeping it is up to the folks interested
in those distributions or the community to at least keep the expunge list up to
date.

## Provisioning

If you are using baremetal just skip the sections about using oscheck. If
you need to provision systems read on.

### Vagrant support - localized VMs

Vagrant is used to easily deploy oscheck non-cloud virtual machines. Below are
the list of providers supported:

  * Virtualbox
  * libvirt (KVM)

The following Operating Systems are supported:

  * OS X
  * Linux

The effort for using vagrant and terraform are now their own independent
project, [kdevops](https://gitlab.com/mcgrof/kdevops), since that effort is
very generic. This project shares code with that project for now for vagrant /
terraform and a the few of the core ansible roles which are shared.

For now a commit is done there and then merged here transparently as the
file structure is shared. In the future how code is shared may change
and is yet to be determined.

#### Provisioning with vagrant for oscheck

If on Linux we'll assume you are using KVM. If OS X we'll assume you are using
Virtualbox. If these assumptions are incorrect you can override on the
filesystem configuration file of your choise. To override the provider
set the environment variable `OSCHECK_VAGRANT_PROVIDER` with either
`virtualbox` or `libvirt`.

You are responsible for having a pretty recent system with some fresh
libvirt, or vitualbox installed. For instance, a virtualbox which supports
nvme. By default additional sparse files are used for the target disks
which will be used for testing fstests.

You are expected to be able to use oshceck as a regular user, no root
access is required. To use libvirt as a regular user refer to the
documentation on [kdevops](https://gitlab.com/mcgrof/kdevops) about
how to accomplish this.

Note that you will need to ensure the right group for the default
user which qemu will be spawned for matches the configuration. The
default group on oscheck is libvirt-qemu, as this is what is used
on Debian. Fedora uses the qemu group. To verride you can set the
environment variable:

```
export OSCHECK_VAGRANT_QEMU_GROUP=qemu
```

Read the [kdevops](https://gitlab.com/mcgrof/kdevops) documentaion about
apparmor/selinux and configuring libvirt if you run into issues with
permissions.

To run vagrant:

```bash
cd vagrant/
vagrant up
```

Say you want to just test the provisioning mechanism:

```bash
vagrant provision
```
##### Limitting vagrant's number of boxes

By default the using vagrant will try to create *all* the boxes specified on
the filesystem you are trying to test. By default this is xfs.yml and there
are currently 7 boxes there. If you are going to just test this framework
you can limit this initially using environment variables:

```bash
export OSCHECK_VAGRANT_LIMIT_BOXES="yes"
export OSCHECK_VAGRANT_LIMIT_NUM_BOXES=1
```

This will ensure only oscheck-xfs for example would be created and
provisioned. This might be useful if you are developing oscheck on a laptop,
for example, and you want to limit the amount of resources used by oscheck.

### Terraform support

Terraform is used to deploy oscheck on cloud virtual machines. Below are the
list of clouds currently supported:

  * azure
  * openstack (special minicloud support added)
  * aws

#### Provisioning with terraform with oscheck

```bash
cd terraform/you_provider
make deps
terraform init
terraform plan
terraform apply
```

## Running ansible

Before running ansible make sure you can ssh into the hosts listed on
ansible/hosts.

Ansible is *the* main supported mechanism by which we test with fstests.
Although using oscheck on bare metal is possible, you won't be parallelizing
your efforts if you do. If you use different virtual hosts for different
fstests sections, each section testing one specific way to configure your
filesystem, you could simply run all fstests on all hosts in parallel.
Even if you were using baremetal you could just ues ansible on a series of
bare metal nodes to also control them to parallelize your efforts.

Running oscheck.sh or check.sh manually therefore is expected only if
you need to test one specific test.

This means we have written roles for each main task. The aspect of doing a git
clone Linux, compiling Linux, booting into Linux is a generic concept which
obviously others can also used, as such this aspect of this project is now
shared with [kdevops](https://gitlab.com/mcgrof/kdevops) and it is expected
that we'd take advantage of it somehow later once its modularlized.

You'd use ansible to provision fstests and oscheck's dependencies, and install
all you need to get going with oscheck. You can also use it to optionally
compile Linux, and install it. And, you can also use it to *run* oscheck in
parallel on your shiny systems. Ansible is also used to collect results and
then process them, and finally show you regressions.

### Compiling your own kernel

Say you want to get a git repo of Linux, compile Linux, and reboot into it:

```bash
cd ansible/
ansible-playbook -i hosts bootlinux.yml
```

Be sure you are using a correct configuration. YMMV.

### Ansible bootlinux role

The bootlinux role is designed in [kdevops](https://gitlab.com/mcgrof/kdevops)
to allow you to git clone linux, get its dependencies to build, check out
a tag, apply a custom patch if needed, compile and install Linux. As well
as all other management of kernels -- such as manual uninstalls of a
specific kernel, updateing your grub for you.

Since this role is developed as a shared effort read the documentation for
it and how to use in the [kdevops](https://gitlab.com/mcgrof/kdevops) page.

### Ansible oscheck role

When first using the ansible oscheck role you want to use it one step at a
time. First try to manully call the oscheck role to limit it to only get
the repositories needed, get deps, build and install things. If that
succeeds, move on to the next step to limit the role to run oscheck.
Then if that succeeds a second step can be to collect and interpret results.

You can also further extend your hosts file to add more sections so that
you can customize and limit the calls to a set of group of hosts. Refer
to ansible/hosts file for an example set of groups.

First chnage to the ansible directory:

```
cd ansible
```

For the first step to get the repositories needed, build and install them
for a set of hosts:

```
ansible-playbook -i hosts -l dev --tags deps,git,build,install oscheck.yml
```

If that went well to now run the tests:
```

ansible-playbook -i hosts -l dev --tags run_tests oscheck.yml
```

Note that the above may fail for a few hosts, this is indicative of a
failure. This can mean a regression was found.

To collect results:

```
ansible-playbook -i hosts -l dev --tags run_tests,copy_results oscheck.yml
```

Now to see regressions just run:

```
git diff
```

If the above cycle worked well you can run test and collect in one shot:

```
ansible-playbook -i hosts -l dev --tags copy_results oscheck.yml
```

To run all tasks:

```bash
ansible-playbook -i hosts oscheck.yml
```

If you detect your nodes are hosed.. try to reset them on your hypervisor.
For instance consider using this if on KVM:

```
sudo virsh list
sudo virsh reset $name_of_vm_as_per_above
```

But you can also just reboot them manually, this may not work if the
system has crashed:

```
ansible-playbook -i hosts --tags reboot oscheck.yml
```

Need console access:

```
sudo virsh list
sudo virsh console $name_of_vm_as_per_above
```

### Running oscheck with ansible to do a full fstests run

To use ansible to run oscheck to do a full fstests run you would use:

```bash
$ cat ansible/extra_vars.yml
---
oscheck_run_tests: true
```
#### Quick tests

By default oscheck uses runs all tests except those present on the expunge
list. Making oscheck run `check.sh -g quick` is possible as follows:

```bash
$ cat ansible/extra_vars.yml
---
oscheck_run_tests: true
oscheck_extra_args: "-g quick"
```

However, experience shows currently no tests are run with. To use oscheck's
own interpetation of what a fast test are, you can use:

```bash
$ cat ansible/extra_vars.yml
---
oscheck_run_tests: true
oscheck_prefix_vars: "--fast-tests"
```

This will enable the `FAST_TEST` option of oscheck.sh.

```bash
cd ansible/
ansible-playbook -i hosts oscheck.yml --tags "run_tests"
```

# oscheck's primary objective: track a baseline for XFS on latest Linux and Linux stable kernels

oscheck's primary objective is to track baselne results of running fstests for
XFS against:

  * linux-next
  * linux
  * linux-stable kernels listed as supported on kernel.org
  * xfs-linux for-next branch

Different filesystems support can be added at a later time, if there is
interest and a willing maintainer for its respective entries.

## Setup for Tracking xfs-linux for-next branch with a localversion file

oscheck determines which expunge files to use for your kernel buy looking at
your running kernel with uname -r. Since we want to track both Linus' latest
tree, and also xfs-linux for-next branch, and since xfs-linux is based on Linus'
latest tree if we booted into a for-next branch for xfs-linux we'd end up with
the same uname -r. To distinguish these kernels you are encouraged to add an
extra file when building the for-next branch.

The kernel build system appends a tag to your build if you have any file
named prefixed with "localversion-", as such we recommend adding a
localversion-xfs file and with a date to reflect the date matching
the date for you checked out the for-next branch. For instance:

	oscheck@linuxnext-xfs ~/xfs-next (git::xfs-next)$ cat localversion-xfs
	-xfs-20180713

This will produce the following uname -r:

	oscheck@linuxnext-xfs ~/xfs-next (git::xfs-next)$ uname -r
	4.18.0-rc4-xfs-20180713+

This enables oscheck in turn to be able to look at the following directory for
its respective expunge files:

	expunges/4.18.0-rc4-xfs-20180713+

This will typically be a symlink to the linux-next-xfs directory if the
kernel you are building is the latest. Otherwise, it will become a directory
reflecting old results.

# oscheck's secondary objective: track a baseline XFS on different distributions

Different Linux distribution can add support to track the latest Linux and stable
kernels and/or to also track their own kernels if they so wish. oscheck is currently
supported to run on, and a respective baseline can be tracked for the following
distributions:

  * Debian testing
  * OpenSUSE Leap 15.0
  * Fedora 28

# fstest bug triage

  * [xfs bug triage](triage/xfs.md)

## Goals

  * Track latest [fstests ](git://git.kernel.org/pub/scm/fs/xfs/xfstests-dev.git)
  * Keep Linux Distribution agnostic
  * Make it easy to ramp up and use
  * Track fstests issues for all kernels listed as supported on kernel.org
  * Enable addition of different filesystems
  * Enable distributions to track their own fstests issues

## Patches

Please send patches to:

	To: mcgrof@kernel.org

## Requirements

You'll need:

  * A supported distribution
  * clone the latest [fstests ](git://git.kernel.org/pub/scm/fs/xfs/xfstests-dev.git),
    you can then use oscheck.sh --install-deps to install fstests's dependencies.
  * A test system
  * Use existing spare disk or create a qcow2 image for testing
  * To be able to parse xunit results file: pip install junitparser

## Install

As root run:

	make install

Review the deployed config and become comfortable with the different supported
sections:

	/var/lib/xfstests/configs/$(hostname).config

To check the dependencies required to compile and install xfstests:

	/var/lib/xfstests/oscheck.sh --check-deps

If you want to try to get oscheck to install the dependencies for you, you
can run the following, your distribution must have support for this on
the respective helpers.sh, for instance opensuse-leap has osfiles/opensuse-leap/helpers.sh.

	/var/lib/xfstests/oscheck.sh --install-deps

After this go compile and install xfstests.

# Run

Once fstests has been installed you can run:

	cd /var/lib/xfstests/
	./gendisks.sh -d
	time ./oscheck.sh | tee log

## Setup

You'll need a guest with plenty of disk space, currently gendisks.sh requires
240 GiB of space for a loopback setup, however in practice this turns out to
currently be about 60 GiB of real disk space required.

## Usage

Provided you've updated what you need to as per above, for example say you are
going run a baseline test with XFS, just as ssh into the guest, and you should
be able to do a full baseline test as follows. No failures are expected to
appear:

	cd /var/lib/xfstests/
	./gendisks.sh -d
	mkfs.xfs -f /dev/loop16
	time ./oscheck.sh | tee log

### Setting up scrach dev - using truncated files - using gendisks.sh

The easiest and most convenient way to test fstests against a filesystem is
to use the base qcow2 images and use the truncated / loopback file setup.
The scratch devices are set up using one truncated file per test parition.
With this approach, after the truncated files are created one uses losetup
to setup a loopback device for each truncated file. When using loopback
devices one may end up testing up to three different filesystems though,
if using a qcow2 image:

  * The filesystem on the host/hypervisor where the qcow image resides, say /opt/qemu/guest.img
  * The guest filesystem where you create the truncated files (say /media/truncated/)
  * The actual filesystem you test with fstests

Using truncated files with loopback devices therefore may create more
issues than typically observed than just using a real bare metal system
with only the target filesystem you want to test. So we may see more
issues, not less than using bare metal. However, since its convenient, and
since tests run fast, we recommend using this setup.

If using truncated files with loopback devices you want to reduce the number of
different filesystem used though. Control over the hypervisor/host and where the
guest image resides is up to the administrator of the guest. As for the guest,
we recommend you create a separate large partition which the filesystem
developer can then use to create create target truncated files. Then, at least as
far as the guest is concerned only one filesystem is used. To aid with this you
can set the environment variable $OSCHECK_TRUNCATE_PATH with the path to where
truncated files will reside. By default $OSCHECK_TRUNCATE_PATH is set to
/media/truncated.

The script gendisks.sh on this repository can be used to easily set up
loopback devices with truncated files and uses the $OSCHECK_TRUNCATE_PATH
directory path for them.

Ensure you take note what filesystem OSCHECK_TRUNCATE_PATH is on.

	./gendisks.sh -d

You should end up with something like:

	# losetup -a
	/dev/loop5: [0803]:1676932 (/media/truncated/disk-sdc5)
	/dev/loop6: [0803]:1679306 (/media/truncated/disk-sdc6)
	/dev/loop7: [0803]:1679307 (/media/truncated/disk-sdc7)
	/dev/loop8: [0803]:1679308 (/media/truncated/disk-sdc8)
	/dev/loop9: [0803]:1679309 (/media/truncated/disk-sdc9)
	/dev/loop10: [0803]:1679310 (/media/truncated/disk-sdc10)
	/dev/loop11: [0803]:1679311 (/media/truncated/disk-sdc11)
	/dev/loop12: [0803]:1679312 (/media/truncated/disk-sdc12)
	/dev/loop13: [0803]:1679313 (/media/truncated/disk-sdc13)
	/dev/loop14: [0803]:1679314 (/media/truncated/disk-sdc14)
	/dev/loop15: [0803]:1679315 (/media/truncated/disk-sdc15)
	/dev/loop16: [0803]:1679316 (/media/truncated/disk-sdc16)

Ensure that the directory matches what you set up for $OSCHECK_TRUNCATE_PATH.

## Expunge files

We need a way to express to skip tests to work with a baseline. fstests tends
to refer to this as "expunging" tests. fstests supports the ability to specify
an expunge list as a file, and multiple expunge lists can be used.
Comments on expunge files are always ignored. The expected format of the
file is one entry per line, comments after the line are ignored.

We support grooming through this tree's possible expunge files by OS release
and section. You may also optionally triage the failures per priority per
directory. There is a special file "all.txt" which we look for on each
filesystem to allow failures to apply to all sections. This way for instance on
XFS you may want to annotate that a test is failing on section "xfs" and also
on "xfs_reflink", and all other sections on example.config.

Example files with failures due to differenes against the expected golden output
and we're unsure if this is a real issue:

	expunges/opensuse-leap/15.0/unassigned/diff/all.txt
	expunges/opensuse-leap/15.0/unassigned/
	expunges/opensuse-leap/15.0/xfs/diff/xfs.txt
	expunges/opensuse-leap/15.0/xfs/diff/xfs_reflink.txt
	... etc

 Untriaged:

	expunges/opensuse-leap/15.0/xfs/unassigned/all.txt
	expunges/opensuse-leap/15.0/xfs/unassigned/xfs.txt
	expunges/opensuse-leap/15.0/xfs/unassigned/xfs_reflink.txt
	... etc

 Triaged:

	expunges/opensuse-leap/15.0/xfs/unassigned/P1/xfs.txt
	expunges/opensuse-leap/15.0/xfs/unassigned/P1/xfs_nocrc_512.txt
	... etc

 Untriaged:

	expunges/opensuse-leap/15.0/xfs/assigned/all.txt"
	expunges/opensuse-leap/15.0/xfs/assigned/xfs.txt"
	expunges/opensuse-leap/15.0/xfs/assigned/xfs_nocrc_512.txt
	... etc

 Triaged:

	expunges/opensuse-leap/15.0/xfs/assigned/P1/all.txt
	expunges/opensuse-leap/15.0/xfs/assigned/P1/xfs.txt
	expunges/opensuse-leap/15.0/xfs/assigned/P1/xfs_nocrc_512.txt
	expunges/opensuse-leap/15.0/xfs/assigned/P2/all.txt
	expunges/opensuse-leap/15.0/xfs/assigned/P3/xfs_nocrc_512.txt
	expunges/opensuse-leap/15.0/xfs/assigned/xfs.txt
	... etc

## Testing expunge lists

You can test the expunge lists by using a dry run:

	./oscheck.sh -n

This in turn will pass -n to fstests's check which does the same thing.
When -n is used, we don't do any requirements check. If you want to emulate
a different OS you can use the environment variables $OSCHECK_OS_FILE with
a path to an os-release file specific to a target system. This can be used
to test what the expunge list looks like when doing a dry run.

To see the actual files being picked for the expunge list for a release
you can use:

	./oscheck.sh --show-cmd -n

Be sure to set OSCHECK_OS_FILE if you want to emulate an OS file from another
distribution from which you are currently running this on. The path to the
file must be absolute. We carry list of os-release files from different
distributions which you can set OSCHECK_OS_FILE to to test and see what an
expunge files would be used if one runs oscheck.sh on that distribution.

To see the list of possible expunge files for a release use:

	./oscheck.sh --expunge-list -n

To check to see what expunge files would actually be used for opensuse Leap 15.0:

	export OSCHECK_OS_FILE=/home/oscheck/osfiles/opensuse-leap/15.0/os-release
	./oscheck.sh --show-cmd -n

## Parallelizing fstests runs - multiple guests and one test per section

fstests runs serially, since one can run a full set of tests with one section, and since
there are different sections one can tests a filesyste against, one could parallelize
tests by running oscheck against only one specific section per guest. For example,
to run oscheck only against the section xfs_reflink_1024:

	./oscheck --test-section xfs_reflink_1024 | tee log

## Running tests quickly - FAST_TEST

Although ./check supports using the group quick (with -g quick), the quick
group is rather abused and the semantics of how long a tests can run is not
clear. Additionally a thorough filesystem test would run a test against all
known custom sections which are supported.

To help with this we've itemized all tests which are known to take long,
specifically 10 seconds or more on a 4-core qemu system, 4 GiB of RAM on
SSDs, and we can skip all these and all custom sections if you set the
environment variable:

	export FAST_TEST=y

## Adding support for a new distribution

Adding support for a new distribution consists of writing a respective helpers.sh
file. For instance osfiles/distro/helpers.sh. Your distribution may either use
/etc/os-release files or it may rely on lsb_release output information. For the
former you can use the debian helpers.sh file as a templete, otherwise you can
use the opensuse-leap helpers.sh file as a template. If your distribution has
a /etc/os-release file, supply it as a copy under:

	osfiles/your-distro/release/os-release

Once you have a helper file in place for your distsribution test this to ensure
that it can detect if you are running a distro kernel or not:

	./oscheck --is-distro

Likewise test to ensure these work as expected as well:

	./oscheck --check-deps
	./oscheck --install-deps

You will then need to create a baseline. For now you will have to create
expunge files for different failures yourself. Once you have the helpers.sh
file and the expunges files ready, submit them upstream into oscheck.

## qemu kernel configs

For now we supply kernel configs used to build the vanilla / stable kernels tested.
These purposely trimmed to be minimal for use on qemu KVM guests to run a full
fstests. They are under:

	qemu-kernel-configs/

License
-------

This work is licensed under the GPLv2, refer to the [LICENSE](./LICENSE) file
for details. Please stick to SPDX annotations for file license annotations.
If a file has no SPDX annotation the GPLv2 applies. We keep SPDX annotations
with permissive licenses to ensure upstream projects we embraced under
permissive licenses can benefit from our changes to their respective files.
