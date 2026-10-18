# File: backend/app/ai_agent/agent.py
# Description: LangGraph-based Multilingual AI Health Assistant for SwasthyaGrid AI.
#   StateGraph flow:
#     detect_language → classify_intent → query_data → format_response
#
#   Supports 6 Indian languages: en, hi, mr, ta, te, bn.
#   OpenAI GPT-4o-mini is used when OPENAI_API_KEY is set; otherwise uses
#   handcrafted multilingual template responses (offline-capable).

import json
import logging
import re
from typing import Optional, Dict, Any, TypedDict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings

logger = logging.getLogger("swasthya.agent")

# ── Optional: LangGraph / LangChain ──────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph not installed; agent will use simplified sequential flow.")

try:
    from langdetect import detect as langdetect_detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not installed; using regex language detection fallback.")

try:
    from openai import AsyncOpenAI
    _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    OPENAI_AVAILABLE = bool(settings.OPENAI_API_KEY)
except ImportError:
    _openai_client = None
    OPENAI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Supported intents
# ---------------------------------------------------------------------------
INTENTS = [
    "INVENTORY",     # Medicine stock, stockouts, burn rate
    "FOOTFALL",      # Patient OPD count, wait time
    "BEDS",          # Bed availability, occupancy
    "STAFF",         # Doctor/nurse attendance, leave
    "ALERTS",        # Critical alerts, interventions, distress index
    "ECONOMICS",     # Budget, expenditure, purchase orders
    "GENERAL",       # Greeting / generic
]

# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

_LANG_PATTERNS: Dict[str, list] = {
    "hi": ["इन्वेंटरी", "दवाई", "बेड", "डॉक्टर", "अलर्ट", "स्टॉक", "मरीज", "हेल्थ", "अस्पताल"],
    "mr": ["औषध", "रुग्ण", "डॉक्टर", "बेड", "इस्पितळ", "स्टॉक", "सावधान"],
    "ta": ["மருந்து", "நோயாளி", "மருத்துவர்", "படுக்கை", "மருத்துவமனை"],
    "te": ["మందు", "రోగి", "వైద్యుడు", "బెడ్", "ఆసుపత్రి", "స్టాక్"],
    "bn": ["ওষুধ", "রোগী", "ডাক্তার", "বেড", "হাসপাতাল", "স্টক"],
}


def detect_language(text: str) -> str:
    """
    Detect the language of *text*.
    Priority: langdetect library → regex keyword matching → 'en' default.
    """
    if LANGDETECT_AVAILABLE:
        try:
            detected = langdetect_detect(text)
            if detected in ("hi", "mr", "ta", "te", "bn", "en"):
                return detected
        except Exception:
            pass

    text_lower = text.lower()
    for lang, keywords in _LANG_PATTERNS.items():
        if any(kw in text for kw in keywords):
            return lang

    return "en"


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: Dict[str, list] = {
    "INVENTORY": ["stock", "medicine", "drug", "pharmacy", "inventory", "stockout",
                  "supply", "दवाई", "इन्वेंटरी", "औषध", "மருந்து", "మందు", "ওষুধ"],
    "FOOTFALL":  ["patient", "opd", "queue", "footfall", "visit", "waiting",
                  "मरीज", "रोगी", "நோயாளி", "రోగి", "রোগী"],
    "BEDS":      ["bed", "ward", "occupy", "admission", "icu", "maternity",
                  "बेड", "बिस्तर", "படுக்கை", "బెడ్", "বেড"],
    "STAFF":     ["doctor", "nurse", "staff", "attend", "absent", "leave",
                  "डॉक्टर", "नर्स", "மருத்துவர்", "వైద్యుడు", "ডাক্তার"],
    "ALERTS":    ["alert", "critical", "distress", "warning", "danger", "emergency",
                  "अलर्ट", "खतरा", "சேதார", "హెచ్చరిక", "সতর্ক"],
    "ECONOMICS": ["budget", "expense", "cost", "expenditure", "purchase", "order",
                  "बजट", "खर्च", "பட்ஜெட்", "బడ్జెట్", "বাজেট"],
}


def classify_intent(text: str) -> str:
    """Classify user query into one of the INTENTS using keyword matching."""
    text_lower = text.lower()
    scores = {intent: 0 for intent in INTENTS}
    for intent, keywords in _INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                scores[intent] += 1
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "GENERAL"


# ---------------------------------------------------------------------------
# Response templates (offline-capable, 6 languages)
# ---------------------------------------------------------------------------

