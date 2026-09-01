"""Car Intake Agent - orchestrates vehicle intake.

Responsibilities:
 1. Receive files.
 2. Classify files (RC / photos / documents / excel).
 3. Identify the RC.
 4. Identify vehicle photographs.
 5. Identify other documents.
 6. Extract user-provided information.
 7. Create temporary vehicle record.
 8. Send info to specialist agents.
 9. Detect missing information.
10. Detect conflicts.
11. Request human confirmation when required.

It never invents missing information.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from km_car_deals.agents.rc_document_agent import RCDocumentAgent
from km_car_deals.agents.vision_agent import VehicleVisionAgent
from km_car_deals.core.logging import get_logger
from km_car_deals.image_processing.processor import available_backgrounds
from km_car_deals.models.customer import Customer, CustomerVehicleInterest
from km_car_deals.models.enums import DocumentType, SourceType, VehicleStatus
from km_car_deals.models.vehicle import (
    Vehicle,
    VehicleDocument,
    VehicleFact,
    VehiclePhoto,
)
from km_car_deals.schemas.vehicle import VehicleFactIn
from km_car_deals.services import inventory
from km_car_deals.services.crm import get_or_create_customer
from km_car_deals.utils import paths

logger = get_logger(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
DOC_EXTS = {".pdf", ".txt"}
EXCEL_EXTS = {".xlsx", ".xlsm", ".xls"}


class IntakeInput:
    """Bundle of files + free-text message for a single intake submission."""

    def __init__(
        self,
        files: List[Tuple[bytes, str]] | None = None,
        message: str = "",
        seller_whatsapp: Optional[str] = None,
    ):
        self.files = files or []
        self.message = message or ""
        self.seller_whatsapp = seller_whatsapp


class CarIntakeAgent:
    def __init__(self, db: Session):
        self.db = db

    # ---- file classification ----
    def classify_file(self, filename: str) -> str:
        """Return one of: 'rc', 'photo', 'document', 'excel', 'unknown'."""
        ext = Path(filename).suffix.lower()
        low = filename.lower()
        if ext in EXCEL_EXTS:
            return "excel"
        if ext in IMAGE_EXTS:
            if "rc" in low or "registration" in low:
                return "rc"
            return "photo"
        if ext == ".pdf":
            if "rc" in low or "registration" in low:
                return "rc"
            return "document"
        return "unknown"

    # ---- user message parsing (never invented; only parsed what's present) ----
    def parse_user_message(self, message: str) -> Dict[str, Any]:
        """Extract structured fields from the free-text user message.

        Only populates fields explicitly present in the message text. It never
        guesses. Brand/model/variant are resolved only against a known-brand
        vocabulary so we never invent a car that wasn't named.
        """
        info: Dict[str, Any] = {}
        if not message:
            return info

        # Brand / model / variant from a known-brand vocabulary.
        parsed_name = self._parse_vehicle_name(message)
        info.update(parsed_name)

        # Fuel type (explicit mentions only)
        low = message.lower()
        if "diesel" in low:
            info["fuel_type"] = "DIESEL"
        elif "petrol" in low:
            info["fuel_type"] = "PETROL"
        elif "cng" in low:
            info["fuel_type"] = "CNG"
        elif "electric" in low or "ev " in low:
            info["fuel_type"] = "ELECTRIC"

        # Transmission (explicit mentions only)
        if "automatic" in low or "at " in low or "amt" in low:
            info["transmission"] = "AUTOMATIC" if "automatic" in low else "AMT"
        elif "manual" in low or "mt" in low:
            info["transmission"] = "MANUAL"

        # Color (explicit mention of a common color)
        for color in ("white", "silver", "black", "grey", "gray", "red", "blue", "brown", "beige", "gold"):
            if color in low:
                info["vehicle_color"] = color.title()
                break

        # Year
        m = re.search(r"\b(19|20)\d{2}\b", message)
        if m:
            info["manufacturing_year"] = int(m.group(0))

        # KM / mileage
        m = re.search(r"(\d{1,3}(?:,\d{3})*)\s*km", message, re.IGNORECASE)
        if m:
            info["mileage_km"] = int(m.group(1).replace(",", ""))

        # Price (₹ / INR)
        m = re.search(
            r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s*(?:lakh|lacs?)\b",
            message,
            re.IGNORECASE,
        )
        if m:
            if m.group(1):
                amt = Decimal(m.group(1).replace(",", ""))
            else:
                amt = Decimal(m.group(2).replace(",", "")) * 100000
            info["selling_price"] = amt

        # Owner count
        m = re.search(r"(\d+)\s*(?:owner|owners)", message, re.IGNORECASE)
        if m:
            info["owner_count"] = int(m.group(1))

        # Single owner phrase
        if re.search(r"single owner", message, re.IGNORECASE):
            info["owner_count"] = 1

        return info

    def _parse_vehicle_name(self, text: str) -> Dict[str, str]:
        """Return {manufacturer, vehicle_model, vehicle_variant} if detectable.

        Uses a fixed vocabulary of common manufacturers and models so the agent
        only attaches a value that the user explicitly typed. Returns {} if no
        brand match is found (no guess).
        """
        from km_car_deals.ai.vehicles import MODEL_REGISTRY

        info: Dict[str, str] = {}
        low = text.lower()
        found_brand = None
        found_model = None
        found_variant = None
        for brand, models in MODEL_REGISTRY.items():
            if brand not in low:
                continue
            # Brand present; find a known model of this brand in the text.
            found_brand = brand.title()
            best = []
            for model in models:
                if model in low:
                    best.append(model)
            if best:
                # Pick the longest matching model (most specific) if multiple.
                found_model = max(best, key=len)
        if not found_brand:
            return info
        info["manufacturer"] = found_brand
        if found_model:
            info["vehicle_model"] = found_model.replace("_", " ").title()
            # Variant: the token immediately following the model, if it looks
            # like a trim/variant word (uppercase letters, e.g. SX, SX(O), GLE).
            self._extract_variant(text, found_model, info)
        return info

    def _extract_variant(self, text: str, model: str, info: Dict[str, str]) -> None:
        idx = text.lower().find(model)
        if idx < 0:
            return
        tail = text[idx + len(model):]
        m = re.match(r"\s+([A-Z][A-Z0-9/().]*)\b", tail)
        if m:
            # Avoid capturing stray words like "Diesel", "2022" as a variant.
            token = m.group(1)
            if not token.lower() in ("diesel", "petrol", "automatic", "manual", "cng"):
                info["vehicle_variant"] = token.title()

    # ---- main intake ----
    def run_intake(
        self,
        files: List[Tuple[bytes, str]],
        message: str = "",
        seller_whatsapp: Optional[str] = None,
        referral: Optional[str] = None,
        intake_source: Optional[str] = None,
    ) -> Tuple[Vehicle, List[str]]:
        """Persist files, coordinate specialist agents, return (vehicle, notices)."""
        notices: List[str] = []

        # persist files to disk
        stored = []
        classifications: Dict[str, List] = {"photo": [], "rc": [], "document": [], "excel": [], "unknown": []}
        for data, name in files:
            path = paths.store_upload(data, name, subdir="intake")
            cls = self.classify_file(name)
            classifications[cls].append((path, name))
            stored.append((path, name))
            logger.info("Intake file %s classified as %s", name, cls)

        # user-provided structured info
        user_info = self.parse_user_message(message)

        # Create the vehicle record (temp)
        vehicle = inventory.create_vehicle(
            self.db, self._vehicle_create_from(user_info), created_by="car_intake_agent"
        )
        inventory.update_status(
            self.db, vehicle.vehicle_id, VehicleStatus.PROCESSING.value,
            reason="Intake started", actor="car_intake_agent"
        )

        # Attach documents
        for path, name in classifications["rc"]:
            doc = VehicleDocument(
                vehicle_id=vehicle.vehicle_id,
                doc_type=DocumentType.RC.value,
                file_path=str(path),
                original_file_name=name,
                mime_type=name.rsplit(".", 1)[-1].lower() if "." in name else "unknown",
            )
            self.db.add(doc)
            self.db.flush()
            vehicle.documents.append(doc)
            rc_agent = RCDocumentAgent(self.db)
            rc_facts = rc_agent.process_document(vehicle.vehicle_id, str(path), doc)
            for fact in rc_facts:
                inventory.set_fact(self.db, vehicle.vehicle_id, fact)
            self.db.flush()

        for path, name in classifications["document"]:
            doc = VehicleDocument(
                vehicle_id=vehicle.vehicle_id,
                doc_type=self._document_type(name),
                file_path=str(path),
                original_file_name=name,
            )
            self.db.add(doc)
            vehicle.documents.append(doc)

        # Attach photos and run vision
        photos = []
        for path, name in classifications["photo"]:
            photo = VehiclePhoto(
                vehicle_id=vehicle.vehicle_id,
                variant="original",
                file_path=str(path),
                original_file_name=name,
            )
            self.db.add(photo)
            self.db.flush()
            photos.append(photo)
            vehicle.photos.append(photo)

        for photo in photos:
            VehicleVisionAgent(self.db).analyze_photo(photo)

        # Detect duplicates among photos
        VehicleVisionAgent(self.db).detect_duplicates(photos)

        # Set first photo as primary
        if photos:
            photos[0].is_primary = True

        # Merge user-provided facts (highest priority commercial/visual)
        self._apply_user_facts(vehicle, user_info)

        # Detect conflicts between RC facts and user facts
        self._detect_conflicts(vehicle)

        # Sync confirmed facts to queryable columns
        inventory.sync_vehicle_from_facts(self.db, vehicle.vehicle_id)

        # Detect missing info
        self._detect_missing(vehicle, notices)

        # Associate a seller customer if provided
        if seller_whatsapp:
            cust, _ = get_or_create_customer(
                self.db, whatsapp=seller_whatsapp, source="VEHICLE_INTARE_SELLER"
            )
            self.db.add(
                CustomerVehicleInterest(
                    customer_id=cust.customer_id,
                    vehicle_id=vehicle.vehicle_id,
                    interest_type="VIEWED",
                    interest_status="ACTIVE",
                    notes="Seller of this vehicle",
                )
            )

        # Check for duplicate vehicle by registration number
        duplicate_notice = self._check_duplicate(vehicle, notices)

        # Build confidence summary across all extracted facts
        self._build_confidence_summary(vehicle)

        # Generate description (deterministic fallback if AI disabled)
        if not vehicle.description:
            try:
                vehicle.description = inventory.generate_description(vehicle)
            except Exception as exc:
                logger.warning("Description generation failed: %s", exc)

        # Determine next workflow status
        has_open_conflicts = bool(inventory.open_conflicts(self.db, vehicle.vehicle_id))
        has_review_fields = any(f.needs_review for f in vehicle.facts)
        if has_open_conflicts or has_review_fields:
            next_status = VehicleStatus.NEEDS_REVIEW.value
        elif classifications["rc"]:
            next_status = VehicleStatus.EXTRACTED.value
        else:
            next_status = VehicleStatus.AI_DRAFT.value
        inventory.update_status(
            self.db, vehicle.vehicle_id, next_status,
            reason="Intake pipeline complete", actor="car_intake_agent"
        )

        # Audit log
        from km_car_deals.services.audit import log_action
        log_action(
            self.db, actor="car_intake_agent", action="INTAKE_COMPLETE",
            entity_type="Vehicle", entity_id=vehicle.vehicle_id,
            after_data={
                "status": next_status,
                "facts": len(vehicle.facts),
                "photos": len(vehicle.photos),
                "conflicts": len(vehicle.conflicts),
                "notices": notices,
            },
        )

        self.db.flush()
        return vehicle, notices

    # ---- helpers ----

    def _check_duplicate(self, vehicle: Vehicle, notices: List[str]) -> Optional[Vehicle]:
        """Check for a duplicate vehicle by registration number."""
        reg = vehicle.registration_number
        if not reg:
            # Try facts
            for f in vehicle.facts:
                if f.field == "registration_number" and f.value:
                    reg = f.value
                    break
        if reg:
            dup = inventory.find_duplicate_by_registration(self.db, reg)
            if dup and dup.vehicle_id != vehicle.vehicle_id:
                notices.append(
                    f"⚠ Possible duplicate: registration {reg} already exists "
                    f"as stock {dup.stock_id} (status: {dup.status})."
                )
                return dup
        return None

    def _build_confidence_summary(self, vehicle: Vehicle) -> None:
        """Compute per-field confidence and store on vehicle.ai_confidence_summary."""
        summary: Dict[str, Any] = {}
        for fact in vehicle.facts:
            summary[fact.field] = {
                "value": fact.value,
                "confidence": fact.confidence,
                "source": fact.source,
                "needs_review": fact.needs_review,
            }
        vehicle.ai_confidence_summary = summary

    def _vehicle_create_from(self, info: Dict[str, Any]):
        from km_car_deals.schemas.vehicle import VehicleCreate

        return VehicleCreate(
            manufacturer=info.get("manufacturer"),
            model=info.get("vehicle_model") or info.get("model"),
            fuel_type=info.get("fuel_type"),
            vehicle_color=info.get("vehicle_color"),
            owner_count=info.get("owner_count"),
            mileage_km=info.get("mileage_km"),
            manufacturing_year=info.get("manufacturing_year"),
            selling_price=info.get("selling_price"),
        )

    def _document_type(self, name: str) -> str:
        low = name.lower()
        if "insur" in low:
            return DocumentType.INSURANCE.value
        if "puc" in low or "pollution" in low:
            return DocumentType.PUC.value
        if "servic" in low:
            return DocumentType.SERVICE.value
        if "invoic" in low:
            return DocumentType.INVOICE.value
        return DocumentType.OTHER.value

    def _apply_user_facts(self, vehicle: Vehicle, info: Dict[str, Any]) -> None:
        """Commercial & visual fields: user > database > excel."""
        mapping = {
            "mileage_km": "mileage_km",
            "selling_price": "selling_price",
            "owner_count": "owner_count",
            "manufacturing_year": "manufacturing_year",
            "fuel_type": "fuel_type",
            "vehicle_color": "vehicle_color",
        }
        for user_key, field in mapping.items():
            if user_key in info and info[user_key] is not None:
                inventory.set_fact(
                    self.db,
                    vehicle.vehicle_id,
                    VehicleFactIn(
                        field=field,
                        value=str(info[user_key]),
                        source=SourceType.USER.value,
                        confidence=1.0,
                        needs_review=False,
                    ),
                )

    def _detect_conflicts(self, vehicle: Vehicle) -> None:
        """Compare RC facts with user facts; create VehicleConflict records."""
        rc_facts = {
            f.field: f.value
            for f in vehicle.facts
            if f.source == SourceType.RC.value and f.value is not None
        }
        user_facts = {
            f.field: f.value
            for f in vehicle.facts
            if f.source == SourceType.USER.value and f.value is not None
        }
        for field in set(rc_facts) & set(user_facts):
            if rc_facts[field] != user_facts[field]:
                inventory.create_conflict(
                    self.db,
                    vehicle.vehicle_id,
                    field=field,
                    source_a=SourceType.RC.value,
                    value_a=rc_facts[field],
                    source_b=SourceType.USER.value,
                    value_b=user_facts[field],
                    message=(
                        f"Vehicle information conflict detected.\n"
                        f"RC {field}: {rc_facts[field]}\n"
                        f"User-provided {field}: {user_facts[field]}\n"
                        f"Please confirm the correct value."
                    ),
                )

    def _detect_missing(self, vehicle: Vehicle, notices: List[str]) -> None:
        required = [
            ("manufacturer", "Manufacturer"),
            ("vehicle_model", "Model"),
            ("manufacturing_year", "Year"),
        ]
        present_fields = {f.field for f in vehicle.facts}
        for field, label in required:
            if field not in present_fields and not getattr(vehicle, self._attribute(field), None):
                notices.append(f"Missing: {label} - awaiting confirmation.")

    def _attribute(self, field: str) -> str:
        mapping = {"vehicle_model": "model"}
        return mapping.get(field, field)
