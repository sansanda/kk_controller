import pyvisa


class VisaResourceManager:
    """
    Wrapper mínimo del ResourceManager de PyVISA.
    backend: "@ni", "@keysight", "@py" (pyvisa-py), "@sim" (pyvisa-sim)
    """

    def __init__(self, backend: str = "@ni", timeout_ms: int = 5000):
        self.rm = pyvisa.ResourceManager()
        self.timeout_ms = timeout_ms

    def list_resources(self) -> tuple[str, ...]:
        return self.rm.list_resources()

    def open(self, address: str):
        res = self.rm.open_resource(address)
        res.timeout = self.timeout_ms
        return res

    def close(self) -> None:
        try:
            self.rm.close()
        except Exception:
            pass
