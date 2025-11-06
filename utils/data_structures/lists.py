class LimitedList(list):
    def __init__(self, max_length: int, *args):
        super().__init__(*args)
        self.max_length = max_length

    def append(self, item):
        """Añade un elemento y elimina el más antiguo si se supera el tamaño máximo."""
        super().append(item)  # llama al append original
        if len(self) > self.max_length:
            self.pop(0)  # elimina el primer elemento