import base64
import io
from datetime import datetime

from django.test import SimpleTestCase, TestCase
from openpyxl import Workbook

from apps.banking.models import ImportJob, Transaction
from apps.banking.tasks import import_csv
from apps.banking.xlsx import parse_xlsx
from tests.test_imports import ImportTests


def workbook_bytes(rows, extra_sheet=False):
    book = Workbook()
    book.active.append(["external_id", "date", "amount", "description"])
    for row in rows:
        book.active.append(row)
    if extra_sheet:
        book.create_sheet("Extra")
    output = io.BytesIO()
    book.save(output)
    book.close()
    return output.getvalue()


class XlsxParserTests(SimpleTestCase):
    def test_dates_and_text_ids(self):
        rows = parse_xlsx(workbook_bytes([["0001", datetime(2026, 9, 1), -10.25, "Adobe"]]))
        self.assertEqual(rows[0]["external_id"], "0001")
        self.assertEqual(rows[0]["date"], "2026-09-01")
        self.assertEqual(rows[0]["amount"], "-10.25")

    def test_rejects_unsafe_or_ambiguous_inputs(self):
        for content in (
            b"not a zip",
            workbook_bytes([["id", "2026-09-01", "=1+1", "Venta"]]),
            workbook_bytes([[123, "2026-09-01", 10, "Venta"]]),
            workbook_bytes([], extra_sheet=True),
        ):
            with self.subTest(content=content[:10]), self.assertRaises(ValueError):
                parse_xlsx(content)

    def test_row_limit(self):
        rows = [[str(i), "2026-09-01", 1, "Venta"] for i in range(10000)]
        self.assertEqual(len(parse_xlsx(workbook_bytes(rows))), 10000)
        rows.append(["extra", "2026-09-01", 1, "Venta"])
        with self.assertRaises(ValueError):
            parse_xlsx(workbook_bytes(rows))


class XlsxImportTests(TestCase):
    setUp = ImportTests.setUp
    job = ImportTests.job

    def test_xlsx_then_csv_is_duplicate(self):
        content = workbook_bytes([["csv-1", "2026-09-01", 100.10, "Venta"]])
        job = ImportJob.objects.create(
            account=self.account,
            user=self.user,
            file_format="xlsx",
            content=base64.b64encode(content).decode(),
        )
        import_csv(job.id)
        job.refresh_from_db()
        self.assertEqual(job.status, "completed", job.error)
        second = self.job()
        import_csv(second.id)
        second.refresh_from_db()
        self.assertEqual(second.duplicate_count, 1)
        self.assertEqual(Transaction.objects.count(), 1)
