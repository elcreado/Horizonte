import re
import unicodedata

from django.db import migrations


def normalized(value):
    text = "".join(
        char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)
    )
    return " ".join(re.findall(r"\w+", text.upper()))[:250]


def backfill(apps, schema_editor):
    Merchant = apps.get_model("banking", "Merchant")
    MerchantAlias = apps.get_model("banking", "MerchantAlias")
    Transaction = apps.get_model("banking", "Transaction")
    aliases = {}
    pending = []
    rows = (
        Transaction.objects.exclude(merchant_name="")
        .filter(merchant__isnull=True)
        .select_related("account", "account__connection")
        .iterator(chunk_size=500)
    )
    for row in rows:
        company_id = row.account.company_id
        provider = row.account.connection.provider if row.account.connection_id else "manual_upload"
        key = normalized(row.merchant_name)
        if not key:
            continue
        alias_key = (company_id, provider, key)
        merchant_id = aliases.get(alias_key)
        if merchant_id is None:
            merchant, _ = Merchant.objects.get_or_create(
                company_id=company_id,
                normalized_name=key,
                defaults={"display_name": key},
            )
            alias, _ = MerchantAlias.objects.get_or_create(
                company_id=company_id,
                provider=provider,
                normalized_name=key,
                defaults={"merchant_id": merchant.pk},
            )
            merchant_id = alias.merchant_id
            aliases[alias_key] = merchant_id
        row.merchant_id = merchant_id
        pending.append(row)
        if len(pending) >= 500:
            Transaction.objects.bulk_update(pending, ["merchant"], batch_size=500)
            pending.clear()
    if pending:
        Transaction.objects.bulk_update(pending, ["merchant"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("banking", "0009_merchant_transaction_merchant_merchantalias_and_more")]

    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
