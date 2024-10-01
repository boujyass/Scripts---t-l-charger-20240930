from oscpy.server import OSCThreadServer
from time import sleep, time
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
                v.decode('utf8') if isinstance(v, bytes) else v
            )
            for v in values if values
        )
    ))

# Adjusted thresholds
STEER_THRES = 0.3  # Lower threshold for steering
ACCEL_THRES = 0.3  # Lower threshold for acceleration
SHAKE_THRESHOLD = 1.2  # Adjusted threshold for shake detection
DOUBLE_TAP_TIME = 0.3  # Adjusted time interval for double-tap detection

current_steering = STEER.NEUTRAL
current_accel = ACCEL.NEUTRAL

last_tap_time = 0
tap_count = 0
address = ('localhost', 6006)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def callback_x(*values):
    acceleration = ACCEL.NEUTRAL
    if values[0] < -ACCEL_THRES:
        acceleration = ACCEL.DOWN  # Move backward
    elif values[0] > ACCEL_THRES:
        acceleration = ACCEL.UP  # Move forward

    process_acceleration(acceleration)

def callback_y(*values):
    steering = STEER.NEUTRAL
    if values[0] < -STEER_THRES:
        steering = STEER.LEFT  # Steer left
    elif values[0] > STEER_THRES:
        steering = STEER.RIGHT  # Steer right

    process_steering(steering)

def callback_touchUP(*values):
    global last_tap_time, tap_count
    current_time = time()
    
    if current_time - last_tap_time <= DOUBLE_TAP_TIME:
        tap_count += 1
        if tap_count == 2:  # Double-tap detected
            send_command(b'DOUBLE_TAP')
            tap_count = 0  # Reset tap count after double tap
    else:
        tap_count = 1  # Reset tap count on a new tap

    last_tap_time = current_time

    # Send command based on current state
    send_control_commands()

def callback_shake(*values):
    acceleration = (values[0]**2 + values[1]**2 + values[2]**2)**0.5
    if acceleration > SHAKE_THRESHOLD:
        send_command(b'SHAKE')

# Pitch will control acceleration
def callback_pitch(*values):
    acceleration = ACCEL.NEUTRAL
    if values[0] > ACCEL_THRES:
        acceleration = ACCEL.UP  # Move forward
    elif values[0] < -ACCEL_THRES:
        acceleration = ACCEL.DOWN  # Move backward

    process_acceleration(acceleration)

# Yaw will control steering
def callback_yaw(*values):
    steering = STEER.NEUTRAL
    if values[0] > STEER_THRES:
        steering = STEER.RIGHT  # Steer right
    elif values[0] < -STEER_THRES:
        steering = STEER.LEFT  # Steer left

    process_steering(steering)

# Roll will control the acceleration
def callback_roll(*values):
    angle = values[0]
    acceleration = ACCEL.NEUTRAL

    if angle < -STEER_THRES:
        acceleration = ACCEL.DOWN  # Move backward
    elif angle > STEER_THRES:
        acceleration = ACCEL.UP  # Move forward

    process_acceleration(acceleration)

# Send command based on current acceleration and steering
def send_control_commands():
    data = b''
    if current_accel != ACCEL.NEUTRAL:
        data += b'R_UP' if current_accel == ACCEL.UP else b'R_DOWN'
    if current_steering != STEER.NEUTRAL:
        data += b'R_LEFT' if current_steering == STEER.LEFT else b'R_RIGHT'

    if len(data) > 0:
        client_socket.sendto(data, address)

def send_command(command):
    client_socket.sendto(command, address)

def process_acceleration(acceleration):
    global current_accel
    if acceleration != current_accel:
        send_control_commands()  # Send new acceleration command
    current_accel = acceleration

def process_steering(steering):
    global current_steering
    if steering != current_steering:
        send_control_commands()  # Send new steering command
    current_steering = steering

# OSC server setup
osc = OSCThreadServer(default_handler=dump)
sock = osc.listen(address='0.0.0.0', port=8000, default=True)

# Bind the OSC addresses to the appropriate callbacks
osc.bind(b'/multisense/pad/x', callback_x)
osc.bind(b'/multisense/pad/y', callback_y)
osc.bind(b'/multisense/pad/touchUP', callback_touchUP)
osc.bind(b'/multisense/orientation/pitch', callback_pitch)
osc.bind(b'/multisense/orientation/yaw', callback_yaw)
osc.bind(b'/multisense/orientation/roll', callback_roll)
osc.bind(b'/multisense/orientation/shake', callback_shake)  # Bind shake detection

sleep(1000)
osc.stop()