_TEMPLATES: Dict[str, Dict[str, str]] = {
    "INVENTORY": {
        "en": "📦 Inventory Summary for {facility}: {critical} critical stockouts, {warning} warnings. Total medicines tracked: {total}.",
        "hi": "📦 {facility} की इन्वेंटरी: {critical} गंभीर स्टॉकआउट, {warning} चेतावनियाँ। कुल दवाइयाँ: {total}।",
        "mr": "📦 {facility} साठी इन्व्हेंटरी: {critical} गंभीर स्टॉकआउट, {warning} सावधानता. एकूण: {total}.",
        "ta": "📦 {facility} இன்வென்டரி: {critical} முக்கியமான குறைவு, {warning} எச்சரிக்கைகள். மொத்தம்: {total}.",
        "te": "📦 {facility} స్టాక్: {critical} క్రిటికల్ స్టాక్అవుట్, {warning} హెచ్చరికలు. మొత్తం: {total}.",
        "bn": "📦 {facility} ইনভেন্টরি: {critical} সংকটজনক স্টকআউট, {warning} সতর্কতা। মোট: {total}।",
    },
    "FOOTFALL": {
        "en": "🏥 Footfall at {facility}: {count} patients today, {waiting} currently waiting.",
        "hi": "🏥 {facility} में आज {count} मरीज़, {waiting} प्रतीक्षारत।",
        "mr": "🏥 {facility} मध्ये आज {count} रुग्ण, {waiting} प्रतीक्षेत आहेत.",
        "ta": "🏥 {facility}: இன்று {count} நோயாளிகள், {waiting} காத்திருக்கிறார்கள்.",
        "te": "🏥 {facility}: ఈ రోజు {count} రోగులు, {waiting} వేచి ఉన్నారు.",
        "bn": "🏥 {facility}: আজ {count} রোগী, {waiting} জন অপেক্ষা করছেন।",
    },
    "BEDS": {
        "en": "🛏 Bed Status at {facility}: {occupied} occupied / {total} total. {available} beds available.",
        "hi": "🛏 {facility} में {occupied}/{total} बेड भरे हैं। {available} खाली।",
        "mr": "🛏 {facility}: {occupied}/{total} बेड भरलेले. {available} रिकामे.",
        "ta": "🛏 {facility}: {occupied}/{total} படுக்கைகள் நிரம்பியுள்ளன. {available} காலியாக உள்ளன.",
        "te": "🛏 {facility}: {occupied}/{total} బెడ్లు నిండాయి. {available} ఖాళీగా ఉన్నాయి.",
        "bn": "🛏 {facility}: {occupied}/{total} বেড ভর্তি। {available}টি খালি।",
    },
    "STAFF": {
        "en": "👨‍⚕️ Staff at {facility}: {present} present today out of {total}. {absent} absences.",
        "hi": "👨‍⚕️ {facility}: {total} में से {present} डॉक्टर/कर्मचारी उपस्थित। {absent} अनुपस्थित।",
        "mr": "👨‍⚕️ {facility}: {total} पैकी {present} उपस्थित. {absent} अनुपस्थित.",
        "ta": "👨‍⚕️ {facility}: {total} இல் {present} பேர் வந்துள்ளனர். {absent} இல்லை.",
        "te": "👨‍⚕️ {facility}: {total} లో {present} మంది హాజరు. {absent} మంది గైర్హాజరు.",
        "bn": "👨‍⚕️ {facility}: {total} জনের মধ্যে {present} জন উপস্থিত। {absent} অনুপস্থিত।",
    },
    "ALERTS": {
        "en": "🚨 Active Alerts at {facility}: {critical} CRITICAL, {warning} WARNING flags. Immediate action required.",
        "hi": "🚨 {facility} में सक्रिय अलर्ट: {critical} गंभीर, {warning} चेतावनी। तत्काल कार्रवाई आवश्यक।",
        "mr": "🚨 {facility}: {critical} गंभीर, {warning} इशारे. त्वरित कार्यवाही आवश्यक.",
        "ta": "🚨 {facility}: {critical} முக்கியமான, {warning} எச்சரிக்கைகள். உடனடி நடவடிக்கை தேவை.",
        "te": "🚨 {facility}: {critical} క్రిటికల్, {warning} హెచ్చరికలు. వెంటనే చర్య అవసరం.",
        "bn": "🚨 {facility}: {critical} জরুরি, {warning} সতর্কতা। দ্রুত পদক্ষেপ প্রয়োজন।",
    },
    "ECONOMICS": {
        "en": "💰 Budget at {facility}: ₹{budget} allocated, ₹{spent} spent ({utilization}% used). Burn rate: ₹{burn_rate}/day.",
        "hi": "💰 {facility} बजट: ₹{budget} आवंटित, ₹{spent} खर्च ({utilization}% उपयोग)।",
        "mr": "💰 {facility}: ₹{budget} वाटप, ₹{spent} खर्च ({utilization}%). बर्न रेट: ₹{burn_rate}/दिवस.",
        "ta": "💰 {facility}: ₹{budget} ஒதுக்கீடு, ₹{spent} செலவு ({utilization}%).",
        "te": "💰 {facility}: ₹{budget} కేటాయించారు, ₹{spent} ఖర్చు ({utilization}%).",
        "bn": "💰 {facility}: ₹{budget} বরাদ্দ, ₹{spent} ব্যয় ({utilization}%)।",
    },
    "GENERAL": {
        "en": "👋 Hi! I'm SwasthyaGrid AI Assistant. I can help with inventory, patients, beds, staff, alerts, and economics. What would you like to know?",
        "hi": "👋 नमस्ते! मैं SwasthyaGrid AI हूँ। इन्वेंटरी, मरीज, बेड, स्टाफ, अलर्ट और बजट के बारे में पूछें।",
        "mr": "👋 नमस्कार! मी SwasthyaGrid AI आहे. इन्व्हेंटरी, रुग्ण, बेड, कर्मचारी बद्दल विचारा.",
        "ta": "👋 வணக்கம்! நான் SwasthyaGrid AI. மருந்து, நோயாளி, படுக்கை பற்றி கேளுங்கள்.",
        "te": "👋 నమస్కారం! నేను SwasthyaGrid AI. ఇన్వెంటరీ, రోగులు, బెడ్స్ గురించి అడగండి.",
        "bn": "👋 নমস্কার! আমি SwasthyaGrid AI। ইনভেন্টরি, রোগী, বেড সম্পর্কে জিজ্ঞাসা করুন।",
    },
}


