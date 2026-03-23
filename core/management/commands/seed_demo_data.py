from datetime import date
from typing import Dict, Any

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    Province,
    District,
    Sector,
    Cell,
    Village,
    School,
    AcademicYear,
    Partner,
)
from families.models import Family, FamilyStudent
from students.models import Student, sync_student_enrollment_history


DEMO_DATA = [
    {
        "head_of_family": "Joseph Hakizimana",
        "national_id": "1199880011223345",
        "phone_number": "+250788112233",
        "alternative_phone": "+250732445566",
        "father_name": "Joseph Hakizimana",
        "mother_name": "Beatrice Mukamana",
        "is_orphan": False,
        "guardian_name": "",
        "guardian_phone": "",
        "total_family_members": 5,
        "address_description": "Behind Remera Catholic Church, near the community water point.",
        "notes": "Household participates in the kitchen garden pilot.",
        "location": {
            "province": "Kigali City",
            "district": "Gasabo",
            "sector": "Remera",
            "cell": "Rukiri I",
            "village": "Iga",
        },
        "students": [
            {
                "first_name": "Aline",
                "last_name": "Hakizimana",
                "gender": "F",
                "date_of_birth": date(2010, 3, 15),
                "class_level": "Primary 5",
                "school_level": "primary",
                "enrollment_status": "enrolled",
                "boarding_status": "non_boarding",
                "sponsorship_status": "active",
                "sponsorship_start_year": 2022,
                "sponsorship_reason": "Consistently top of her class and mentors peers.",
                "school": {
                    "name": "Remera Catholic Primary School",
                    "location": {
                        "province": "Kigali City",
                        "district": "Gasabo",
                        "sector": "Remera",
                        "cell": "Rukiri I",
                    },
                },
                "partner": "Hope For Kids",
                "has_disability": False,
                "disability_types": None,
                "disability_description": "",
                "relationship": "Daughter",
            },
            {
                "first_name": "Eric",
                "last_name": "Hakizimana",
                "gender": "M",
                "date_of_birth": date(2012, 8, 2),
                "class_level": "Primary 3",
                "school_level": "primary",
                "enrollment_status": "enrolled",
                "boarding_status": "non_boarding",
                "sponsorship_status": "pending",
                "sponsorship_start_year": 2023,
                "sponsorship_reason": "Needs support for therapy sessions and school meals.",
                "school": {
                    "name": "Remera Catholic Primary School",
                    "location": {
                        "province": "Kigali City",
                        "district": "Gasabo",
                        "sector": "Remera",
                        "cell": "Rukiri I",
                    },
                },
                "partner": "Hope For Kids",
                "has_disability": True,
                "disability_types": "speech",
                "disability_description": "Receives weekly speech therapy at Remera Health Post.",
                "relationship": "Son",
            },
        ],
    },
    {
        "head_of_family": "Anitha Uwimana",
        "national_id": "1199770066554433",
        "phone_number": "+250789334455",
        "alternative_phone": "",
        "father_name": "Jean Damascene Byiringiro",
        "mother_name": "Anitha Uwimana",
        "is_orphan": False,
        "guardian_name": "",
        "guardian_phone": "",
        "total_family_members": 6,
        "address_description": "Near Tumba market opposite the maize mill.",
        "notes": "Family leads the savings group for parents.",
        "location": {
            "province": "Southern Province",
            "district": "Huye",
            "sector": "Tumba",
            "cell": "Kigoma",
            "village": "Nyumba",
        },
        "students": [
            {
                "first_name": "Patrick",
                "last_name": "Byiringiro",
                "gender": "M",
                "date_of_birth": date(2008, 11, 5),
                "class_level": "Senior 3",
                "school_level": "secondary",
                "enrollment_status": "enrolled",
                "boarding_status": "boarding",
                "sponsorship_status": "active",
                "sponsorship_start_year": 2021,
                "sponsorship_reason": "STEM club leader preparing for O-level exams.",
                "school": {
                    "name": "Huye Adventist Secondary School",
                    "location": {
                        "province": "Southern Province",
                        "district": "Huye",
                        "sector": "Tumba",
                    },
                },
                "partner": "Bright Future Cooperative",
                "has_disability": False,
                "disability_types": None,
                "disability_description": "",
                "relationship": "Son",
            },
            {
                "first_name": "Alice",
                "last_name": "Uwera",
                "gender": "F",
                "date_of_birth": date(2016, 4, 21),
                "class_level": "Top Class",
                "school_level": "nursery",
                "enrollment_status": "enrolled",
                "boarding_status": "non_boarding",
                "sponsorship_status": "pending",
                "sponsorship_start_year": 2024,
                "sponsorship_reason": "Recently enrolled in the ECD center and needs meals.",
                "school": {
                    "name": "Kigoma ECD Center",
                    "location": {
                        "province": "Southern Province",
                        "district": "Huye",
                        "sector": "Tumba",
                        "cell": "Kigoma",
                    },
                },
                "partner": "Bright Future Cooperative",
                "has_disability": False,
                "disability_types": None,
                "disability_description": "",
                "relationship": "Daughter",
            },
        ],
    },
    {
        "head_of_family": "Consolee Nyirahabimana",
        "national_id": "1199660099112233",
        "phone_number": "+250781223344",
        "alternative_phone": "+250789887766",
        "father_name": "",
        "mother_name": "",
        "is_orphan": True,
        "guardian_name": "Consolee Nyirahabimana",
        "guardian_phone": "+250781223344",
        "total_family_members": 3,
        "address_description": "Opposite Muhoza taxi park near the cooperative office.",
        "notes": "Grandmother cares for grandchildren after parents passed away.",
        "location": {
            "province": "Northern Province",
            "district": "Musanze",
            "sector": "Muhoza",
            "cell": "Cyabararika",
            "village": "Rugarama",
        },
        "students": [
            {
                "first_name": "Sandrine",
                "last_name": "Ufitimana",
                "gender": "F",
                "date_of_birth": date(2007, 9, 18),
                "class_level": "Senior 5 STEM",
                "school_level": "secondary",
                "enrollment_status": "enrolled",
                "boarding_status": "boarding",
                "sponsorship_status": "active",
                "sponsorship_start_year": 2020,
                "sponsorship_reason": "Excelling in physics and robotics despite mobility challenges.",
                "school": {
                    "name": "Musanze Science School",
                    "location": {
                        "province": "Northern Province",
                        "district": "Musanze",
                        "sector": "Muhoza",
                    },
                },
                "partner": "STEM for Rwanda",
                "has_disability": True,
                "disability_types": "mobility",
                "disability_description": "Uses a wheelchair; dormitory ramp installed through the program.",
                "relationship": "Granddaughter",
            },
            {
                "first_name": "Junior",
                "last_name": "Nshimiyimana",
                "gender": "M",
                "date_of_birth": date(2014, 1, 9),
                "class_level": "Primary 4",
                "school_level": "primary",
                "enrollment_status": "enrolled",
                "boarding_status": "non_boarding",
                "sponsorship_status": "active",
                "sponsorship_start_year": 2022,
                "sponsorship_reason": "Responding well to literacy catch-up sessions.",
                "school": {
                    "name": "Cyabararika Primary School",
                    "location": {
                        "province": "Northern Province",
                        "district": "Musanze",
                        "sector": "Muhoza",
                        "cell": "Cyabararika",
                    },
                },
                "partner": "STEM for Rwanda",
                "has_disability": False,
                "disability_types": None,
                "disability_description": "",
                "relationship": "Grandson",
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed demonstration Families and Students data for local testing."

    def handle(self, *args, **options):
        academic_year, _ = AcademicYear.objects.get_or_create(
            name="2024-2025",
            defaults={"is_active": True},
        )
        if not academic_year.is_active:
            academic_year.is_active = True
            academic_year.save(update_fields=["is_active"])

        families_created = 0
        students_created = 0

        with transaction.atomic():
            for family_payload in DEMO_DATA:
                family, family_created = self.get_or_create_family(family_payload)
                if family_created:
                    families_created += 1

                for student_payload in family_payload["students"]:
                    student, student_created = self.get_or_create_student(
                        student_payload,
                        family_payload,
                        family,
                        academic_year,
                    )
                    if student_created:
                        students_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ensured for {families_created} new families and {students_created} new students."
            )
        )
        self.stdout.write("If location tables are empty, load core/fixtures/rwanda_locations.json before seeding.")

    def get_or_create_family(self, payload: Dict[str, Any]):
        location_objs = self.resolve_location_objects(payload.get("location", {}))
        defaults = {
            "head_of_family": payload["head_of_family"],
            "phone_number": payload["phone_number"],
            "alternative_phone": payload.get("alternative_phone") or "",
            "father_name": payload.get("father_name", ""),
            "mother_name": payload.get("mother_name", ""),
            "is_orphan": payload.get("is_orphan", False),
            "guardian_name": payload.get("guardian_name", ""),
            "guardian_phone": payload.get("guardian_phone", ""),
            "total_family_members": payload.get("total_family_members", 1),
            "address_description": payload.get("address_description"),
            "notes": payload.get("notes", ""),
            **location_objs,
        }
        family, created = Family.objects.get_or_create(
            national_id=payload["national_id"],
            defaults=defaults,
        )
        if not created:
            updated = False
            for field, value in defaults.items():
                if getattr(family, field) != value:
                    setattr(family, field, value)
                    updated = True
            if updated:
                family.save()
        return family, created

    def get_or_create_student(self, student_payload: Dict[str, Any], family_payload: Dict[str, Any], family: Family, academic_year: AcademicYear):
        school = self.get_or_create_school(
            student_payload.get("school", {}),
            family_payload.get("location", {}),
        )
        partner_obj = None
        partner_name = student_payload.get("partner")
        if partner_name:
            partner_obj, _ = Partner.objects.get_or_create(name=partner_name)

        defaults = {
            "family": family,
            "gender": student_payload["gender"],
            "school": school,
            "school_name": school.name,
            "class_level": student_payload["class_level"],
            "school_level": student_payload["school_level"],
            "enrollment_status": student_payload["enrollment_status"],
            "boarding_status": student_payload["boarding_status"],
            "sponsorship_status": student_payload["sponsorship_status"],
            "sponsorship_start_year": student_payload.get("sponsorship_start_year"),
            "sponsorship_reason": student_payload.get("sponsorship_reason", ""),
            "partner": partner_obj,
            "has_disability": student_payload.get("has_disability", False),
            "disability_types": student_payload.get("disability_types"),
            "disability_description": student_payload.get("disability_description", ""),
        }

        student, created = Student.objects.update_or_create(
            first_name=student_payload["first_name"],
            last_name=student_payload["last_name"],
            date_of_birth=student_payload["date_of_birth"],
            defaults=defaults,
        )

        FamilyStudent.objects.update_or_create(
            student=student,
            defaults={
                "family": family,
                "relationship": student_payload.get("relationship", "Child"),
            },
        )

        sync_student_enrollment_history(student, academic_year, overwrite=True)

        return student, created

    def get_or_create_school(self, school_payload: Dict[str, Any], fallback_location: Dict[str, Any]):
        school_name = school_payload.get("name")
        if not school_name:
            school_name = "Community School"
            school_payload = {
                "name": school_name,
                "location": fallback_location,
            }

        location_names = school_payload.get("location") or fallback_location or {}
        location_objs = self.resolve_location_objects(location_names)
        defaults = {
            "province": location_objs.get("province"),
            "district": location_objs.get("district"),
            "sector": location_objs.get("sector"),
        }
        school, created = School.objects.get_or_create(
            name=school_name,
            defaults=defaults,
        )
        if not created:
            updated = False
            for field in ("province", "district", "sector"):
                obj = location_objs.get(field)
                if obj and getattr(school, field) != obj:
                    setattr(school, field, obj)
                    updated = True
            if updated:
                school.save()
        return school

    def resolve_location_objects(self, location_names: Dict[str, Any]):
        province = self.ensure_location_node(Province, location_names.get("province"))
        district = self.ensure_location_node(District, location_names.get("district"), "province", province)
        sector = self.ensure_location_node(Sector, location_names.get("sector"), "district", district)
        cell = self.ensure_location_node(Cell, location_names.get("cell"), "sector", sector)
        village = self.ensure_location_node(Village, location_names.get("village"), "cell", cell)
        return {
            "province": province,
            "district": district,
            "sector": sector,
            "cell": cell,
            "village": village,
        }

    def ensure_location_node(self, model, name: str, parent_field: str = None, parent=None):
        if not name:
            return None

        filters = {"name": name}
        if parent_field and parent:
            filters[parent_field] = parent
        obj = model.objects.filter(**filters).first()
        if obj:
            return obj

        if parent_field and not parent:
            # Unable to create without parent; fall back to name-only lookup.
            return model.objects.filter(name=name).first()

        create_kwargs = {"name": name}
        if parent_field:
            create_kwargs[parent_field] = parent
        return model.objects.create(**create_kwargs)
