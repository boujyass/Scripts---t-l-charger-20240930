from oscpy.server import OSCThreadServer
from time import sleep
from enum import Enum
import socket

class STEER(Enum):
    LEFT = 1
    NEUTRAL = 2
    RIGHT = 3

class ACCEL(Enum):
    UP = 1
    NEUTRAL = 2
    DOWN = 3

def dump(address, *values):
    print(u'{}: {}'.format(
        address.decode('utf8'),
        ', '.join(
            '{}'.format(
                v.decode(options.encoding or 'utf8')
                if isinstance(v, bytes)
                else v
            )
            for v in values if values
        )
    ))


STEER_THRES = 0.4
ACCEL_THRES = 0.4

current_steering = STEER.NEUTRAL
current_accel = ACCEL.NEUTRAL


def callback_x(*values):
    global current_accel

    data = b''

    acceleration = ACCEL.NEUTRAL
    if values[0] < -STEER_THRES:
        acceleration = ACCEL.DOWN
    elif values[0] > STEER_THRES:
        acceleration = ACCEL.UP

    if current_accel != ACCEL.NEUTRAL and acceleration == ACCEL.NEUTRAL:
        if current_accel == ACCEL.UP:
            data = b'R_UP'
        elif current_accel == ACCEL.DOWN:
            data = b'R_DOWN'



    if current_accel == ACCEL.NEUTRAL and acceleration != ACCEL.NEUTRAL:
        if acceleration == ACCEL.UP:
            data = b'P_UP'
        elif acceleration == ACCEL.DOWN:
            data = b'P_DOWN'

    if len(data) > 0:
        client_socket.sendto(data, address)

    current_accel = acceleration

def callback_y(*values):
    global current_steering

    data = b''

    steering = STEER.NEUTRAL
    if values[0] < -ACCEL_THRES:
        steering = STEER.LEFT
    elif values[0] > ACCEL_THRES:
        steering = STEER.RIGHT

    if current_steering != STEER.NEUTRAL and steering == STEER.NEUTRAL:
        if current_steering == STEER.LEFT:
            data = b'R_LEFT'
        elif current_steering == STEER.RIGHT:
            data = b'R_RIGHT'

    if current_steering == STEER.NEUTRAL and steering != STEER.NEUTRAL:
        if steering == STEER.LEFT:
            data = b'P_LEFT'
        elif steering == STEER.RIGHT:
            data = b'P_RIGHT'

    if len(data) > 0:
        client_socket.sendto(data, address)

    current_steering = steering

def callback_touchUP(*values):
  
    data = b''
    if current_accel != ACCEL.NEUTRAL:
        if current_accel == ACCEL.UP:
            data = b'R_UP'
        elif current_accel == ACCEL.DOWN:
            data = b'R_DOWN'
    if current_steering != STEER.NEUTRAL:
        if current_steering == STEER.LEFT:
            data = b'R_LEFT'
        elif current_steering == STEER.RIGHT:
            data = b'R_RIGHT'

    if len(data) > 0:
        client_socket.sendto(data, address)



def process_steering(steering):
    global current_steering

    data = b''

    if current_steering != STEER.NEUTRAL and steering == STEER.NEUTRAL:
        if current_steering == STEER.LEFT:
            data = b'R_LEFT'
        elif current_steering == STEER.RIGHT:
            data = b'R_RIGHT'

    if current_steering == STEER.NEUTRAL and steering != STEER.NEUTRAL:
        if steering == STEER.LEFT:
            data = b'P_LEFT'
        elif steering == STEER.RIGHT:
            data = b'P_RIGHT'

    if len(data) > 0:
        client_socket.sendto(data, address)

    current_steering = steering

def process_acceleration(acceleration):
    data = b''

    global current_accel

    if current_accel != ACCEL.NEUTRAL and acceleration == ACCEL.NEUTRAL:
        if current_accel == ACCEL.UP:
            data = b'R_UP'
        elif current_accel == ACCEL.DOWN:
            data = b'R_DOWN'



    if current_accel == ACCEL.NEUTRAL and acceleration != ACCEL.NEUTRAL:
        if acceleration == ACCEL.UP:
            data = b'P_UP'
        elif acceleration == ACCEL.DOWN:
            data = b'P_DOWN'

    if len(data) > 0:
        client_socket.sendto(data, address)

    current_accel = acceleration



if __name__ = "__main__":

    address = ('localhost', 6006)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    osc = OSCThreadServer(default_handler=dump)  # See sources for all the arguments

    # You can also use an \*nix socket path here
    sock = osc.listen(address='0.0.0.0', port=8000, default=True)

    osc.bind(b'/multisense/pad/x', callback_x)
    osc.bind(b'/multisense/pad/y', callback_y)
    osc.bind(b'/multisense/pad/touchUP', callback_touchUP)

    sleep(1000)
    osc.stop()  # Stop the default socket