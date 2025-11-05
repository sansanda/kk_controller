# This is a sample Python script.
import time
import timeit
# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


from devices import (
    VisaResourceManager,
    Keithley2400,
    KeysightE4990A,
)
from config import GPIB_ADDRESS_SOURCEMETER, GPIB_ADDRESS_IMPEDANCE_ANALYZER
from devices.base import AmmeterBase
from utils.delays.delays import TimeDelay, ThresholdDelay


def main():
    # Configura tu backend VISA y direcciones GPIB:
    BACKEND = "@ni"  # "@ni", "@keysight", "@py", "@sim"

    visa = VisaResourceManager(backend=BACKEND, timeout_ms=5000)
    print("Recursos VISA:", visa.list_resources())

    # --- SourceMeter ---
    smu_res = visa.open(GPIB_ADDRESS_SOURCEMETER)
    smu = Keithley2400(smu_res)
    configure_smu(smu)

    imp_res = visa.open(GPIB_ADDRESS_IMPEDANCE_ANALYZER)
    imp_analyzer = KeysightE4990A(imp_res)
    configure_impedance_analyzer(imp_analyzer)
    time.sleep(1)
    imp_analyzer.trigger_single()
    print(imp_analyzer.fetch())


    # def myfunc():
    #     print('Y ya estamos')
    #     smu.output(False)
    #
    # d = ThresholdCurrentDelay(1E-5, 'below', 0.5, myfunc, smu.measure_current)
    # # d = TimeDelay(2, myfunc)
    # d.start()

    # def get_current(ammeter: AmmeterBase) -> float:
    #     ammeter.configure_ammeter()
    #     ammeter.set_ammeter_range('AUTO')
    #     return ammeter.measure_current()
    #
    # print(get_current(smu))

    # smu.reset()

    # # Ejemplo rápido: fijar 1 mA y leer V
    # smu.output(True)
    # smu.source_current(0.001, compliance_v=10.0)
    # v = smu.measure_voltage()
    # print(f"[SMU] I=1 mA -> V={v:.6f} V")
    # smu.output(False)
    # smu.close()
    #
    # --- Impedance Analyzer ---
    # imp_res = visa.open(GPIB_ADDRESS_IMPEDANCE_ANALYZER)
    # imp = KeysightE4990A(imp_res)
    # print("Impedance Analyzer:", imp.idn())
    # imp.preset()
    # imp.set_freq(1_000)      # 1 kHz
    # imp.set_level_volt(1.0)  # 1 Vrms
    # imp.set_function("CPD")
    # imp.trigger_single()
    # c, d = imp.fetch()
    # print(f"[IMP] C={c:.6e} F, D={d:.6f}")
    # imp.close()

    # visa.close()


def configure_smu(smu):
    print("SMU:", smu.idn())
    smu.reset()
    smu.configure_data_format_elements(['CURR'])
    smu.set_source_mode('V')
    smu.set_source_range(1000)
    smu.set_measure_function('I')
    smu.set_compliance(1E-3)
    smu.set_measure_range('AUTO')
    smu.enable_remote_sense(False)
    smu.set_nplc(0.01)
    smu.set_terminals("FRONT")


def configure_impedance_analyzer(imp_analyzer):
    print("SMU:", imp_analyzer.idn())
    imp_analyzer.preset()
    imp_analyzer.set_freq(1_000)  # 1 kHz
    imp_analyzer.set_level_volt(1.0)  # 1 Vrms
    imp_analyzer.set_function("CPD")


if __name__ == "__main__":
    main()
