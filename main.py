# This is a sample Python script.

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


from devices import (
    VisaResourceManager,
    Keithley2400,
    KeysightE4990A,
)
from config import GPIB_ADDRESS_SOURCEMETER, GPIB_ADDRESS_IMPEDANCE_ANALYZER


def main():
    # Configura tu backend VISA y direcciones GPIB:
    BACKEND = "@ni"   # "@ni", "@keysight", "@py", "@sim"

    visa = VisaResourceManager(backend=BACKEND, timeout_ms=5000)
    print("Recursos VISA:", visa.list_resources())

    # --- SourceMeter ---
    smu_res = visa.open(GPIB_ADDRESS_SOURCEMETER)
    smu = Keithley2400(smu_res)
    print("SMU:", smu.idn())
    smu.set_nplc(1);
    smu.set_terminals("FRONT")
    smu.set_source_mode('CURR')
    smu.set_measure_mode('VOLT')
    smu.set_compliance(0.1)
    #smu.reset()

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

    visa.close()

if __name__ == "__main__":
    main()
