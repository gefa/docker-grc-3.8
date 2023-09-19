#!/usr/bin/env python3
from subprocess import Popen, PIPE
import signal,time
import socket
from scapy.layers.dot15d4 import *
from scapy.all import *
import struct
import atexit
import os
import sys
import time
from datetime import datetime
import errno
import random
import atexit
import errno
import os
import random
import signal
from distutils.version import StrictVersion
from struct import pack, unpack
from collections import defaultdict
import pyshark
from zigbee import *
from functools import partial
# PCAP Header constants
PCAP_MAGIC = 0xA1B2C3D4
PCAP_MAJOR = 2
PCAP_MINOR = 4
PCAP_ZONE = 0
PCAP_SIG = 0
PCAP_SNAPLEN = 0xFFFF
PCAP_NETWORK = 256
ip = '127.0.0.1'
port = 52001
burst_n = 5
burst_t = 0.02
PROBE = b'\x03\x08\xf2\xff\xff\xff\xff\x07\xcd\xe1' # BEACON_REQ
READ_SIZE = 8192
CHANNEL_DWELL_ACTIVE = 0.1
CHANNEL_DWELL_PASSIVE = 1
FIRST_CHANNEL=11
LAST_CHANNEL=26
NUM_CHANNELS = LAST_CHANNEL - FIRST_CHANNEL + 1
CHANNELS = [x for x in range(FIRST_CHANNEL,LAST_CHANNEL+1,1)]
zig_addresses = {key: {} for key in range(FIRST_CHANNEL, LAST_CHANNEL+1)}
try:
    devices = int(sys.argv[1])
except:
    print("Assuming 12 devices")
    devices = 12
scan_time = 10*60
try:
    channel_time = float(sys.argv[2])
except:
    print("Assuming 1s channel_time")
    channel_time = 1

def open_pcap(filename, mode='overwrite',):
    if mode == 'append' and os.path.exists(filename):
        pcap_fd = open(filename, 'ab')
        return pcap_fd
    pcap_fd = open(filename, 'ab')
    # Write PCAP file header
    pcap_fd.write(
        pack(
            '<LHHLLLL',
            PCAP_MAGIC,
            PCAP_MAJOR,
            PCAP_MINOR,
            PCAP_ZONE,
            PCAP_SIG,
            PCAP_SNAPLEN,
            195,
        )
    )
    return pcap_fd

def write_pcap(fd, channel, access_address, data,):
    now = time.time()
    sec = int(now)
    usec = int((now - sec) * 1000000)
    length = 11
    flags = 0x3C37
    # Write PCAP packet header
    length = int(len(data) + 0)
    fd.write(
        pack(
            '<LLLL',
            sec,
            usec,
            length,
            length,
        )
    )
    fd.write(data)
    fd.flush()

from time import sleep
from contextlib import contextmanager
@contextmanager
def socketcontext(*args, **kwargs):
    s = socket.socket(*args, **kwargs)
    try:
        yield s
    finally:
        s.close()

def sendburst(data, burst=burst_n, timeout=burst_t):
    for _ in range(burst):
        with socketcontext(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(data, (ip, port))
            sleep(timeout)

def recv_timeout(the_socket,chan,timeout=1,extend_if_busy=False):
    the_socket.setblocking(0)
    total_data=[];
    data='';
    begin=time.time()
    while 1:
        if time.time()-begin > timeout:
            break
        try:
            data = the_socket.recv(READ_SIZE)
            if data:
                write_pcap(pcap_zig, chan, 0xc0febabe, data,)
                total_data.append(data)
                if extend_if_busy:
                  begin=time.time()
            else:
                time.sleep(0.1)
        except:
            pass
    return total_data

def insert_colon(addr):
    ret =''
    for elem1,elem2 in zip(addr[ : : 2],addr[1: : 2]) :
        ret += elem1+elem2+":"
    return ret[:-1]
import names
def filter_devices(packets, start_time, data, ch):
    address = set()
    addr_types = set()
    #addrs = []
    layer_addr_types = []  # Initialize layer_addr_types as an empty list
    for pkg_content in data:
        pkt = Dot15d4FCS(pkg_content)
        t = time.time() - start_time
        packet = [t, ch, pkt, [], [], []]
        for layer in pkt.layers():
            layer_name = layer.__name__
            for adr_type in ['source', 'dest_addr', 'src_addr', 'destination', 'ext_src', 'dest_panid']:
                if adr_type in pkt[layer_name].fields:
                    layer_addr_types.append(f'{layer_name}.{adr_type}')
                    adr_val = pkt[layer_name].fields[adr_type]
                    
                    if adr_val is not None:
                        addr = insert_colon(f'{adr_val:0{16}x}')
                        #addrs.append(addr)
                        try:
                            if addr != '00:00:00:00:00:00:00:00' and \
                               addr != '00:00:00:00:00:00:ff:ff':
                                address.add(addr)
                                packet[4].append(addr)
                        except KeyError:
                            pass
    return address, layer_addr_types

if __name__ == '__main__':
    top_block_cls=zigbee
    tb = top_block_cls()
    tb.start()
    socrx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socrx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socrx.settimeout(1)
    server_address = ('127.0.0.1', 52002)
    socrx.bind(server_address)
    BUSY = set()
    idx = 0
    addresses_final = set()
    packets_act = []
    os.system("rm zig_act_scan.pcap")
    pcap_zig = open_pcap("zig_act_scan.pcap",mode='overwrite',)
    t_start_cap = time.time()
    for channel in CHANNELS:
        freq = 1000000 * (2400 + 5 * (channel - 10)) 
        tb.uhd_usrp_source_0.set_center_freq(freq)
        tb.uhd_usrp_sink_0.set_center_freq(freq)
        sendburst(bytes(PROBE), burst=1)
        data = recv_timeout(socrx,channel,timeout=CHANNEL_DWELL_ACTIVE,extend_if_busy=True)
        for packet in data:
            if packet != PROBE and len(packet) >= 3:
                BUSY.add(channel)
        addrs, types = filter_devices(packets_act, t_start_cap, data, ch=channel)
        new_addresses = list(addrs)
        for new_addr in new_addresses:
            if new_addr not in addresses_final:
                addresses_final.add(new_addr)
        idx = idx + 1
        if idx >= len(CHANNELS):
            idx = 0
    print("BUSY channels", BUSY)
    packets_pas = []
    BUSY = list(BUSY)
    idx = 0
    t_end_cap = t_start_cap + scan_time - CHANNEL_DWELL_ACTIVE*NUM_CHANNELS
    try:
        while(time.time() < t_end_cap and len(addresses_final)<devices):
            freq = 1000000 * (2400 + 5 * (BUSY[idx] - 10)) 
            tb.uhd_usrp_source_0.set_center_freq(freq)
            tb.uhd_usrp_sink_0.set_center_freq(freq)
            data = recv_timeout(socrx,BUSY[idx],timeout=CHANNEL_DWELL_PASSIVE,extend_if_busy=False)
            if len(data) >= 3:
                print((data))
            addrs, types = filter_devices(packets_pas, t_start_cap, data, ch=BUSY[idx])
            for new_device in addrs:
                if new_device not in addresses_final:
                    addresses_final.add(new_device)
            print("addresses_final")
            print(addresses_final)
            idx = idx + 1
            if idx >= len(BUSY):
                idx = 0
    except IndexError:
        print("no busy channels")
    tb.stop()
    tb.wait()
    socrx.close()
