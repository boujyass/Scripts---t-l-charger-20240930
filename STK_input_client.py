#!/usr/bin/env python3
#Michael ORTEGA - 09 jan 2018

###############################################################################
## Global libs
import socket
import sys
import select
from time import sleep

address = ('localhost', 6006)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send_command(command):
    client_socket.sendto(command, address)
    print(f"Sent command: {command}")
    
    
sleep(3)
data = b'P_LEFT'
send_command(data)
sleep(3)
data = b'R_LEFT'
send_command(data)
sleep(3)
data = b'BLAH BLAH BLAH'
send_command(data)
