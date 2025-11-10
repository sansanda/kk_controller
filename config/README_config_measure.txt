# Configuración JSON para la aplicación de medida

Este fichero JSON define la configuración de los instrumentos y la medida que se realizará en la aplicación Python. Se ha organizado para que cada parámetro tenga un valor actual y, cuando procede, un conjunto de valores válidos (valid_options) para validación y parsing.

---

## 1. Instruments

### 1.1 SourceMeter
- `model`: Modelo del SourceMeter (string). Ejemplo: "Keithley_2410".
- `gpib_addr`: Dirección GPIB del instrumento (string).
- `timeout`: Tiempo máximo de espera para la comunicación con el instrumento (milisegundos).

**Parámetros de fuente (source)**
- `source_mode`: Modo de fuente. `"voltage"` o `"current"`.
- `source_mode_valid_options`: Valores válidos para `source_mode`.
- `source_range`: Valor actual del rango de salida según `source_mode`.
- `source_range_valid_options`: Valores válidos de `source_range` según `source_mode`.
- `remote_sense`: Activación de sense remoto (`"y"` o `"n"`).
- `remote_sense_valid_options`: Valores válidos para `remote_sense`.
- `format_elements`: Lista de elementos a medir ["VOLT", "CURR"].
- `format_elements_valid_options`: Valores válidos para `format_elements`.

**Parámetros de medida (measure)**
- `measure_function`: Función de medida actual.
- `measure_function_valid_options`: Valores válidos para `measure_function`:
    - "dc_voltage"
    - "dc_current"
    - "resistance"
    - "four_wire_resistance"
- `measure_range`: Rango de medida actual según `measure_function`.
- `measure_range_valid_options`: Valores válidos para cada `measure_function`.
- `nplc`: Número de ciclos de línea para la medida (float).
- `nplc_valid_options`: Valores válidos típicos [0.01, 0.1, 1, 10, 100].
- `front_rear`: Selección de panel frontal o trasero ("front" o "rear").
- `front_rear_valid_options`: ["front", "rear"].

### 1.2 Impedance_Analyzer
- `model`: Modelo del analizador de impedancia.
- `gpib_addr`: Dirección GPIB.
- `timeout`: Tiempo máximo de espera para la comunicación con el instrumento (milisegundos).
- `frequency`: Frecuencia de medida en Hz (float).
- `mode`: Modo de medida actual ("voltage" o "current").
- `mode_valid_options`: Valores válidos para `mode`.

---

## 2. Sweep

Define el sweep de voltaje y los parámetros de delay y compliance.

- `start_voltage`: Voltaje inicial en V.
- `stop_voltage`: Voltaje final en V.
- `number_of_points`: Número de puntos del sweep (int).
- `compliance`: Corriente máxima permitida en A.
- `compliance_valid_options`: Valores típicos de compliance [0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0].

**Delay**
- `selected_delay`: Tipo de delay a usar ("time" o "statistics").
- `selected_delay_valid_options`: ["time", "statistics"].

**Time delay**
- `time_delay.delay_value`: Retardo en segundos si `selected_delay == "time"`.

**Statistics delay**
- `statistics_delay.metric`: Métrica usada para evaluar la estabilidad ("last_measure", "st_dev", "mean").
- `statistics_delay.metric_valid_options`: ["last_measure", "st_dev", "mean"].
- `statistics_delay.comparator`: Comparador de la métrica ("LESS_THAN", "GREATER_THAN", "EQUAL_TO").
- `statistics_delay.comparator_valid_options`: ["LESS_THAN", "GREATER_THAN", "EQUAL_TO"].
- `statistics_delay.timer_interval`: Intervalo de actualización de la métrica en segundos.
- `statistics_delay.statistic_function`: Función que devuelve los datos de la estadística.
- `statistics_delay.statistic_function_valid_options`: ["measure_sweep_voltage", "measure_sweep_current"].

---

### Notas:
- Los campos `*_valid_options` permiten a la aplicación parsear y validar los valores configurados.
- `source_range` depende de `source_mode`.
- `measure_range` depende de `measure_function`.
- `metric`, `comparator` y `statistic_function` solo se usan si `selected_delay == "statistics"`.
- `timeout` ahora está en **milisegundos** para ambos instrumentos.