# ---------------------------------------------------------------------------
# Database query functions (async)
# ---------------------------------------------------------------------------

async def _query_inventory(db: AsyncSession, facility_id: Optional[str]) -> Dict[str, Any]:
    from app.models.inventory import MedicineStock
    q = select(MedicineStock)
    if facility_id:
        q = q.where(MedicineStock.facility_id == facility_id)
    result = await db.execute(q)
    stocks = result.scalars().all()
    critical = sum(1 for s in stocks if s.days_of_supply <= 3)
    warning  = sum(1 for s in stocks if 3 < s.days_of_supply <= 7)
    return {"critical": critical, "warning": warning, "total": len(stocks)}


async def _query_footfall(db: AsyncSession, facility_id: Optional[str]) -> Dict[str, Any]:
    from app.models.patient_crm import OPDVisit
    from datetime import date
    today = date.today()
    q = select(OPDVisit)
    if facility_id:
        q = q.where(OPDVisit.facility_id == facility_id)
    result = await db.execute(q)
    visits = result.scalars().all()
    today_visits = [v for v in visits if hasattr(v, "created_at") and v.created_at.date() == today]
    waiting = sum(1 for v in today_visits if getattr(v, "status", "") == "waiting")
    return {"count": len(today_visits), "waiting": waiting}


async def _query_beds(db: AsyncSession, facility_id: Optional[str]) -> Dict[str, Any]:
    from app.models.beds import Bed
    q = select(Bed)
    if facility_id:
        q = q.where(Bed.facility_id == facility_id)
    result = await db.execute(q)
    beds = result.scalars().all()
    occupied  = sum(1 for b in beds if getattr(b, "status", "") == "occupied")
    total     = len(beds)
    available = total - occupied
    return {"occupied": occupied, "total": total, "available": max(0, available)}


async def _query_staff(db: AsyncSession, facility_id: Optional[str]) -> Dict[str, Any]:
    from app.models.staff_attendance import DoctorStaff
    from datetime import date
    q = select(DoctorStaff)
    if facility_id:
        q = q.where(DoctorStaff.facility_id == facility_id)
    result = await db.execute(q)
    staff = result.scalars().all()
    total   = len(staff)
    present = sum(1 for s in staff if getattr(s, "is_on_duty", True))
    absent  = total - present
    return {"total": total, "present": present, "absent": absent}


async def _query_alerts(db: AsyncSession, facility_id: Optional[str]) -> Dict[str, Any]:
    from app.models.alerts_interventions import InterventionAlert
    q = select(InterventionAlert)
    if facility_id:
        q = q.where(InterventionAlert.facility_id == facility_id)
    result = await db.execute(q)
    alerts = result.scalars().all()
    critical = sum(1 for a in alerts if getattr(a, "severity", "") in ("critical", "red"))
    warning  = sum(1 for a in alerts if getattr(a, "severity", "") in ("warning", "yellow"))
    return {"critical": critical, "warning": warning}


