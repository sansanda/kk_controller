import pyvisa
import numpy as np

"""
Keysight E4990A frequency sweep (Cs-Rs mode)
Point-by-point triggering, optimized with *OPC?, correct wait-for-trigger state.
"""

# ---------------- COMMUNICATION ----------------
rm = pyvisa.ResourceManager()
devices = rm.list_resources()
print("\nConnected VISA devices:", devices)

inst = rm.open_resource('GPIB0::25::INSTR')
inst.timeout = 30000  # 30 s per query max
print("Instrument ID:", inst.query("*IDN?").strip())

# ---------------- PARAMETERS ----------------
Npts = 500
f_start = 95e3
f_stop = 105e3
Vac = 0.5        # 500 mV AC level
path = 'E:\\Adria\\CV Measurements\\'
name1 = input('\nEnter file name (without extension): ').strip()

# ---------------- CONFIGURATION ----------------
def configure_measurement(f_start, f_stop, Vac, points):
    """Setup point-triggered sweep, Cs/Rs parameters, no DC bias."""
    inst.write("TRIG:SOUR BUS")
    inst.write("INIT1:CONT ON")
    inst.write("CALC1:PAR:COUN 3")
    inst.write("CALC1:PAR1:DEF Z")
    inst.write("CALC1:PAR2:DEF TZ")
    inst.write("CALC1:PAR3:DEF CS")
    inst.write("DISP:WIND1:SPL D1_2_3")

    inst.write("SENS1:SWE:TYPE LIN")
    inst.write(f"SENS1:FREQ:STAR {f_start}")
    inst.write(f"SENS1:FREQ:STOP {f_stop}")
    inst.write(f"SENS1:SWE:POIN {points}")

    inst.write(f"SOUR1:VOLT {Vac}")

    inst.write("SOUR:BIAS:STAT OFF")

    freq_points = np.linspace(f_start, f_stop, points)
    print("\n--- Measurement Configuration ---")
    print(f"Points: {points}")
    print(f"Range: {f_start/1e3:.2f} – {f_stop/1e3:.2f} kHz")
    print(f"AC level: {Vac} V (no DC bias)")
    print("---------------------------------\n")
    return freq_points

def get_results(points):
    """Read Cs and Rs traces, handle interleaved data correctly."""
    inst.write("INIT1:CONT OFF")
    inst.write("ABOR")  # aborts current measurement
    inst.write("INIT1:CONT ON")
    inst.write("TRIG:SING")  # trigger single
    inst.query("*OPC?")

    inst.write("FORM:DATA REAL")
    inst.write("CALC1:PAR1:SEL")
    z_data = inst.query_binary_values("CALC1:DATA:FDAT?", datatype='d', is_big_endian=True)
    z = np.array(z_data[0::2])

    inst.write("CALC1:PAR2:SEL")
    phi_data = inst.query_binary_values("CALC1:DATA:FDAT?", datatype='d', is_big_endian=True)
    phi = np.array(phi_data[0::2])

    inst.write("CALC1:PAR3:SEL")
    cs_data = inst.query_binary_values("CALC1:DATA:FDAT?", datatype='d', is_big_endian=True)
    cs = np.array(cs_data[0::2])

    return z, phi, cs


def save_results_as_csv(filename, path, freqs, z, phi, cs):
    freqs = np.array(freqs).flatten()
    z = np.array(z).flatten()
    phi = np.array(phi).flatten()
    cs = np.array(cs).flatten()

    data = np.column_stack((freqs, z, phi, cs))
    header = "Frequency (Hz),Impedance (Ohm),Phase (Deg),Capacitance (F)"

    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    np.savetxt(path + filename, data, delimiter=",", header=header, comments='')
    print(f"✅ Data saved to: {path + filename}\n")


# ---------------- RUN ----------------
freq_points = configure_measurement(f_start, f_stop, Vac, Npts)
z, phi, cs = get_results(Npts)
save_results_as_csv(name1, path, freq_points, z, phi, cs)

inst.write("DISP:WIND1:TRAC1:Y:AUTO")
inst.write("DISP:WIND1:TRAC2:Y:AUTO")
inst.write("DISP:WIND1:TRAC3:Y:AUTO")


print("Measurement complete ✅")