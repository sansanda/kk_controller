import pyvisa

class GPIBController:
    def __init__(self, backend="@ni", timeout_ms=5000):
        self.rm = pyvisa.ResourceManager(backend)
        self.timeout_ms = timeout_ms

    def list_resources(self):
        return self.rm.list_resources()

    def open(self, address):
        res = self.rm.open_resource(address)
        res.timeout = self.timeout_ms
        return res

    def close(self):
        self.rm.close()
