from __future__ import annotations
from typing import Dict, Any
from .base import SourcemeterBase, AmmeterBase, Modes, VoltmeterBase


class Keithley2400(SourcemeterBase, AmmeterBase, VoltmeterBase):
    """
    Implementación concreta para el Keithley 2400 (subset SCPI típico).
    Ajusta si tu firmware difiere.
    """

    def output(self, on: bool) -> None:
        self.write(f":OUTP {'ON' if on else 'OFF'}")

    def set_source_mode(self, mode: str) -> str:
        if mode is None:
            raise ValueError("mode no puede ser None")

        m = mode.strip().lower()
        if m in ("current", "curr", "i"):
            self.write(":SOUR:FUNC CURR")
            return "current"
        if m in ("voltage", "volt", "v"):
            self.write(":SOUR:FUNC VOLT")
            return "voltage"

        raise ValueError("mode debe ser 'current'/'curr'/'i' o 'voltage'/'volt'/'v'")

    def get_source_mode(self) -> Modes:
        resp = self.query(":SOUR:FUNC?")
        resp = resp.strip().replace('"', '').upper()
        if resp.startswith("VOLT"):
            return Modes.VOLTAGE_MODE
        if resp.startswith("CURR"):
            return Modes.CURRENT_MODE
        raise RuntimeError(f"Modo de fuente desconocido en :SOUR:FUNC? -> {resp}")

    def set_source_value(self, value: float) -> str:
        mode = self.get_source_mode()
        if mode == Modes.CURRENT_MODE:
            self.write(f":SOUR:CURR {value}")
        elif mode == Modes.VOLTAGE_MODE:
            self.write(f":SOUR:VOLT {value}")
        else:
            raise RuntimeError(f"Modo de fuente no soportado: {mode}")
        return mode

    def set_compliance(self, limit: float) -> str:
        mode = self.get_source_mode()
        if mode == Modes.CURRENT_MODE:
            # En modo corriente, la compliance es de VOLTAJE (V)
            self.write(f":SENS:VOLT:PROT {limit}")
        elif mode == Modes.VOLTAGE_MODE:
            # En modo tensión, la compliance es de CORRIENTE (A)
            self.write(f":SENS:CURR:PROT {limit}")
        else:
            raise RuntimeError(f"Modo de fuente no soportado: {mode}")
        return mode

    def configure_data_format_elements(self, elements: [str]):
        if not elements:
            raise ValueError("La lista de elementos no puede estar vacía.")

        # Opcional: Validar elementos permitidos
        valid_elements = {"READ", "VOLT", "CURR", "RES", "TIME", "STAT"}
        for el in elements:
            if el.upper() not in valid_elements:
                raise ValueError(f"Elemento no válido: {el}. Opciones válidas: {valid_elements}")

        # Construir la cadena SCPI
        formatted = ",".join(f'{el.upper()}' for el in elements)
        command = f":FORM:ELEM {formatted}"
        self.write(command)

    def set_measure_function(self, function: str):
        mode_map = {
            "V": "VOLT",
            "C": "CURR",
            "I": "CURR",
            "R": "RES",
            "VOLT": "VOLT",
            "CURR": "CURR",
            "RES": "RES",
            "VOLTAGE": "VOLT",
            "CURRENT": "CURR",
            "RESISTANCE": "RES"
        }

        mode_upper = function.upper()
        if mode_upper not in mode_map:
            raise ValueError(f"Modo de medición no válido: {function}. Opciones válidas: {list(mode_map.keys())}")

        selected_mode = mode_map[mode_upper]
        self.write(f":SENS:FUNC \"{selected_mode}\"")

    def get_measure_function(self) -> str:
        valid_functions = {"VOLT", "CURR", "RES"}
        response = self.query(":SENS:FUNC?")
        response = response.strip().replace('"', '').upper()
        # Comprobar si alguno de los modos está en la cadena
        if not any(valid_func in response.upper() for valid_func in valid_functions):
            raise RuntimeError(f"Función de medición desconocida o no soportada: {response}")
        return response.split(":")[0]

    def set_nplc(self, nplc: float) -> set[str]:
        funcs = self.get_measure_function()
        applied: set[str] = set()

        # Aplica a cada función reconocida
        if "VOLT" in funcs:
            self.write(f":SENS:VOLT:NPLC {nplc}")
            applied.add("VOLT")
        if "CURR" in funcs:
            self.write(f":SENS:CURR:NPLC {nplc}")
            applied.add("CURR")
        if "RES" in funcs:
            self.write(f":SENS:RES:NPLC {nplc}")
            applied.add("RES")
        if "FRES" in funcs:
            self.write(f":SENS:FRES:NPLC {nplc}")
            applied.add("FRES")

        if not applied:
            # Si no hay función activa reconocible, lo indicamos de forma explícita
            raise RuntimeError(
                f"No hay función de medida activa reconocible para aplicar NPLC (FUNC?={funcs})"
            )

        return applied

    def set_terminals(self, where: str = "FRONT") -> None:
        w = where.strip().lower()
        if w not in ("front", "rear"):
            raise ValueError("where debe ser 'front' o 'rear'")
        # Opcional: garantizar salida off por seguridad
        try:
            self.write(":OUTP OFF")
        except Exception:
            pass
        self.write(f":ROUT:TERM {'FRONT' if w == 'front' else 'REAR'}")

    def set_measure_range(self, value: object):
        measure_function = self.get_measure_function()
        command = ''
        if isinstance(value, str) and value.upper() in {"AUTO", "A"}:
            command = f":SENS:{measure_function}:RANG:AUTO ON"
        elif isinstance(value, (float, int)):
            command = f":SENS:{measure_function}:RANG {value}"
        else:
            raise ValueError("El valor debe ser un número o 'AUTO'/'A'.")
        self.write(command)

    def set_source_range(self, range_or_auto: "AUTO") -> str:
        func = self.get_source_mode()  # 'VOLT' o 'CURR'
        if isinstance(range_or_auto, str) and range_or_auto.strip().lower() == "auto":
            self.write(f":SOUR:{func.value}:RANG:AUTO ON")
            return func

        # Cadenas numéricas también válidas
        if isinstance(range_or_auto, str):
            val = float(range_or_auto.strip())
        else:
            val = float(range_or_auto)

        self.write(f":SOUR:{func.value}:RANG {val}")
        self.write(f":SOUR:{func.value}:RANG:AUTO OFF")
        return func

    def enable_remote_sense(self, enable: bool = True) -> None:
        self.write(f":SYST:RSEN {'ON' if enable else 'OFF'}")

    # ********* AMMETER Y VOLTMETER INTERFACES ****************
    def configure_ammeter(self, settings: Dict[str, Any] = None) -> None:
        # self.set_measure_function('CURR')
        pass

    def _measure(self) -> float:
        response = self.query(":READ?")
        # TODO: mejorar _measure. puede dar problemas cuando el equipo está formateado para medir varios elementos
        if isinstance(response, list):
            response = float(response.split(',')[1])  # Tomamos el segundo valor si se trata de una list,
        return float(response)

    def measure_current(self) -> float:
        return self._measure()

    def set_ammeter_range(self, range_in_amps: Any) -> None:
        self.set_measure_range(range_in_amps)

    def measure_voltage(self) -> float:
        return self._measure()

    def set_voltmeter_range(self, range_in_volts: Any) -> None:
        self.set_measure_range(range_in_volts)

    def configure_voltmeter(self, settings: Dict[str, Any] = None) -> None:
        # self.set_measure_function('VOLT')
        pass
