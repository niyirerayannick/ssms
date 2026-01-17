import json
import os
import urllib.request

from django.core.management import BaseCommand, call_command
from django.db import transaction

from core.models import Province, District, Sector, Cell, Village


DEFAULT_SOURCE_URL = (
    "https://raw.githubusercontent.com/jnkindi/rwanda-locations-json/master/locations.json"
)


def normalize_code(code_value):
    if code_value is None:
        return None
    code_str = str(code_value).strip()
    if not code_str:
        return None
    if len(code_str) > 10:
        return code_str[:10]
    return code_str


class Command(BaseCommand):
    help = "Sync Rwanda locations from official dataset and export fixture."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-url",
            default=DEFAULT_SOURCE_URL,
            help="Raw JSON URL from jnkindi/rwanda-locations-json.",
        )
        parser.add_argument(
            "--replace",
            dest="replace",
            action="store_true",
            default=True,
            help="Delete existing location records before import (default).",
        )
        parser.add_argument(
            "--keep-existing",
            dest="replace",
            action="store_false",
            help="Keep existing records and only add missing ones.",
        )
        parser.add_argument(
            "--output",
            default=os.path.join("core", "fixtures", "rwanda_locations.json"),
            help="Path to write the updated fixture JSON.",
        )
        parser.add_argument(
            "--no-export",
            action="store_true",
            help="Skip exporting the fixture after import.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of records for testing (0 = all).",
        )

    def handle(self, *args, **options):
        source_url = options["source_url"]
        output_path = options["output"]
        no_export = options["no_export"]
        limit = options["limit"]
        replace = options["replace"]

        self.stdout.write(f"Downloading dataset from {source_url} ...")
        with urllib.request.urlopen(source_url) as response:
            raw_data = response.read()

        records = json.loads(raw_data.decode("utf-8"))
        if isinstance(records, dict):
            records = records.get("data") or records.get("locations") or []

        if not isinstance(records, list):
            raise ValueError("Unexpected dataset format. Expected a list of records.")

        if limit and limit > 0:
            records = records[:limit]

        if replace:
            self.stdout.write("Removing existing location records...")
            Village.objects.all().delete()
            Cell.objects.all().delete()
            Sector.objects.all().delete()
            District.objects.all().delete()
            Province.objects.all().delete()

        provinces_by_name = {p.name: p for p in Province.objects.all()}
        districts_by_key = {(d.name, d.province_id): d for d in District.objects.all()}
        sectors_by_key = {(s.name, s.district_id): s for s in Sector.objects.all()}
        cells_by_key = {(c.name, c.sector_id): c for c in Cell.objects.all()}
        villages_by_key = {(v.name, v.cell_id): v for v in Village.objects.all()}

        created_counts = {
            "province": 0,
            "district": 0,
            "sector": 0,
            "cell": 0,
            "village": 0,
        }

        with transaction.atomic():
            for index, record in enumerate(records, start=1):
                province_name = record.get("province_name")
                district_name = record.get("district_name")
                sector_name = record.get("sector_name")
                cell_name = record.get("cell_name")
                village_name = record.get("village_name")

                if not all([province_name, district_name, sector_name, cell_name, village_name]):
                    continue

                province_code = normalize_code(record.get("province_code"))
                district_code = normalize_code(record.get("district_code"))
                sector_code = normalize_code(record.get("sector_code"))
                cell_code = normalize_code(record.get("cell_code"))
                village_code = normalize_code(record.get("village_code"))

                province = provinces_by_name.get(province_name)
                if province is None:
                    province = Province.objects.create(
                        name=province_name,
                        code=province_code,
                    )
                    provinces_by_name[province_name] = province
                    created_counts["province"] += 1
                elif not province.code and province_code:
                    province.code = province_code
                    province.save(update_fields=["code"])

                district_key = (district_name, province.id)
                district = districts_by_key.get(district_key)
                if district is None:
                    district = District.objects.create(
                        name=district_name,
                        province=province,
                        code=district_code,
                    )
                    districts_by_key[district_key] = district
                    created_counts["district"] += 1
                elif not district.code and district_code:
                    district.code = district_code
                    district.save(update_fields=["code"])

                sector_key = (sector_name, district.id)
                sector = sectors_by_key.get(sector_key)
                if sector is None:
                    sector = Sector.objects.create(
                        name=sector_name,
                        district=district,
                        code=sector_code,
                    )
                    sectors_by_key[sector_key] = sector
                    created_counts["sector"] += 1
                elif not sector.code and sector_code:
                    sector.code = sector_code
                    sector.save(update_fields=["code"])

                cell_key = (cell_name, sector.id)
                cell = cells_by_key.get(cell_key)
                if cell is None:
                    cell = Cell.objects.create(
                        name=cell_name,
                        sector=sector,
                        code=cell_code,
                    )
                    cells_by_key[cell_key] = cell
                    created_counts["cell"] += 1
                elif not cell.code and cell_code:
                    cell.code = cell_code
                    cell.save(update_fields=["code"])

                village_key = (village_name, cell.id)
                village = villages_by_key.get(village_key)
                if village is None:
                    village = Village.objects.create(
                        name=village_name,
                        cell=cell,
                        code=village_code,
                    )
                    villages_by_key[village_key] = village
                    created_counts["village"] += 1
                elif not village.code and village_code:
                    village.code = village_code
                    village.save(update_fields=["code"])

                if index % 5000 == 0:
                    self.stdout.write(f"Processed {index} records...")

        self.stdout.write(
            "Created: "
            f"provinces={created_counts['province']}, "
            f"districts={created_counts['district']}, "
            f"sectors={created_counts['sector']}, "
            f"cells={created_counts['cell']}, "
            f"villages={created_counts['village']}"
        )

        if no_export:
            return

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.stdout.write(f"Exporting fixture to {output_path} ...")
        with open(output_path, "w", encoding="utf-8") as output_file:
            call_command(
                "dumpdata",
                "core.Province",
                "core.District",
                "core.Sector",
                "core.Cell",
                "core.Village",
                indent=2,
                stdout=output_file,
            )
        self.stdout.write("Done.")
