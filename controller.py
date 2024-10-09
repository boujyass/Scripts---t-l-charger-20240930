import socket
from steering_acceleration import STEER, ACCEL

STEER_THRES = 0.4
ACCEL_THRES = 0.4

class Controller:

    def __init__(self, address):
        self.current_steering = STEER.NEUTRAL
        self.current_accel = ACCEL.NEUTRAL
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = address


    def send_data(self, data):
        if len(data) > 0:
            self.client_socket.sendto(data, self.address)


    def callback_x(self, *values):
        data = b''
        acceleration = ACCEL.NEUTRAL

        if values[0] < -STEER_THRES:
            acceleration = ACCEL.DOWN
        elif values[0] > STEER_THRES:
            acceleration = ACCEL.UP

        if self.current_accel != ACCEL.NEUTRAL and acceleration == ACCEL.NEUTRAL:
            if self.current_accel == ACCEL.UP:
                data = b'R_UP'
            elif self.current_accel == ACCEL.DOWN:
                data = b'R_DOWN'

        if self.current_accel == ACCEL.NEUTRAL and acceleration != ACCEL.NEUTRAL:
            if acceleration == ACCEL.UP:
                data = b'P_UP'
            elif acceleration == ACCEL.DOWN:
                data = b'P_DOWN'

        self.send_data(data)
        self.current_accel = acceleration



    def callback_y(self, *values):
        data = b''
        steering = STEER.NEUTRAL

        if values[0] < -ACCEL_THRES:
            steering = STEER.LEFT
        elif values[0] > ACCEL_THRES:
            steering = STEER.RIGHT

        if self.current_steering != STEER.NEUTRAL and steering == STEER.NEUTRAL:
            if self.current_steering == STEER.LEFT:
                data = b'R_LEFT'
            elif self.current_steering == STEER.RIGHT:
                data = b'R_RIGHT'

        if self.current_steering == STEER.NEUTRAL and steering != STEER.NEUTRAL:
            if steering == STEER.LEFT:
                data = b'P_LEFT'
            elif steering == STEER.RIGHT:
                data = b'P_RIGHT'

        self.send_data(data)
        self.current_steering = steering



    def callback_touchUP(self, *values):
        data = b''

        if self.current_accel != ACCEL.NEUTRAL:
            if self.current_accel == ACCEL.UP:
                data = b'R_UP'
            elif self.current_accel == ACCEL.DOWN:
                data = b'R_DOWN'
        
        if self.current_steering != STEER.NEUTRAL:
            if self.current_steering == STEER.LEFT:
                data = b'R_LEFT'
            elif self.current_steering == STEER.RIGHT:
                data = b'R_RIGHT'

        self.send_data(data)


