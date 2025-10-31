from __future__ import annotations
from .base import SourcemeterBase


class Keithley2400(SourcemeterBase):
    """
    Implementación concreta para el Keithley 2400 (subset SCPI típico).
    Ajusta si tu firmware difiere.
    """

    def output(self, on: bool) -> None:
        self.write(f":OUTP {'ON' if on else 'OFF'}")

    def set_source_mode(self, mode: str) -> str:
        """
        Configura el modo de fuente (source) del SMU: corriente o tensión.

        Acepta alias:
            - corriente: 'current', 'curr', 'i'
            - tensión:   'voltage', 'volt', 'v'
        """
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

    # set_source_value SIN compliance ---
    def set_source_value(self, value: float) -> str:
        mode = self.get_source_mode()
        if mode == "current":
            self.write(f":SOUR:CURR {value}")
        elif mode == "voltage":
            self.write(f":SOUR:VOLT {value}")
        else:
            raise RuntimeError(f"Modo de fuente no soportado: {mode}")
        return mode

    # set_compliance ---
    def set_compliance(self, limit: float) -> str:
        mode = self.get_source_mode()
        if mode == "current":
            # En modo corriente, la compliance es de VOLTAJE (V)
            self.write(f":SENS:VOLT:PROT {limit}")
        elif mode == "voltage":
            # En modo tensión, la compliance es de CORRIENTE (A)
            self.write(f":SENS:CURR:PROT {limit}")
        else:
            raise RuntimeError(f"Modo de fuente no soportado: {mode}")
        return mode

    def set_source_as_voltage(self, volts: float, compliance_i: float | None = 0.1) -> None:
        self.write(":SOUR:FUNC VOLT")
        self.write(f":SOUR:VOLT {volts}")
        if compliance_i is not None:
            self.write(f":SENS:CURR:PROT {compliance_i}")

    def set_measure_voltage(self) -> float:
        self.write(":FORM:ELEM VOLT")
        return float(self.query(":READ?"))

    def set_measure_current(self) -> float:
        self.write(":FORM:ELEM CURR")
        return float(self.query(":READ?"))

    def _get_measure_mode(self) -> set[str]:
        """
        Lee :SENS:FUNC? y devuelve un set normalizado con las funciones activas:
        {'VOLT', 'CURR', 'RES', 'FRES'} según corresponda.
        """
        resp = self.query(":SENS:FUNC?").strip()
        # Respuestas típicas: "\"VOLT:DC\"" o "\"VOLT:DC\",\"CURR:DC\""
        cleaned = resp.replace('"', '').replace("'", "")
        parts = [p.strip().upper() for p in cleaned.split(",") if p.strip()]
        funcs: set[str] = set()
        for p in parts:
            if p.startswith("VOLT"):
                funcs.add("VOLT")
            elif p.startswith("CURR"):
                funcs.add("CURR")
            elif p == "RES" or p.startswith("RES:"):  # por si algún FW devuelve variantes
                funcs.add("RES")
            elif p == "FRES" or p.startswith("FRES:"):
                funcs.add("FRES")
        return funcs

    # Métodos utilitarios comunes
    def _get_source_mode(self) -> str:
        """
        Devuelve 'VOLT' o 'CURR' leyendo :SOUR:FUNC?.
        Acepta respuestas tipo 'VOLT' o 'VOLT:DC' (según FW).
        """
        resp = self.query(":SOUR:FUNC?").strip().replace('"', '').upper()
        if resp.startswith("VOLT"):
            return "VOLT"
        if resp.startswith("CURR"):
            return "CURR"
        raise RuntimeError(f"Modo de fuente desconocido en :SOUR:FUNC? -> {resp}")

    def set_nplc(self, nplc: float) -> set[str]:
        """
        Ajusta el NPLC leyendo primero la(s) función(es) de medida activas en el instrumento.
        Aplica el mismo NPLC a todas las funciones activas (útil en modo concurrente).
        Devuelve el conjunto de funciones a las que se aplicó NPLC.

        SCPI (serie 2400/2410):
            - :SENS:VOLT:NPLC <n>
            - :SENS:CURR:NPLC <n>
            - :SENS:RES:NPLC  <n>     (ohmios 2 hilos)
            - :SENS:FRES:NPLC <n>     (ohmios 4 hilos)
        """
        funcs = self._get_measure_mode()
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

    # ---------- FRONT/REAR ----------
    def set_terminals(self, where: str = "FRONT") -> None:
        """
        Selecciona terminales FRONT o REAR.
        Recomendado: salida OFF antes de conmutar.
        """
        w = where.strip().lower()
        if w not in ("front", "rear"):
            raise ValueError("where debe ser 'front' o 'rear'")
        # Opcional: garantizar salida off por seguridad
        try:
            self.write(":OUTP OFF")
        except Exception:
            pass
        self.write(f":ROUT:TERM {'FRONT' if w == 'front' else 'REAR'}")

    # ---------- Set Ranges con 'auto' o valor ----------
    def set_measure_range(self, range_or_auto: "AUTO") -> set[str]:
        """
        Ajusta el rango de MEDIDA para cada función activa.
        - Si recibe 'auto'/'AUTO' (case-insensitive): habilita AUTO RANGE.
        - Si recibe numérico: fija un rango concreto y desactiva AUTO.
        Devuelve el set de funciones a las que aplicó el cambio.

        SCPI:
            :SENS:<FUNC>:RANG <val>
            :SENS:<FUNC>:RANG:AUTO ON|OFF
        """
        funcs = self.read_measure_functions()
        if not funcs:
            raise RuntimeError("No hay funciones de medida activas en :SENS:FUNC?")

        # ¿'auto' o valor numérico?
        if isinstance(range_or_auto, str) and range_or_auto.strip().lower() == "auto":
            for f in funcs:
                self.write(f":SENS:{f}:RANG:AUTO ON")
            return funcs

        # Intentar convertir cadenas numéricas
        val: float
        if isinstance(range_or_auto, str):
            val = float(range_or_auto.strip())
        else:
            val = float(range_or_auto)

        for f in funcs:
            self.write(f":SENS:{f}:RANG {val}")
            self.write(f":SENS:{f}:RANG:AUTO OFF")
        return funcs

    def set_source_range(self, range_or_auto: "AUTO") -> str:
        """
        Ajusta el rango de FUENTE para la función activa (VOLT o CURR).
        - 'auto'/'AUTO' -> habilita AUTO RANGE.
        - numérico -> fija rango y desactiva AUTO.
        Devuelve 'VOLT' o 'CURR' según la función de fuente afectada.

        SCPI:
            :SOUR:VOLT:RANG <val> / :SOUR:VOLT:RANG:AUTO ON|OFF
            :SOUR:CURR:RANG <val> / :SOUR:CURR:RANG:AUTO ON|OFF
        """
        func = self.read_source_function()  # 'VOLT' o 'CURR'

        if isinstance(range_or_auto, str) and range_or_auto.strip().lower() == "auto":
            self.write(f":SOUR:{func}:RANG:AUTO ON")
            return func

        # Cadenas numéricas también válidas
        if isinstance(range_or_auto, str):
            val = float(range_or_auto.strip())
        else:
            val = float(range_or_auto)

        self.write(f":SOUR:{func}:RANG {val}")
        self.write(f":SOUR:{func}:RANG:AUTO OFF")
        return func

    # ---------- COMPLIANCE con autodetección de modo ----------
    def set_compliance(self, value: float) -> None:
        """
        Ajusta la COMPLIANCE adecuada al modo de fuente:
          - Si Source V -> límite de corriente (A):  :SENS:CURR:PROT <value>
          - Si Source I -> límite de tensión (V):    :SENS:VOLT:PROT <value>
        """
        mode = self._get_source_mode()
        if mode == "VOLT":
            self.write(f":SENS:CURR:PROT {value}")
        else:  # CURR
            self.write(f":SENS:VOLT:PROT {value}")

    # ---------- 2W / 4W ----------
    def enable_remote_sense(self, enable: bool = True) -> None:
        """
        Activa/desactiva Remote Sense (4 hilos) en el instrumento (afecta V/Ω).
        """
        self.write(f":SYST:RSEN {'ON' if enable else 'OFF'}")
