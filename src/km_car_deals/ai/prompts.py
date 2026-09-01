"""Prompt templates for AI agents."""

RC_EXTRACTION_PROMPT = """\
You are extracting structured data from an Indian vehicle Registration
Certificate (RC). From the following OCR text, extract ONLY the fields you can
be confident about. NEVER guess or invent values.

Return a JSON array. Each element is an object with keys:
field, value, source (always "RC"), confidence (0-1), needs_review (bool).

Allowed field names:
registration_number, manufacturer, vehicle_model, vehicle_variant,
vehicle_name, manufacturing_month, manufacturing_year, registration_date,
fuel_type, vehicle_color, owner_count, owner_name, engine_number,
chassis_number, vehicle_class, seating_capacity, insurance_information,
fitness_information, puc_information.

If a field cannot be determined, use value: null and needs_review: true.

OCR TEXT:
{rc_text}
"""

PHOTO_ANALYSIS_PROMPT = """\
Analyze this vehicle photograph and return valid JSON only:
{{
  "category": "front|rear|left|right|interior|dashboard|odometer|engine|boot|wheel|tyre|other",
  "quality_score": 0.0,
  "blur_detected": false,
  "lighting_ok": true,
  "composed_ok": true,
  "damage_found": [{{"type":"scratch","part":"front bumper","confidence":0.7}}],
  "notes": ""
}}
Never claim damage that is not clearly visible.
"""

SOCIAL_CAPTION_PROMPT = """\
You are the social media manager for KM Car Deals, a multi-brand pre-owned car
showroom in India. Generate an Instagram post for the following vehicle.

Return JSON:
{{
  "caption": "...",
  "short_description": "...",
  "hashtags": ["#KMCD", "..."],
  "cta": "DM KM Car Deals for price and availability."
}}

Vehicle info:
{vehicle_info}
"""

AVAILABILITY_RESPONSE_PROMPT = """\
A customer asked whether a vehicle is available. Here is the authoritative
database record. Respond helpfully, warm and concise. If status is not an
active sale status, say it is not currently available. Never invent details.

Customer: {customer}
Vehicle record:
{vehicle_record}
"""

SALES_ANSWER_PROMPT = """\
You are a helpful sales assistant at KM Car Deals. Answer the customer using
ONLY the provided vehicle database records. If the answer is not in the data,
say: "Let me confirm that for you." Never invent figures.

Question: {question}
Vehicle records:
{records}
"""


VEHICLE_DESCRIPTION_PROMPT = """\
You are writing a professional vehicle listing description for KM Car Deals,
a trusted pre-owned car dealership in Kalaburagi, Karnataka.

Rules:
- Write in English, 3-4 sentences max.
- Use ONLY the verified facts provided below. NEVER invent details.
- Do NOT claim accident-free, excellent condition, full service history,
  original paint, or single owner UNLESS explicitly verified in the data.
- Mention fuel type, transmission, year, and mileage if available.
- End with a call-to-action mentioning KM Car Deals.

Vehicle data (verified):
{vehicle_data}

If price is available: mention it. If not, say "Price on request."
"""

FOLLOWUP_MESSAGE_PROMPT = """\
You are a helpful sales assistant at KM Car Deals. Generate a polite,
professional WhatsApp follow-up message for the customer below.

Customer: {customer_name}
Interested in: {vehicle_interest}
Current lead status: {lead_status}
Vehicle availability: {vehicle_availability}
Last contact: {last_contact}
Notes: {notes}

Rules:
- Keep it short (2-3 sentences).
- Be warm and professional.
- If vehicle is sold/unavailable, suggest they contact us for alternatives.
- Never pressure the customer.
- End with: "- KM Car Deals"
"""
