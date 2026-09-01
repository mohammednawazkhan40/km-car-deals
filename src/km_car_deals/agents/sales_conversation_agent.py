"""Sales Conversation Agent.

Understands customer messages, resolves vehicle references using CRM
customer-vehicle-interest records plus inventory, answers basic questions from
database data, and routes humans for handoff scenarios. Never invents data.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from km_car_deals.ai.provider import ai_provider
from km_car_deals.core.logging import get_logger
from km_car_deals.models.customer import Customer, CustomerVehicleInterest
from km_car_deals.models.enums import (
    ContactChannel,
    FollowupReason,
    HandoffReason,
    InteractionType,
    InterestType,
)
from km_car_deals.models.vehicle import Vehicle
from km_car_deals.services import crm, inventory

logger = get_logger(__name__)


class ConversationResult:
    def __init__(
        self,
        reply: str,
        *,
        handoff: bool = False,
        handoff_reason: Optional[str] = None,
        handoff_summary: Optional[str] = None,
        followup_create: Optional[dict] = None,
        vehicle_interest_id: Optional[str] = None,
        paused: bool = False,
    ):
        self.reply = reply
        self.handoff = handoff
        self.handoff_reason = handoff_reason
        self.handoff_summary = handoff_summary
        self.followup_create = followup_create
        self.vehicle_interest_id = vehicle_interest_id
        self.paused = paused


class SalesConversationAgent:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, customer: Customer, text: str) -> ConversationResult:
        lowered = text.strip().lower()

        # Human handoff triggers take precedence.
        handoff = self._detect_handoff(customer, text)
        if handoff:
            task = crm.create_handoff(
                self.db, reason=handoff["reason"], summary=handoff["summary"],
                customer_id=customer.customer_id, channel=ContactChannel.WHATSAPP.value
            )
            self.db.flush()
            return ConversationResult(
                reply=(
                    "Let me connect you with a member of our sales team who "
                    "can help with this. One moment, please."
                ),
                handoff=True,
                handoff_reason=handoff["reason"],
                handoff_summary=f"HumanHandoffTask {task.task_id}: {handoff['summary']}",
                paused=True,
            )

        # Opt-out / consent handling
        if self._is_optout(text):
            crm.mark_opt_out(self.db, customer.customer_id, reason="reply_stop", source_message=text)
            return ConversationResult(reply="You have been opted out of marketing messages. Noted.")

        if self._is_availability_question(text):
            reply = self._handle_availability(customer, text)
            return ConversationResult(reply=reply)

        if self._is_vehicle_request(text):
            reply = self._handle_vehicle_request(customer, text)
            return ConversationResult(reply=reply)

        if self._is_followup_schedule(text):
            return self._handle_followup_schedule(customer, text)

        if self._is_greeting(text):
            return ConversationResult(reply=self._greeting(customer))

        if self._is_price_question(text):
            return self._answer_price(customer, text)

        # Fallback: route through any active interests
        return self._fallback(customer, text)

    # ---- intent detection ----
    def _is_availability_question(self, text: str) -> bool:
        return any(
            kw in text
            for kw in ("available", "still have", "do you have", "in stock", "sold?")
        )

    def _is_vehicle_request(self, text: str) -> bool:
        return any(kw in text for kw in ("send photos", "show me", "photos", "list of cars"))

    def _is_followup_schedule(self, text: str) -> bool:
        return any(kw in text for kw in ("call me", "tomorrow", "sunday", "will decide", "i'll come", "i will come", "11 am", "am"))

    def _is_price_question(self, text: str) -> bool:
        return "price" in text or "cost" in text or "final price" in text or "how much" in text

    def _is_greeting(self, text: str) -> bool:
        return text in ("hi", "hello", "hey", "good morning", "good evening", "good afternoon")

    def _is_optout(self, text: str) -> bool:
        return any(kw in text for kw in ("stop", "unsubscribe", "opt out", "don't contact"))

    # ---- handoff detection ----
    def _detect_handoff(self, customer: Customer, text: str) -> Optional[dict]:
        lowered = text.lower()
        rules = [
            (HandoffReason.ANGRY_CUSTOMER.value, ["angry", "furious", "terrible service", "disgusted", "scam", "cheat"]),
            (HandoffReason.PRICE_NEGOTIATION.value, ["negotiat", "final price", "best price", "reduce", "discount", "bargain"]),
            (HandoffReason.LARGE_DISCOUNT_REQUEST.value, ["50% off", "half price", "big discount"]),
            (HandoffReason.LEGAL_QUESTION.value, ["legal", "lawyer", "court", "rto rules", "legal issue"]),
            (HandoffReason.FINANCING_APPROVAL.value, ["finance approval", "loan approved", "financing"]),
            (HandoffReason.PAYMENT_ISSUE.value, ["payment failed", "payment issue", "can't pay", "refund"]),
            (HandoffReason.COMPLAINT.value, ["complaint", "problem with", "not as described", "misrepresented"]),
            (HandoffReason.BOOKING_CONFIRMATION.value, ["confirm booking", "book now", "book the car"]),
            (HandoffReason.DOCUMENT_DISPUTE.value, ["document issue", "rc issue", "wrong document"]),
            (HandoffReason.VEHICLE_CONDITION_DISPUTE.value, ["damage not disclosed", "condition not as", "scratch you didn't"]),
        ]
        for reason, kws in rules:
            if any(kw in lowered for kw in kws):
                return {"reason": reason, "summary": f"Customer({customer.customer_id}): {text}"}
        return None

    # ---- availability ----
    def _resolve_vehicle(self, customer: Customer, text: str) -> List[Vehicle]:
        """Resolve the vehicle a customer means, using CRM interest records."""
        interests = self.db.execute(
            select(CustomerVehicleInterest).where(
                CustomerVehicleInterest.customer_id == customer.customer_id,
                CustomerVehicleInterest.interest_status.in_(["ACTIVE", "FOLLOW_UP"]),
            )
        ).scalars().all()
        interest_vehicles = [
            inventory.get_vehicle(self.db, i.vehicle_id) for i in interests if inventory.get_vehicle(self.db, i.vehicle_id)
        ]

        # try matching by keywords in the text against inventory search
        matched = self._search_by_keywords(text)
        if matched:
            return matched
        return [v for v in interest_vehicles if v]

    def _search_by_keywords(self, text: str) -> List[Vehicle]:
        lowered = text.lower()
        query = None
        for key in ("creta", "innova", "i20", "swift", "breeza", "suv", "diesel", "petrol", "wagonr", "verna", "venue", "alto"):
            if key in lowered:
                query = key
                break
        if query:
            return inventory.search_vehicles(self.db, q=query, limit=10)
        return []

    def _handle_availability(self, customer: Customer, text: str) -> str:
        vehicles = self._resolve_vehicle(customer, text)
        if not vehicles:
            reply = (
                "I could not find a matching vehicle in our current inventory. "
                "Could you share the brand and model you're looking for? "
                "I'll check availability for you right away."
            )
            crm.add_interaction(self.db, customer.customer_id, InteractionType.NOTE.value, "Availability query - no match found")
            return reply
        if len(vehicles) > 1:
            return self._ask_clarification(customer, vehicles)
        vehicle = vehicles[0]
        active = inventory.vehicle_is_active(vehicle)
        crm.customer_vehicle_interest(
            self.db, customer.customer_id, vehicle.vehicle_id,
            interest_type=InterestType.ENQUIRED.value, notes="Availability enquiry"
        )
        if active:
            return (
                f"Yes, the {vehicle.vehicle_name or vehicle.model} is currently available at KM Car Deals.\n\n"
                f"{self._vehicle_summary(vehicle)}\n\n"
                "Would you like more photos or a showroom visit?"
            )
        return (
            f"I'm sorry, the {vehicle.vehicle_name or vehicle.model} is currently not available for sale. "
            "Would you like me to suggest similar available models?"
        )

    def _ask_clarification(self, customer: Customer, vehicles: List[Vehicle]) -> str:
        lines = ["It looks like you've been interested in more than one vehicle. Which one do you mean?"]
        for i, v in enumerate(vehicles[:5], 1):
            lines.append(f"{i}. {v.vehicle_name or v.model} {v.manufacturing_year or ''}")
        return "\n".join(lines)

    def _vehicle_summary(self, v: Vehicle) -> str:
        lines = []
        if v.manufacturing_year:
            lines.append(f"Year: {v.manufacturing_year}")
        if v.fuel_type:
            lines.append(f"Fuel: {v.fuel_type}")
        if v.mileage_km:
            lines.append(f"Mileage: {v.mileage_km:,} km")
        if v.selling_price:
            lines.append(f"Price: ₹{v.selling_price:,.0f}")
        if v.transmission:
            lines.append(f"Transmission: {v.transmission}")
        if v.vehicle_color:
            lines.append(f"Color: {v.vehicle_color}")
        return "\n".join(lines or ["Details available on request."])

    # ---- vehicle request (photos) ----
    def _handle_vehicle_request(self, customer: Customer, text: str) -> str:
        vehicles = self._resolve_vehicle(customer, text)
        if not vehicles:
            return (
                "I'd be happy to share photos. Could you tell me which car you're "
                "interested in (brand and model)?"
            )
        vehicle = vehicles[0]
        photos = [p.file_path for p in vehicle.photos]
        if not photos:
            return "That vehicle's photos aren't uploaded yet. Let me confirm that for you."
        interests = self.db.execute(
            select(CustomerVehicleInterest).where(
                CustomerVehicleInterest.customer_id == customer.customer_id
            )
        ).scalars().all()
        return (
            f"Here are photos of the {vehicle.vehicle_name or vehicle.model}. "
            "Our team will send them over shortly. Would you like a showroom visit or test drive?"
        )

    # ---- follow-up scheduling ----
    def _handle_followup_schedule(self, customer: Customer, text: str) -> ConversationResult:
        from datetime import datetime, timedelta, timezone

        lowered = text.lower()
        scheduled = None
        reason = FollowupReason.CUSTOMER_DECISION.value
        now = datetime.now(timezone.utc)
        if "call me" in lowered or "call tomorrow" in lowered:
            reason = FollowupReason.CALL_REQUEST.value
            scheduled = now + timedelta(days=1)
            if "11" in lowered:
                scheduled = scheduled.replace(hour=11, minute=0, second=0)
        elif "will decide" in lowered or "decide tomorrow" in lowered:
            scheduled = now + timedelta(days=1)
        elif "sunday" in lowered:
            days = (6 - now.weekday()) % 7
            if days == 0:
                days = 7
            scheduled = (now + timedelta(days=days)).replace(hour=10, minute=0, second=0)
        elif "tomorrow" in lowered:
            scheduled = now + timedelta(days=1)

        followup = crm.create_followup(
            self.db, customer.customer_id, scheduled_for=scheduled,
            reason=reason, preferred_channel=ContactChannel.WHATSAPP.value
        )
        self.db.flush()
        return ConversationResult(
            reply="Noted! I've scheduled a follow-up for you. Is there anything else I can help with?",
            followup_create={"followup_id": followup.followup_id, "scheduled_for": str(scheduled)},
        )

    # ---- price ----
    def _answer_price(self, customer: Customer, text: str) -> str:
        vehicles = self._resolve_vehicle(customer, text)
        if not vehicles:
            return "Let me confirm the current price for you."
        vehicle = vehicles[0]
        if vehicle.selling_price:
            crm.add_interaction(self.db, customer.customer_id, InteractionType.NOTE.value, "Price query")
            return f"The price of the {vehicle.vehicle_name or vehicle.model} is ₹{vehicle.selling_price:,.0f}."
        return "Let me confirm the current price for you."

    # ---- greeting ----
    def _greeting(self, customer: Customer) -> str:
        name = customer.name or "there"
        return f"Hi {name}! Welcome to KM Car Deals. What type of vehicle are you looking for today?"

    # ---- fallback ----
    def _fallback(self, customer: Customer, text: str) -> str:
        vehicles = self._resolve_vehicle(customer, text)
        if vehicles:
            vehicle = vehicles[0]
            return self._answer_from_data(vehicle, text)
        return (
            "Thanks for your message! Let me check our inventory and confirm "
            "the details for you."
        )

    def _answer_from_data(self, vehicle: Vehicle, question: str) -> str:
        if ai_provider.name != "disabled":
            from km_car_deals.ai.prompts import SALES_ANSWER_PROMPT

            record = self._vehicle_summary(vehicle)
            raw = ai_provider.complete_llm(SALES_ANSWER_PROMPT.format(question=question, records=record))
            return raw.strip()[:500]
        # Deterministic fallback answers
        q = question.lower()
        if "owner" in q or "first owner" in q:
            return f"This {vehicle.vehicle_name or vehicle.model} has {vehicle.owner_count or 'N/A'} owner(s)." if vehicle.owner_count else "Let me confirm the owner details for you."
        if "mileage" in q:
            return f"Current mileage is {vehicle.mileage_km:,} km." if vehicle.mileage_km else "Let me confirm the exact mileage for you."
        if "fuel" in q or "diesel" in q or "petrol" in q:
            return f"This vehicle runs on {vehicle.fuel_type}." if vehicle.fuel_type else "Let me confirm the fuel type for you."
        if "location" in q or "showroom" in q:
            return f"Our showroom: {vehicle.location}." if vehicle.location else "Our showroom is open for visits. Let me confirm the location for you."
        if "finance" in q or "loan" in q:
            return "Yes, we can assist with finance options. A member of our team will help you with approval requirements."
        if "exchange" in q:
            return "Yes, we accept vehicle exchanges. Share your current car's details and we'll assess the value."
        if "test drive" in q or "book" in q:
            return "Yes, you can book a test drive! What time on the weekend would suit you?"
        return (
            f"For details on the {vehicle.vehicle_name or vehicle.model}, I can confirm the "
            "specifics for you. Which detail are you most interested in?"
        )
