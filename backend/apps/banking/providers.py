"""Contrato de lectura para fuentes bancarias y una implementación sintética local."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal


@dataclass(frozen=True)
class ProviderMovement:
    external_id: str
    date: date
    amount: Decimal
    description: str


class FinancialDataProvider(ABC):
    @abstractmethod
    def snapshot(self, connection_id: int, cutoff: date) -> tuple[Decimal, list[ProviderMovement]]:
        """Devuelve saldo al corte y movimientos completos hasta ese día."""


class MockBankProvider(FinancialDataProvider):
    """Fuente determinista sin red ni credenciales; uso exclusivo de pruebas locales."""

    def snapshot(self, connection_id: int, cutoff: date) -> tuple[Decimal, list[ProviderMovement]]:
        start = cutoff - timedelta(days=119)
        movements = []
        for offset in range(120):
            day = start + timedelta(days=offset)
            amount = Decimal("80000.00") if offset % 7 in (0, 2, 4) else Decimal("-25000.00")
            movements.append(
                ProviderMovement(
                    external_id=f"mock:{connection_id}:{day.isoformat()}",
                    date=day,
                    amount=amount,
                    description="Venta simulada" if amount > 0 else "Proveedor simulado",
                )
            )
        return Decimal("5000000.00"), movements


PROVIDERS = {"mock": MockBankProvider()}
