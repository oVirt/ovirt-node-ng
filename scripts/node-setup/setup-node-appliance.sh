#!/bin/bash

set -eo pipefail

####### defs #######

NODE_SETUP_PATH=$(dirname $(realpath $0))
MAX_VM_MEM=2048
MAX_VM_CPUS=2
WORKDIR="/var/lib/virtual-machines"
APPLIANCE_DOMAIN="appliance.net"

BOOTISO_URL="http://mirror.centos.org/centos/7/os/x86_64/images/boot.iso"
RELEASE_RPM=

####################


die() { echo "ERROR: $@" && exit 1; }

download_rpm_and_extract() {
    local url=$1
    local name=$2
    local search=$3

    local tmpdir=$(mktemp -d)
    echo "$name: Downloading rpm from $url"
    curl -L -# -o "$tmpdir/$name.rpm" $url || die "Download failed"
    echo "$name: Extracting rpm..."
    rpm2cpio "$tmpdir/$name.rpm" | cpio --quiet -diuD $tmpdir || \
        die "Failed extracting rpm"
    find $tmpdir -name "*.$search" -exec mv -f {} "$WORKDIR/$name.$search" \;
    rm -rf $tmpdir
}

do_ssh() {
    local ssh_key=$1
    local ip=$2
    local cmd=$3

    for i in {1..10}
    do
        ssh -q -o "UserKnownHostsFile /dev/null" -o "StrictHostKeyChecking no" -i $ssh_key root@$ip $cmd && break ||:
        sleep 5
    done
}

get_vm_ip() {
    name=$1

    for i in {1..10}
    do
        ip=$(virsh -q domifaddr $name | awk '{sub(/\/.*/,""); print $4}') ||:
        [[ -n "$ip" ]] && {
            echo $ip
            return
        }
        sleep 5
    done

    die "get_vm_ip failed"
}

run_nodectl_check() {
    local name=$1
    local ssh_key=$2
    local ip=$3
    local timeout=120
    local check=""

    while [[ -z "$check" ]]
    do
        [[ $timeout -eq 0 ]] && break
        check=$(do_ssh $ssh_key $ip "nodectl check" 2>&1)
        sleep 10
        timeout=$((timeout - 10))
    done

    echo "$check" > $name-nodectl-check.log
}

prepare_appliance() {
    local name=$1
    local url=$2

    download_rpm_and_extract "$url" $name "ova"

    local diskimg=$(tar tf $WORKDIR/$name.ova |  grep -Po "images.*(?=.meta)")
    local tmpdir=$(mktemp -d)

    tar xf $WORKDIR/$name.ova -C $tmpdir || die "Failed extracting ova"
    mv $tmpdir/$diskimg $WORKDIR/$name.qcow2
    find $tmpdir -name "*.ovf" -exec mv -f {} "$WORKDIR/$name.ovf" \;
    rm -rf $tmpdir $WORKDIR/$name.ova
}

