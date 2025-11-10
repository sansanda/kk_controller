def lin_space(f_start, f_stop, points):
    """Genera una lista de valores igualmente espaciados entre f_start y f_stop."""
    if points < 2:
        return [f_start]
    step = (f_stop - f_start) / (points - 1)
    return [f_start + i * step for i in range(points)]