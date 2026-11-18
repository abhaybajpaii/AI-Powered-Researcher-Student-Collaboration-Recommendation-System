"""Institutional Faculty CSV Importer.

Allows university administrators to upload verified faculty rosters via CSV, ensuring
genuine academic faculty profiles are distinguished from unverified external scholarly authors.
"""

import csv
import io
from typing import Any, Dict, List, Tuple
from backend.app.ingestion.schemas import FacultyIngestDTO


class InstitutionalCsvImporter:
    """Parses and validates verified university faculty rosters from CSV."""

    REQUIRED_HEADERS = {"first_name", "last_name", "email", "department"}

    @classmethod
    def parse_faculty_csv(
        cls,
        csv_text: str,
    ) -> Tuple[List[FacultyIngestDTO], List[Dict[str, Any]]]:
        """Parses CSV text into valid FacultyIngestDTOs with VERIFIED status.

        Returns (valid_dtos, error_list).
        """
        f = io.StringIO(csv_text.strip())
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            return [], [{"row": 0, "error": "CSV file is empty or headers are missing."}]

        fieldnames_normalized = {h.strip().lower(): h for h in reader.fieldnames}
        missing_required = cls.REQUIRED_HEADERS - set(fieldnames_normalized.keys())
        if missing_required:
            return [], [
                {
                    "row": 0,
                    "error": f"Missing required CSV column headers: {', '.join(sorted(missing_required))}. "
                    f"Required: {', '.join(sorted(cls.REQUIRED_HEADERS))}",
                }
            ]

        valid_records: List[FacultyIngestDTO] = []
        errors: List[Dict[str, Any]] = []

        for row_idx, row in enumerate(reader, start=2):
            try:
                # Clean and extract fields
                def get_val(key: str, default: Any = None) -> Any:
                    actual_key = fieldnames_normalized.get(key)
                    if actual_key and row.get(actual_key):
                        return row[actual_key].strip()
                    return default

                first_name = get_val("first_name")
                last_name = get_val("last_name")
                email = get_val("email")
                department = get_val("department")

                if not all([first_name, last_name, email, department]):
                    errors.append({
                        "row": row_idx,
                        "error": "Required fields (first_name, last_name, email, department) cannot be empty.",
                    })
                    continue

                max_capacity = 5
                try:
                    if get_val("max_capacity"):
                        max_capacity = int(get_val("max_capacity"))
                except ValueError:
                    max_capacity = 5

                accepting_students = True
                accepting_raw = get_val("accepting_students")
                if accepting_raw and accepting_raw.lower() in ("false", "0", "no"):
                    accepting_students = False

                dto = FacultyIngestDTO(
                    first_name=first_name,
                    last_name=last_name,
                    email=email.lower(),
                    department=department,
                    title_rank=get_val("title_rank", "ASSISTANT_PROFESSOR"),
                    office_location=get_val("office_location"),
                    website_url=get_val("website_url"),
                    lab_name=get_val("lab_name"),
                    bio=get_val("bio"),
                    max_capacity=max_capacity,
                    accepting_students=accepting_students,
                    is_synthetic=False,
                    verification_status="VERIFIED",
                    openalex_id=get_val("openalex_id"),
                    institution_name=get_val("institution_name", "University Faculty Roster"),
                    verification_notes="Imported via official verified institutional CSV roster.",
                )
                valid_records.append(dto)

            except Exception as exc:
                errors.append({"row": row_idx, "error": str(exc)})

        return valid_records, errors


csv_importer = InstitutionalCsvImporter()
