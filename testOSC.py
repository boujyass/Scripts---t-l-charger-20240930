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

def is_double_tap():
    global double_tap_time, last_tap_time
    current_time = time()
    if current_time - last_tap_time < DOUBLE_TAP_THRESHOLD:
        double_tap_time = current_time
        return True
    last_tap_time = current_time
    return False

def throw_object():
    client_socket.sendto(b'FIRE', address)


STEER_THRES = 0.4
ACCEL_THRES = 0.4

current_steering = STEER.NEUTRAL
current_accel = ACCEL.NEUTRAL


def callback_x(*values):
    global current_accel
    print("got values: {}".format(values))
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
    print("got values: {}".format(values))
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
def callback_doubletap(address, *args):
    # Your code to handle the double tap event
    throw_object()  # If throw_object() is the intended action

def callback_touchUP(*values):
    # if is_double_tap():
    #     throw_object()
    print("got values: {}".format(values))
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

def callback_pitch(*values):
    return
STEER_ANGLE_THRES = 20
ACCEL_ANGLE_THRES = 15
ACCEL_ANGLE_OFFSET = -50

def callback_yaw(*values):
    steering = STEER.NEUTRAL

    angle = values[0]

    if angle < - STEER_ANGLE_THRES:
        steering = STEER.RIGHT
    elif angle > STEER_ANGLE_THRES:
        steering = STEER.LEFT

    process_steering(steering)

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
# Roll will control the acceleration
def callback_roll(*values):
    angle = values[0]

    acceleration = ACCEL.NEUTRAL

    if angle < ACCEL_ANGLE_OFFSET - ACCEL_ANGLE_THRES:
        acceleration = ACCEL.DOWN
    elif angle > ACCEL_ANGLE_OFFSET + ACCEL_ANGLE_THRES:
        acceleration = ACCEL.UP

    process_acceleration(acceleration)

address = ('localhost', 6006)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

osc = OSCThreadServer(default_handler=dump)  # See sources for all the arguments

# You can also use an \*nix socket path here
sock = osc.listen(address='0.0.0.0', port=8000, default=True)

osc.bind(b'/multisense/pad/x', callback_x)
osc.bind(b'/multisense/pad/y', callback_y)
osc.bind(b'/multisense/pad/touchUP', callback_touchUP)
osc.bind(b'/multisense/orientation/pitch', callback_pitch)
osc.bind(b'/multisense/orientation/yaw', callback_yaw)
osc.bind(b'/multisense/orientation/roll', callback_roll)
osc.bind(b'/multisense/pad/doubletap', callback_doubletap)

sleep(1000)
osc.stop()  # Stop the default socket