async def _query_economics(db: AsyncSession, facility_id: Optional[str]) -> Dict[str, Any]:
    from app.models.economics import BudgetAllocation, Expenditure
    from datetime import datetime
    year = datetime.utcnow().year

    ba_q = select(BudgetAllocation).where(BudgetAllocation.fiscal_year == year)
    if facility_id:
        ba_q = ba_q.where(BudgetAllocation.facility_id == facility_id)
    ba_result = await db.execute(ba_q)
    allocations = ba_result.scalars().all()
    total_budget = sum(a.allocated_amount for a in allocations)

    ex_q = select(Expenditure)
    if facility_id:
        ex_q = ex_q.where(Expenditure.facility_id == facility_id)
    ex_result = await db.execute(ex_q)
    expenditures = ex_result.scalars().all()
    total_spent = sum(e.amount for e in expenditures)

    utilization = round((total_spent / total_budget * 100), 1) if total_budget > 0 else 0
    from datetime import datetime
    days_passed = datetime.utcnow().timetuple().tm_yday
    burn_rate = round(total_spent / max(1, days_passed), 0)

    return {
        "budget": round(total_budget),
        "spent": round(total_spent),
        "utilization": utilization,
        "burn_rate": int(burn_rate),
    }


_QUERY_FUNCS = {
    "INVENTORY": _query_inventory,
    "FOOTFALL":  _query_footfall,
    "BEDS":      _query_beds,
    "STAFF":     _query_staff,
    "ALERTS":    _query_alerts,
    "ECONOMICS": _query_economics,
}


# ---------------------------------------------------------------------------
# Core agent pipeline
# ---------------------------------------------------------------------------

async def run_agent(
    query: str,
    db: AsyncSession,
    facility_id: Optional[str] = None,
    language_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the full agent pipeline for a user query.

    Steps:
      1. detect_language
      2. classify_intent
      3. query_data (async DB)
      4. format_response (templates or OpenAI)

    Returns:
        {
            "response": str,       # Final formatted response
            "language": str,       # Detected / used language code
            "intent": str,         # Classified intent
            "data": dict,          # Raw query data
            "facility_id": str,    # Used facility scope
        }
    """
    # Step 1: Language detection
    lang = language_hint or detect_language(query)
    if lang not in ("en", "hi", "mr", "ta", "te", "bn"):
        lang = "en"

    # Step 2: Intent classification
    intent = classify_intent(query)

    # Step 3: Query data
    data: Dict[str, Any] = {}
    if intent in _QUERY_FUNCS:
        try:
            data = await _QUERY_FUNCS[intent](db, facility_id)
        except Exception as exc:
            logger.warning(f"Agent DB query failed for intent {intent}: {exc}")
            data = {}

    # Facility name (use ID as fallback for display)
    facility_name = facility_id or "District"
    if facility_id:
        try:
            from app.models.facility import Facility
            res = await db.execute(select(Facility).where(Facility.id == facility_id))
            fac = res.scalar_one_or_none()
            if fac:
                facility_name = fac.name
        except Exception:
            pass

    # Step 4: Format response
    response = await _format_response(query, intent, lang, data, facility_name)

    return {
        "response": response,
        "language": lang,
        "intent": intent,
        "data": data,
        "facility_id": facility_id,
    }


async def _format_response(
    query: str,
    intent: str,
    lang: str,
    data: Dict[str, Any],
    facility_name: str,
) -> str:
    """Format a response using OpenAI GPT-4o-mini (if available) or multilingual templates."""

    # ── Try OpenAI first ──────────────────────────────────────────────────────
    if OPENAI_AVAILABLE and _openai_client:
        system_prompt = (
            "You are SwasthyaGrid AI, a multilingual health assistant for Indian rural clinics (PHC/CHC). "
            f"The user asked in language code '{lang}'. Respond in the SAME language. "
            f"Intent detected: {intent}. Data available: {json.dumps(data)}. "
            f"Facility context: {facility_name}. "
            "Provide a concise, helpful response under 100 words. Include the key data naturally."
        )
        try:
            completion = await _openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                max_tokens=200,
                temperature=0.3,
            )
            return completion.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning(f"OpenAI fallback failed: {exc}")

    # ── Template fallback ─────────────────────────────────────────────────────
    template = _TEMPLATES.get(intent, _TEMPLATES["GENERAL"]).get(lang, _TEMPLATES.get(intent, {}).get("en", ""))
    if not template:
        return _TEMPLATES["GENERAL"].get(lang, _TEMPLATES["GENERAL"]["en"])

    # Fill template with data, defaulting missing keys to "N/A"
    fill = {"facility": facility_name}
    fill.update({k: v for k, v in data.items()})
    try:
        return template.format_map({k: fill.get(k, "N/A") for k in re.findall(r"\{(\w+)\}", template)})
    except Exception:
        return template
