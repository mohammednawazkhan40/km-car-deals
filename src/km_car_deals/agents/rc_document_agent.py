"""RC Document Agent.

Accepts JPG/JPEG/PNG/WEBP/PDF. Extracts registration / vehicle fields with
value/source/confidence/needs_review semantics.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from km_car_deals.ai.provider import ai_provider
from km_car_deals.models.enums import DocumentType, SourceType
from km_car_deals.models.vehicle import VehicleDocument
from km_car_deals.schemas.vehicle import VehicleFactIn

logger = logging.getLogger(__name__)

RC_FIELDS = {
    "registration_number",
    "manufacturer",
    "vehicle_model",
    "vehicle_variant",
    "vehicle_name",
    "manufacturing_month",
    "manufacturing_year",
    "registration_date",
    "fuel_type",
    "vehicle_color",
    "owner_count",
    "owner_name",
    "engine_number",
    "chassis_number",
    "vehicle_class",
    "seating_capacity",
    "insurance_information",
    "fitness_information",
    "puc_information",
}

# keyword -> fact field (Indian RC layout)
KEYWORD_MAP: List[tuple[str, str]] = [
    ("REG.NO", "registration_number"),
    ("Registration No", "registration_number"),
    ("Reg No", "registration_number"),
    ("MAKER/MODEL", "vehicle_model"),
    ("MAKER'S NAME", "manufacturer"),
    ("Makers Name", "manufacturer"),
    ("Model", "vehicle_model"),
    ("Variant", "vehicle_variant"),
    ("Month & Year of Mfg", "manufacturing_month"),
    ("Date of Registration", "registration_date"),
    ("Mfg. Year", "manufacturing_year"),
    ("Fuel", "fuel_type"),
    ("N. V. T", "fuel_type"),
    ("Colour", "vehicle_color"),
    ("Color", "vehicle_color"),
    ("Owner", "owner_name"),
    ("Engine No", "engine_number"),
    ("Chasis No", "chassis_number"),
    ("Chassis No", "chassis_number"),
    ("Class", "vehicle_class"),
    ("Seating Capacity", "seating_capacity"),
]


class RCDocumentAgent:
    """Extracts structured facts from an RC image/PDF."""

    def __init__(self, db: Session):
        self.db = db

    def process_document(
        self, vehicle_id: str, file_path: str, doc: VehicleDocument
    ) -> List[VehicleFactIn]:
        """Return extracted facts from an RC document."""
        text = ai_provider.ocr_text(file_path)
        doc.extracted_text = text
        doc.extraction_engine = ai_provider.name

        facts = self._rule_extract(text)
        ai_facts = ai_provider.extract_rc_fields(text)
        merged = self._merge(text, facts, ai_facts)
        self.db.flush()
        return merged

    def _rule_extract(self, text: str) -> Dict[str, Any]:
        """Deterministic regex/keyword extraction from RC text lines."""
        out: Dict[str, Any] = {}
        lowered = text.lower()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for line in lines:
            for kw, field in KEYWORD_MAP:
                if kw.lower() in line.lower():
                    value = self._after_colon(line)
                    if value and field not in out:
                        out[field] = value
        # registration number pattern: 2 letters + 2 digits + letters + 4 digits
        found = self._regex_find(
            text, r"\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,2}\s?\d{4}\b", "registration_number"
        )
        if found:
            out["registration_number"] = found
        # year reference
        year = self._regex_find(text, r"\b(20\d{2}|19\d{2})\b", "manufacturing_year")
        if year and "manufacturing_year" not in out:
            out["manufacturing_year"] = year
        return out

    def _after_colon(self, line: str) -> Optional[str]:
        for sep in [":", "\t", "-"]:
            if sep in line:
                parts = line.split(sep, 1)
                val = parts[1].strip()
                if val:
                    return val
        return None

    def _regex_find(self, text: str, pattern: str, field: str) -> Optional[str]:
        import re

        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
        return None

    def _merge(
        self, text: str, rule: Dict[str, Any], ai_facts: List[Dict[str, Any]]
    ) -> List[VehicleFactIn]:
        """Merge rule-based and AI facts into a de-duplicated fact list."""
        result: Dict[str, VehicleFactIn] = {}

        # Rule-based facts first (deterministic)
        for field, value in rule.items():
            if field not in RC_FIELDS:
                continue
            result[field] = VehicleFactIn(
                field=field,
                value=value,
                source=SourceType.RC.value,
                confidence=0.9,
                needs_review=False,
            )

        # AI facts (only for fields we didn't confidently get from rules)
        for f in ai_facts:
            field = f.get("field")
            if field not in RC_FIELDS:
                continue
            value = f.get("value")
            conf = float(f.get("confidence", 0.5))
            if field in result and result[field].confidence >= conf:
                continue
            result[field] = VehicleFactIn(
                field=field,
                value=str(value) if value is not None else None,
                source=SourceType.RC.value,
                confidence=conf,
                needs_review=bool(f.get("needs_review", value is None)),
            )
        return list(result.values())
