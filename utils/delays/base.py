from __future__ import annotations

import threading
from abc import ABC, abstractmethod


class Delay(ABC):
    """
    Clase abstracta base para implementar diferentes tipos de delays con métodos de control (start, pause, resume).
    """

    @abstractmethod
    def start(self):
        """Inicia el delay sin bloquear el hilo principal."""

    @abstractmethod
    def pause(self):
        """Pausa el delay sin bloquear el hilo principal."""

    @abstractmethod
    def resume(self):
        """Reanuda el delay sin bloquear el hilo principal."""

    @abstractmethod
    def reset(self):
        """Reinicia el estado del delay."""

    @abstractmethod
    def elapsed(self):
        """
        Tiempo transcurrido desde que se inició el delay
        :return: La cantidad de segundos transcurridos.
        """

    @abstractmethod
    def remaining(self):
        """
        Tiempo que falta para cumplir con el delay
        :return: La cantidad de segundos que faltan `para llegar al intervalo.
        """