make_cidata_iso() {
    local ssh_key=$1
    local vmpasswd=$2

    local pub_ssh=$(cat $ssh_key.pub)
    local tmpdir=$(mktemp -d)

    echo "instance-id: rhevm-engine" > $tmpdir/meta-data
    cat << EOF > $tmpdir/user-data
#cloud-config
chpasswd:
  list: |
    root:$vmpasswd
  expire: False
EOF
    genisoimage -quiet -output $WORKDIR/ci.iso -volid cidata \
                        -joliet -rock $tmpdir/* || die "genisoimage failed"

    rm -rf $tmpdir
}

setup_appliance() {
    local name=$1
    local url=$2
    local ssh_key=$3
    local vmpasswd=$4

    # creating $WORKDIR/{$name.qcow2,ci.iso} - XXX: validate.....
    prepare_appliance $name $url
    make_cidata_iso $ssh_key $vmpasswd

    local diskimg="$WORKDIR/$name.qcow2"
    local ovf="$WORKDIR/$name.ovf"
    local cidata="$WORKDIR/ci.iso"
    local logfile="$WORKDIR/virt-install-$name.log"

    local ovf_mem=$(grep -Po "(?<=<rasd:Caption>)[^<]+(?= MB of memory)" $ovf)
    local ovf_cpus=$(grep -Po "(?<=<rasd:Caption>)[^<]+(?= virtual CPU)" $ovf)

    echo "$name: OVF reports $ovf_mem RAM and $ovf_cpus CPUs"

    local v_mem=$(( ovf_mem > MAX_VM_MEM ? MAX_VM_MEM : ovf_mem ))
    local v_cpus=$(( ovf_cpus > MAX_VM_CPUS ? MAX_VM_CPUS : ovf_cpus ))

    echo "$name: Setting up appliance from disk $diskimg"

    virt-customize -q -a $diskimg --ssh-inject root:file:$ssh_key.pub || \
                    die "Failed injecting public ssh key"

    echo "$name: Using $v_mem RAM and $v_cpus CPUs"

    virt-install -q \
        --name $name \
        --ram $v_mem \
        --vcpus $v_cpus \
        --disk path=$diskimg,bus=ide \
        --network network:default,model=virtio  \
        --vnc \
        --noreboot \
        --boot hd \
        --cdrom $cidata \
        --os-type linux \
        --noautoconsole > $logfile || die "virt-install failed"

    local ip=$(get_vm_ip $name)
    local fqdn=$name.$APPLIANCE_DOMAIN

    echo "$name: Setting up repos and hostname ($fqdn)"

    do_ssh $ssh_key $ip "hostnamectl set-hostname $fqdn; echo \"$ip $fqdn $name\" >> /etc/hosts"
    [[ -n "$RELEASE_RPM" ]] && do_ssh $ssh_key $ip "rpm -U --quiet $RELEASE_RPM"
    do_ssh $ssh_key $ip "systemctl -q enable sshd; systemctl -q mask --now cloud-init"

    do_ssh $ssh_key $ip "echo SSO_ALTERNATE_ENGINE_FQDNS=\"$ip\" > /etc/ovirt-engine/engine.conf.d/99-alt-fqdn.conf"
    do_ssh $ssh_key $ip "sed -i 's/^PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config"
    do_ssh $ssh_key $ip "systemctl restart sshd"

    echo "$name: appliance is available at $ip"

    rm $cidata
}

setup_node_iso() {
    local name=$1
    local node_iso_path=$2
    local ssh_key=$3
    local vmpasswd=$4

    local ksfile="$WORKDIR/node-iso-install.ks"
    local logfile="$WORKDIR/node-iso-virt-install-$name.log"
    local ssh=$(cat $ssh_key.pub)

    local tmpdir=$(mktemp -d)
    mount -o ro $node_iso_path $tmpdir
    cat << EOF > $ksfile
timezone --utc Etc/UTC
lang en_US.UTF-8
keyboard us
auth --enableshadow --passalgo=sha512
selinux --enforcing
network --bootproto=dhcp --hostname=$name
firstboot --reconfig
sshkey --username=root "$ssh"
rootpw --plaintext $vmpasswd
poweroff
clearpart --all --initlabel --disklabel=gpt
bootloader --timeout=1
EOF
    sed 's/^imgbase/imgbase --debug/' $tmpdir/*ks* >> $ksfile
    umount $tmpdir && rmdir $tmpdir

    echo "$name: Installing iso to vm..."

    virt-install -q \
        --name "$name" \
        --boot menu=off \
        --memory $MAX_VM_MEM \
        --vcpus $MAX_VM_CPUS \
        --cpu host \
        --location "$node_iso_path" \
        --extra-args "inst.ks=file:///node-iso-install.ks console=ttyS0" \
        --initrd-inject "$ksfile" \
        --graphics none \
        --noreboot \
        --check all=off \
        --wait -1 \
        --os-variant rhel7 \
        --disk size=60 > "$logfile" || die "virt-install failed"

    echo -e "$name: Finished installing, starting..."

    virsh -q start $name || die "virsh start failed"
    local ip=$(get_vm_ip $name)

    # waiting for ssh to be up...
    do_ssh $ssh_key $ip "ls" > /dev/null
    run_nodectl_check $name $ssh_key $ip

    echo "$name: node is available at $ip"

    rm $ksfile
}

setup_node() {
    local name=$1
    local url=$2
    local ssh_key=$3
    local vmpasswd=$4

    download_rpm_and_extract "$url" "$name" "squashfs.img"

    local bootiso="$WORKDIR/boot.iso"
    local squashfs="$WORKDIR/$name.squashfs.img"
    local diskimg="$WORKDIR/$name.qcow2"
    local ksfile="$WORKDIR/node-install.ks"
    local logfile="$WORKDIR/virt-install-$name.log"
    local kickstart_in="$NODE_SETUP_PATH/node-install.ks.in"
    local ssh=$(cat $ssh_key.pub)

    sed -e "s#@HOSTNAME@#$name#" \
        -e "s#@SSHKEY@#$ssh#" \
        -e "s#@VMPASSWD@#$vmpasswd#" \
        $kickstart_in > $ksfile

    [[ ! -e "$bootiso" ]] && {
        echo "$name: Downloading $BOOTISO_URL..."
        curl -# -o $bootiso $BOOTISO_URL || die "Failed downloading boot.iso"
    } || {
        echo "$name: Using $bootiso"
    }

    qemu-img create -q -f qcow2 $diskimg 60G || die "Failed creating disk"

    echo "$name: Installing $squashfs to $diskimg..."
    echo "$name: Install log file is $logfile"

    virt-install -q \
        --name "$name" \
        --boot menu=off \
        --memory $MAX_VM_MEM \
        --vcpus $MAX_VM_CPUS \
        --cpu host \
        --location $bootiso \
        --extra-args "inst.ks=file:///node-install.ks console=ttyS0" \
        --initrd-inject $ksfile \
        --check disk_size=off,path_in_use=off \
        --graphics none \
        --noreboot \
        --wait -1 \
        --os-variant rhel7 \
        --disk path=$diskimg,bus=virtio,cache=unsafe,discard=unmap,format=qcow2 \
        --disk path=$squashfs,readonly=on,device=disk,bus=virtio,serial=livesrc \
        > $logfile || die "virt-install failed"

    echo "$name: Finished installing, bringing it up..."

    virsh -q start $name || die "virsh start failed"
    local ip=$(get_vm_ip $name)

    # waiting for ssh to be up...
    do_ssh $ssh_key $ip "ls" > /dev/null
    run_nodectl_check $name $ssh_key $ip

    echo "$name: node is available at $ip"

    rm $ksfile $squashfs
}

main() {
    local node_url=""
    local appliance_url=""
    local node_iso_path=""
    local vmpasswd=""

    while getopts "n:a:i:p:m:" OPTION
    do
        case $OPTION in
            n)
                node_url=$OPTARG
                ;;
            a)
                appliance_url=$OPTARG
                ;;
            i)
                node_iso_path=$OPTARG
                ;;
            p)
                vmpasswd=$OPTARG
                ;;
            m)
                machine=$OPTARG
                ;;
        esac
    done


    [[ -z "$node_url" && -z "$appliance_url" && -z "$node_iso_path" ]] && {
        echo "Usage: $0 -n <node_rpm_url> -a <appliance_rpm_url> -i <node_iso>"
        exit 1
    }

    [[ $EUID -ne 0 ]] && {
        echo "Must run as root"
        exit 1
    }

    [[ -z "$vmpasswd" ]] && {
        while [[ -z "$vmpasswd" ]]
        do
            echo -n "Set VM password: "
            read -s vmpasswd
            echo ""
        done

        echo -n "Reenter password: "
        read -s vmpasswd2
        echo ""

        [[ "$vmpasswd" != "$vmpasswd2" ]] && {
            echo "Passwords do not match"
            exit 1
        }
    }

    [[ ! -d "$WORKDIR" ]] && mkdir -p "$WORKDIR"

    [[ ! -z "$node_url" ]] && {
        node=${machine:-node-$RANDOM}
        ssh_key="$WORKDIR/sshkey-$node"
        ssh-keygen -q -f $ssh_key -N ''
        setup_node "$node" "$node_url" "$ssh_key" "$vmpasswd"
    }

    [[ ! -z "$node_iso_path" ]] && {
        node=${machine:-node-iso-$RANDOM}
        ssh_key="$WORKDIR/sshkey-$node"
        ssh-keygen -q -f $ssh_key -N ''
        setup_node_iso "$node" "$node_iso_path" "$ssh_key" "$vmpasswd"
    }

    [[ ! -z "$appliance_url" ]] && {
        appliance=${machine:-engine-$RANDOM}
        ssh_key="$WORKDIR/sshkey-$appliance"
        ssh-keygen -q -f $ssh_key -N ''
        setup_appliance "$appliance" "$appliance_url" "$ssh_key" "$vmpasswd"
        echo "For smoketesting, remember to run engine-setup on $appliance"
    } || :
}

main "$@"
