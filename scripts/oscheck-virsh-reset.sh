#!/bin/bash

for i in $(virsh list | awk '{print $2'}| grep oscheck); do
	virsh reset $i
done
