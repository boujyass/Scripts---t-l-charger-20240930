from oscpy.server import OSCThreadServer
from controller import Controller

class OSCServer:
    def __init__(self, controller, host='0.0.0.0', port=8000):
        self.osc = OSCThreadServer(default_handler=self.dump)
        self.sock = self.osc.listen(address=host, port=port, default=True)
        self.controller = controller

    def bind_callbacks(self):
        self.osc.bind(b'/multisense/pad/x', self.controller.callback_x)
        self.osc.bind(b'/multisense/pad/y', self.controller.callback_y)
        self.osc.bind(b'/multisense/pad/touchUP', self.controller.callback_touchUP)

    def dump(self, address, *values):
        """Default handler for unbound OSC messages."""
        print(u'{}: {}'.format(
            address.decode('utf8'),
            ', '.join(
                '{}'.format(
                    v.decode('utf8') if isinstance(v, bytes) else v
                )
                for v in values if values
            )
        ))

    def stop(self):
        self.osc.stop()
