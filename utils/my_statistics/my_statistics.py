import statistics
from enum import Enum

class Metrics(Enum):
    LAST_VALUE = "last_value"
    MEAN = "mean"
    ST_DEV = "st_dev"

class Comparator(Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUAL_TO = "equal_to"

def compute_metric(values: list, metric: Metrics):
    """Calcula el valor que se usará para comparar con la referencia."""
    if not values:
        return None
    match metric:
        case Metrics.LAST_VALUE:
            return values[-1]
        case Metrics.MEAN:
            return statistics.mean(values)
        case Metrics.ST_DEV:
            return statistics.stdev(values) if len(values) > 1 else 0.0

def check_match(computed_metric:float, comparator:Comparator, reference_value:float) -> bool:
    """
    Comprueba si la condición se cumple y retorna True en ese caso o False en caso contrario.
    :param computed_metric: Valor calculado según la lista de valores y la metrica seleccionada.
    :param comparator: tipo de comparación (ABOVE, UNDER, EQUAL)
    :param reference_value: valor de referencia a comparar
    :returns True si se cumple la condicion. False en caso contario.
    """

    # Comprobar comparación
    trigger = False
    if computed_metric is not None:
        if comparator == Comparator.LESS_THAN and computed_metric < reference_value:
            trigger = True
        elif comparator == Comparator.GREATER_THAN and computed_metric > reference_value:
            trigger = True
        elif comparator == Comparator.EQUAL_TO and computed_metric == reference_value:
            trigger = True
    return trigger