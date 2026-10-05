"""Resolución de nombres explícitos de comercio por empresa y fuente."""

from collections.abc import Iterable

from apps.classify.services import normalize

from .models import Merchant, MerchantAlias


def resolve_merchants(company_id: int, provider: str, names: Iterable[str]) -> dict[str, int]:
    """Devuelve el comercio de cada etiqueta explícita sin cruzar empresas.

    Los alias existentes prevalecen para permitir futuras consolidaciones manuales.
    Las restricciones únicas resuelven importaciones concurrentes del mismo nombre.
    """
    keys = {name: normalize(name) for name in names if name and normalize(name)}
    if not keys:
        return {}
    normalized = set(keys.values())
    aliases = dict(
        MerchantAlias.objects.filter(
            company_id=company_id, provider=provider, normalized_name__in=normalized
        ).values_list("normalized_name", "merchant_id")
    )
    missing = normalized - aliases.keys()
    if missing:
        Merchant.objects.bulk_create(
            [
                Merchant(company_id=company_id, normalized_name=key, display_name=key)
                for key in missing
            ],
            ignore_conflicts=True,
            batch_size=500,
        )
        merchants = dict(
            Merchant.objects.filter(company_id=company_id, normalized_name__in=missing).values_list(
                "normalized_name", "pk"
            )
        )
        MerchantAlias.objects.bulk_create(
            [
                MerchantAlias(
                    company_id=company_id,
                    merchant_id=merchants[key],
                    provider=provider,
                    normalized_name=key,
                )
                for key in missing
            ],
            ignore_conflicts=True,
            batch_size=500,
        )
        aliases.update(
            MerchantAlias.objects.filter(
                company_id=company_id, provider=provider, normalized_name__in=missing
            ).values_list("normalized_name", "merchant_id")
        )
    return {name: aliases[key] for name, key in keys.items()}
