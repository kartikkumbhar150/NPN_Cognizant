"""Intent router for the HDFC banking chatbot.

Three-layer classification::

    Layer 1 — Deterministic rules (regex/phrase matching, banking-affinity guard)
    Layer 2 — Optional classifier (Protocol, never required)
    Layer 3 — Safe fallback (banking-domain detector)

Final precedence (first match wins)::
    1. UNSAFE_OR_SENSITIVE
    2. CUSTOMER_ACCOUNT_QUERY
    3. TRANSACTION_QUERY
    4. PERSONALIZED_RECOMMENDATION
    5. PRODUCT_COMPARISON
    6. SERVICE_HELP
    7. GENERAL_BANKING_QUERY
    8. PRODUCT_INFORMATION

IMPORTANT — Follow-up fix (Hermes P2): bare product-detail language
(fees, features, benefits, eligibility) is treated as PRODUCT_INFORMATION
even without explicit banking keywords, so multi-turn follow-ups like
"What are its fees?" are correctly routed to product-lookup instead of
falling through to OUT_OF_SCOPE.  This matches Hermes's debugging
finding on the reference branch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Protocol, runtime_checkable

from chatbot.app.models.chat_models import ChatIntent, MAX_MESSAGE_LENGTH


# ── Routing decision ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RoutingDecision:
    """Structured output of intent classification."""

    intent: ChatIntent
    confidence: float
    reason: str
    requires_retrieval: bool = False
    requires_customer_context: bool = False
    requires_recommendation: bool = False
    requires_account_access: bool = False
    requires_transaction_access: bool = False
    requires_authenticated_context: bool = False
    safety_flags: tuple = ()

    def __post_init__(self) -> None:
        if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool):
            raise ValueError(f"confidence must be a number, got {self.confidence!r}")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence!r}")


# ── Capability mapping (deterministic, testable) ──────────────────────────

_INTENT_CAPABILITIES: Dict[ChatIntent, Dict[str, bool]] = {
    ChatIntent.GENERAL_BANKING_QUERY: {
        "requires_retrieval": True, "requires_customer_context": False,
        "requires_recommendation": False, "requires_account_access": False,
        "requires_transaction_access": False, "requires_authenticated_context": False,
    },
    ChatIntent.PRODUCT_INFORMATION: {
        "requires_retrieval": True, "requires_customer_context": False,
        "requires_recommendation": False, "requires_account_access": False,
        "requires_transaction_access": False, "requires_authenticated_context": False,
    },
    ChatIntent.PRODUCT_COMPARISON: {
        "requires_retrieval": True, "requires_customer_context": False,
        "requires_recommendation": False, "requires_account_access": False,
        "requires_transaction_access": False, "requires_authenticated_context": False,
    },
    ChatIntent.PERSONALIZED_RECOMMENDATION: {
        "requires_retrieval": True, "requires_customer_context": True,
        "requires_recommendation": True, "requires_account_access": False,
        "requires_transaction_access": False, "requires_authenticated_context": True,
    },
    ChatIntent.CUSTOMER_ACCOUNT_QUERY: {
        "requires_retrieval": False, "requires_customer_context": True,
        "requires_recommendation": False, "requires_account_access": True,
        "requires_transaction_access": False, "requires_authenticated_context": True,
    },
    ChatIntent.TRANSACTION_QUERY: {
        "requires_retrieval": False, "requires_customer_context": True,
        "requires_recommendation": False, "requires_account_access": False,
        "requires_transaction_access": True, "requires_authenticated_context": True,
    },
    ChatIntent.SERVICE_HELP: {
        "requires_retrieval": True, "requires_customer_context": False,
        "requires_recommendation": False, "requires_account_access": False,
        "requires_transaction_access": False, "requires_authenticated_context": False,
    },
    ChatIntent.OUT_OF_SCOPE: {
        "requires_retrieval": False, "requires_customer_context": False,
        "requires_recommendation": False, "requires_account_access": False,
        "requires_transaction_access": False, "requires_authenticated_context": False,
    },
    ChatIntent.UNSAFE_OR_SENSITIVE: {
        "requires_retrieval": False, "requires_customer_context": False,
        "requires_recommendation": False, "requires_account_access": False,
        "requires_transaction_access": False, "requires_authenticated_context": False,
    },
}


# ── Optional classifier abstraction (Layer 2) ────────────────────────────

@runtime_checkable
class IntentClassificationProvider(Protocol):
    def classify(self, message: str) -> ChatIntent: ...


# ── Normalization ─────────────────────────────────────────────────────────

_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.strip().lower())


# ── Banking-domain vocabulary ───────────────────────────────────────────────

_BANKING_TERMS = frozenset({
    "account", "accounts", "bank", "banking", "hdfc",
    "credit card", "credit cards", "debit card", "debit cards",
    "loan", "loans", "deposit", "deposits", "fixed deposit",
    "recurring deposit", "upi", "neft", "rtgs", "imps",
    "forex", "nri", "transaction", "transactions", "payment", "payments",
    "interest", "emi", "netbanking", "net banking", "fastag",
    "balance", "statement", "pin", "otp", "atm", "cheque", "check",
    "branch", "ifsc", "micr", "nominee", "kyc", "insurance",
    "mutual fund", "demat", "trading", "portfolio", "investment",
    "savings", "current account", "salary account", "credit limit",
    "cashback", "reward point", "forex card", "travel card",
    "annual fee", "joining fee", "prepayment", "foreclosure",
    "demand draft", "wire transfer", "remittance", "credit score",
    "cibil", "grievance", "complaint", "dispute", "hotlist",
    "locker", "overdraft", "customer id", "beneficiary",
    "card", "cards", "password", "aadhaar", "rewards", "cheque book",
    "support", "mobile number",
    "regalia", "millennia", "millenia", "infinia", "diners",
    "freedom", "moneyback", "titanium", "indigo",
})


def _banking_affinity(normalized: str) -> bool:
    return "hdfc" in normalized or any(term in normalized for term in _BANKING_TERMS)


# ── Negation guards ─────────────────────────────────────────────────────────

_NEGATED_RECOMMENDATION = re.compile(
    r"(?:don'?t|do not|not)\s+(?:want|need|asking for|looking for|here for|seeking)\s+"
    r"(?:a\s+|any\s+)?(?:recommendation|suggestion|advice|to be recommended)",
    re.IGNORECASE,
)

_NEGATED_TRANSACTION = re.compile(
    r"(?:don'?t|do not|stop|no need to|not)\s+(?:show(?:ing)?|need|want|see|check|give|share)\s+"
    r"(?:my\s+|the\s+|any\s+)?(?:transactions?|payments?|purchases?|statement)",
    re.IGNORECASE,
)

_NEGATED_UNSAFE = re.compile(
    r"(?:i'?m\s+)?not\s+asking\s+(?:how\s+)?to"
    r"|don'?t\s+(?:want|need)\s+to\s+know\s+how\s+to"
    r"|not\s+asking\s+about"
    r"|isn'?t\s+about\s+(?:bypassing|hacking|stealing)"
    r"|\bmy\s+(?:account|card|bank)\s+(?:was|is|has\s+been)\s+(?:hacked|compromised|breached)"
    r"|(?:prevent|protect(?:ion|s|ing)?|stop|avoid|defend\s+against)\s+(?:unauthorized|fraud|hack)",
    re.IGNORECASE,
)

_WHICH_OF_THESE = re.compile(r"which\s+of\s+(?:these|the\s+two)\b", re.IGNORECASE)


# ── Layer-1 rule matchers (precedence order) ─────────────────────────────

# 1. UNSAFE_OR_SENSITIVE
_UNSAFE_PATTERN = re.compile(
    r"(?:another\s+customer|someone\s+else|other\s+customer|other\s+user"
    r"|someone'?s\s+(?:transaction|account|balance|card)"
    r"|another\s+person'?s"
    r"|their\s+(?:account|card|balance|transaction|details?|pin|otp)"
    r"|cust[a-z0-9]*'s"
    r"|bypass\s+(?:otp|authentication|verification|auth|2fa|security)"
    r"|bypass\s+(?:login|otp|verification|authentication)\s+to\s+(?:access|another|someone|a\s+|an?\s+)"
    r"|skip\s+(?:otp|verification|authentication)"
    r"|without\s+(?:authentication|otp|verification|authoriz)"
    r"|unauthorized\s+access"
    r"|\bhack(?:ing)?\s+(?:into\s+)?(?:someone'?s?\s+)?(?:an?\s+)?(?:bank\s+)?(?:hdfc\s+)?account"
    r"|\bhack(?:ing)?\s+(?:into\s+)?(?:an?\s+)?(?:bank|hdfc)\b"
    r"|\b(?:access|get(?:\s+into)?|break\s+into?|log\s+into?|enter)\s+(?:another|someone'?s?\s+|other\s+|a\s+customer'?s?\s+|some\s+)(?:person'?s?\s+|customer'?s?\s+)?(?:bank\s+|hdfc\s+)?(?:account|card|profile|details?)\b"
    r"|\bbreak\s+into\s+(?:an?\s+)?(?:bank\s+|hdfc\s+)?(?:account|bank|hdfc)\b"
    r"|\bsteal\s+(?:someone'?s?\s+)?(?:banking\s+)?(?:money|credentials?|card|data|information|details?)\b"
    r"|\btake\s+money\s+from\s+someone"
    r"|\bimpersonate\b"
    r"|(?:create|make|build|design)\s+(?:a\s+)?phishing"
    r"|phishing\s+(?:page|site|email|link|kit|website)"
    r"|fake\s+(?:identity|kyc|documents?)"
    r"|forge\d?\s+(?:cheque|document)"
    r"|\blaunder\b)",
    re.IGNORECASE,
)

def _match_unsafe(text: str, affinity: bool) -> bool:
    return bool(_UNSAFE_PATTERN.search(text)) and not _NEGATED_UNSAFE.search(text)


# 2. CUSTOMER_ACCOUNT_QUERY
_ACCT_PATTERN = re.compile(
    r"(?:my\s+(?:account\s+)?balance"
    r"|my\s+(?:savings|current|loan|credit\s+card)\s+(?:account\s+)?(?:balance|details?|status)"
    r"|my\s+account\s+(?:details?|status|information|number|balance|statement)"
    r"|account\s+(?:balance|statement|details?|status|information)"
    r"|bank\s+balance|savings\s+balance|current\s+balance"
    r"|(?:check|know|what\s+is|what's|show|tell\s+me)\s+(?:my\s+)?balance"
    r"|my\s+(?:fixed\s+)?deposits?\b|my\s+emi\b|emi\s+(?:due|status|schedule)"
    r"|my\s+(?:overdraft|od)\b|my\s+available\s+balance|my\s+ledger\s+balance"
    r"|how\s+much\s+(?:money\s+)?(?:do|have)\s+i\s+got|how\s+much\s+is\s+in\s+my)",
    re.IGNORECASE,
)

_CONCEPTUAL_SAFETY = re.compile(
    r"(?:deposit|money|balance)\s+(?:is\s+)?(?:safe|insured|protected)", re.IGNORECASE
)

def _match_account_query(text: str, affinity: bool) -> bool:
    if _CONCEPTUAL_SAFETY.search(text):
        return False
    return bool(_ACCT_PATTERN.search(text))


# 3. TRANSACTION_QUERY
_TX_PATTERN = re.compile(
    r"(?:\b(?:my|recent|last|past|all|pending|latest)\b[^.!?]{0,40}"
    r"\b(?:transactions?|purchases?|payments?|expenses?)\b"
    r"|\b(?:transactions?|purchases?|payments?)\b[^.!?]{0,25}\b(?:history|details?|log)\b"
    r"|\bwhat\s+did\s+i\s+(?:spend|buy|pay|purchase)\b"
    r"|\bspending\s+history\b|\bexpense\s+history\b|\bpayment\s+history\b"
    r"|\b(?:show|view|list|get|check|see|download)\b[^.!?]{0,30}"
    r"\b(?:transactions?|purchases?)\b)",
    re.IGNORECASE,
)

def _match_transaction(text: str, affinity: bool) -> bool:
    return bool(_TX_PATTERN.search(text)) and not _NEGATED_TRANSACTION.search(text)


# 4. PERSONALIZED_RECOMMENDATION
_REC_STRONG_PATTERN = re.compile(
    r"(?:\bbest\b[^.!?]{0,40}\bfor\s+me\b"
    r"|\bwhich\b[^.!?]{0,40}\b(?:should\s+i|would\s+(?:you\s+)?(?:recommend|suggest)|for\s+me|suits?\s+me|good\s+for\s+me)\b"
    r"|\bwhat\s+(?:(?:credit|debit|hdfc|travel|forex)\s+){0,2}(?:card|loan|plan|option|product|account|fd)s?\s+should\s+i\b"
    r"|\b(?:what|which)\s+(?:(?:credit|debit|hdfc|travel|forex)\s+){0,2}(?:card|loan)s?\s+(?:should|would|could)\s+i\s+(?:get|choose|pick|take|go\s+for|consider)\b"
    r"|\bsuitable\s+for\s+me\b|\bsuits?\s+me\b"
    r"|\bright\s+(?:card|loan|option|product|choice)\s+for\s+me\b"
    r"|\bbased\s+on\s+my\s+(?:spending|salary|income|profile|usage|needs|transactions?|expenses?)\b"
    r"|\bfor\s+my\s+(?:profile|needs|usage|spending|salary|income)\b"
    r"|\bwhat\s+should\s+i\s+(?:choose|get|pick|go\s+for|consider)\b"
    r"|\bwhat\s+(?:(?:credit|debit|hdfc|travel|forex)\s+){0,2}(?:card|loan|plan|option|product|account|fd)s?\s+would\s+(?:you\s+)?recommend\b"
    r"|\bpersonalized?\b|\btailored\s+(?:for|to)\b"
    r"|\bmy\s+(?:salary|income|monthly\s+spend\w*|spending\s+pattern)\b"
    r"|\bi\s+earn\b|\bi\s+spend\b"
    r"|\bi\s+(?:travel|dine|shop|fly)\s+(?:a\s+lot|internationally|frequently|online|often|abroad)\b"
    r"|\bfrequent\s+(?:travell?er|flyer)\b|\b(?:heavy|high)\s+spender\b"
    r"|\bwhich\s+(?:is|would\s+be)\s+(?:good|right|better)\s+for\s+me\b)",
    re.IGNORECASE,
)

_REC_BARE_PATTERN = re.compile(
    r"\b(?:recommend|suggest)(?:ation|s|ing)?\b", re.IGNORECASE,
)

def _match_recommendation(text: str, affinity: bool) -> bool:
    if _NEGATED_RECOMMENDATION.search(text):
        return False
    if _WHICH_OF_THESE.search(text):
        return False
    if _REC_STRONG_PATTERN.search(text):
        return True
    return affinity and bool(_REC_BARE_PATTERN.search(text))


# 5. PRODUCT_COMPARISON
_CMP_PATTERN = re.compile(
    r"(?:\bcompare\b|\bcomparison\b|\bdifference\s+between\b"
    r"|\bvs\.?\b|\bversus\b"
    r"|\bwhich\s+is\s+better\b|\bwhich\s+of\s+(?:these|the\s+two)\b"
    r"|\bpros?\s+and\s+cons?\b"
    r"|\bbetter\s+(?:between|among)\b|\bchoose\s+between\b"
    r"|\bcompared?\s+to\b.*\b(?:card|loan|plan|account|deposit)\b"
    r"|\b(?:card|loan|plan|account|deposit)s?\b[^.!?]{0,25}\bor\b[^.!?]{0,25}\b(?:card|loan|plan|account|deposit)s?\b)",
    re.IGNORECASE,
)

def _match_comparison(text: str, affinity: bool) -> bool:
    return affinity and bool(_CMP_PATTERN.search(text))


# 6. SERVICE_HELP
_SVC_PATTERN = re.compile(
    r"(?:how\s+(?:do|can|to)\s+i\b|how\s+to\b"
    r"|block\s+(?:my\s+|the\s+|a\s+)?(?:card|credit\s+card|debit\s+card)|\bhotlist\w*\b"
    r"|(?:reset|change|forgot|regenerate)\s+(?:my\s+|the\s+)?(?:pin|password|mpin)"
    r"|(?:contact|call|reach)\s+(?:support|customer\s+care|customer\s+service|hdfc)"
    r"|customer\s+(?:care|service)\b"
    r"|(?:file|lodge|register|raise)\s+(?:a\s+)?(?:complaint|dispute)"
    r"|activat\w+\s+(?:my\s+)?(?:card|account)"
    r"|(?:replace|reissue)\s+(?:my\s+)?\w*\s*card|card\s+(?:replacement|reissue)"
    r"|(?:report|my|lost|stolen|misplaced)\s+(?:lost\s+|stolen\s+)?card"
    r"|close\s+(?:my\s+)?(?:account|card|loan)|closure"
    r"|update\s+(?:my\s+|the\s+)?(?:mobile|email|address|kyc|pan|aadhaar)"
    r"|(?:download|get|request)\s+(?:my\s+|the\s+|a\s+)?(?:statement|cheque\s+book)"
    r"|stop\s+(?:my\s+|the\s+|a\s+)?(?:cheque|payment)|cancel\s+(?:cheque|mandate|sip)"
    r"|link\s+aadhaar|apply\s+(?:for|online)|application\s+status"
    r"|set\s+up\s+(?:auto\s+pay|standing\s+instruction)|redeem\s+(?:my\s+)?(?:reward|points)"
    r"|increase\s+(?:my\s+)?(?:credit\s+limit|limit)|upgrade\s+(?:my\s+)?card"
    r"|netbanking\s+(?:login|issue|problem|not\s+working)|login\s+(?:issue|problem|trouble)"
    r"|not\s+working|unable\s+to\s+(?:login|access|use))",
    re.IGNORECASE,
)

def _match_service(text: str, affinity: bool) -> bool:
    return affinity and bool(_SVC_PATTERN.search(text))


# 7. GENERAL_BANKING_QUERY
_GEN_PATTERN = re.compile(
    r"(?:what\s+(?:is|are|was)\s+(?:an?\s+)?"
    r"(?:neft|rtgs|imps|upi|kyc|emi|repo\s+rate|ifsc|micr|cibil|credit\s+score"
    r"|cheque|demand\s+draft|locker|overdraft|fixed\s+deposit|recurring\s+deposit"
    r"|savings\s+account|current\s+account|salary\s+account|credit\s+card|debit\s+card"
    r"|forex|nri|demat|mutual\s+fund|netbanking|internet\s+banking|mobile\s+banking"
    r"|nominee|beneficiary|standing\s+instruction|basel|mclr)"
    r"|how\s+(?:does|do|did)\s+(?:neft|rtgs|imps|upi|emi|kyc|a\s+cheque)\s+work"
    r"|(?:neft|rtgs|imps)\s+transfer"
    r"|banking\s+(?:terms?|concepts?|hours?|holidays?)"
    r"|(?<!hdfc\s)\b(?:upi|neft|rtgs|imps|fastag|netbanking|net\s+banking)\b"
    r"|(?<!hdfc\s)\b(?:mobile|internet)\s+banking\b"
    r"|how\s+(?:long|much\s+time)\s+(?:does|do|take)"
    r"|is\s+(?:my\s+)?(?:money|deposit)\s+(?:safe|insured)"
    r"|what\s+are\s+the\s+(?:benefits|advantages)\s+of\s+"
    r"(?:neft|rtgs|imps|upi|kyc|emi|fixed\s+deposits?|recurring\s+deposits?))",
    re.IGNORECASE,
)

def _match_general_banking(text: str, affinity: bool) -> bool:
    return bool(_GEN_PATTERN.search(text))


# ── Follow-up / product-detail language (Hermes P2 fix) ──────────────────
#
# Bare words like "fees", "features", "benefits", "eligibility" are
# PRODUCT_INFORMATION even without banking keywords.  This fixes the
# multi-turn bug where "What are its fees?" was routed to OUT_OF_SCOPE
# because bare "fees" has no banking-affinity term.
_FOLLOW_UP_DETAIL = re.compile(
    r"\b(?:fees?|charges?|interest\s+rates?|features?|benefits?|"
    r"eligibility|requirements?|details?|documents?\s+(?:required|needed)|"
    r"rewards?|cashback|credit\s+limit|annual\s+fee|joining\s+fee|"
    r"how\s+(?:to\s+apply|much)\b)\b",
    re.IGNORECASE,
)

# 8. PRODUCT_INFORMATION (HDFC-qualified or follow-up product detail)
_PROD_PATTERN = re.compile(
    r"(?:tell\s+me\s+about|\bhdfc\b|\bwhich\s+hdfc\b|what\s+hdfc"
    r"|(?:credit|debit)\s+cards?\b"
    r"|home\s+loans?|personal\s+loans?|car\s+loans?|education\s+loans?"
    r"|business\s+loans?|loan\s+against"
    r"|fixed\s+deposits?|recurring\s+deposits?"
    r"|(?:forex|travel)\s+cards?|travel\s+money"
    r"|(?:savings|salary|current)\s+accounts?"
    r"|insurance\s+(?:plans?|polic(?:y|ies)|products?)"
    r"|mutual\s+funds?|demat\s+accounts?|trading\s+accounts?"
    r"|(?:fees?|charges?)\s+(?:for|of)\b|interest\s+rates?\b"
    r"|eligibility\s+(?:for|criteria|requirements?)"
    r"|(?:features|benefits|details|documents?)\s+(?:of|for|required)\b"
    r"|documents?\s+required"
    r"|available\s+(?:cards?|loans?|products?|plans?)"
    r"|\bcards?\b[^.!?]{0,25}\bavailable\b"
    r"|\bloans?\b[^.!?]{0,25}\bavailable\b"
    r"|\bregalia\b|\bmillennia\b|\bmillenia\b|\binfinia\b|\bdiners\b"
    r"|\bfreedom\s+card\b|\bmoneyback\b"
    r"|processing\s+(?:fee|time)|reward\s+points?|cashback|credit\s+limit"
    r"|loan\s+tenure|nri\s+(?:accounts?|services?|banking)"
    r"|minimum\s+balance|margin\s+money|rate\s+of\s+interest)",
    re.IGNORECASE,
)

def _match_product_info(text: str, affinity: bool) -> bool:
    # Hermes P2 fix: bare product-detail words are always product info.
    if _FOLLOW_UP_DETAIL.search(text):
        return True
    return affinity and bool(_PROD_PATTERN.search(text))


# ── Rule evaluation ──────────────────────────────────────────────────────

_RULE_LAYERS = (
    (_match_unsafe, ChatIntent.UNSAFE_OR_SENSITIVE,
     "Safety-sensitive request pattern detected.", 0.95),
    (_match_account_query, ChatIntent.CUSTOMER_ACCOUNT_QUERY,
     "User requested account-specific information.", 0.90),
    (_match_transaction, ChatIntent.TRANSACTION_QUERY,
     "Transaction or payment history request detected.", 0.90),
    (_match_recommendation, ChatIntent.PERSONALIZED_RECOMMENDATION,
     "Personal suitability or recommendation language detected.", 0.88),
    (_match_comparison, ChatIntent.PRODUCT_COMPARISON,
     "Comparison language detected for banking products.", 0.90),
    (_match_service, ChatIntent.SERVICE_HELP,
     "Service action or how-to help request detected.", 0.88),
    (_match_general_banking, ChatIntent.GENERAL_BANKING_QUERY,
     "General banking concept or process query detected.", 0.85),
    (_match_product_info, ChatIntent.PRODUCT_INFORMATION,
     "User is asking about an HDFC product or product family.", 0.85),
)

REASON_TEMPLATES = frozenset(
    {reason for _, _, reason, _ in _RULE_LAYERS}
) | {
    "Classified by fallback provider.",
    "Banking-related query without a specific intent signal; "
    "defaulting to general banking.",
    "No banking domain affinity detected; query is out of scope.",
    "Product-detail follow-up language detected.",
}


def _apply_rules(normalized: str, affinity: bool) -> Optional[RoutingDecision]:
    for matcher, intent, reason, confidence in _RULE_LAYERS:
        if matcher(normalized, affinity):
            return _decision_for(intent, confidence, reason)
    return None


def _decision_for(intent: ChatIntent, confidence: float, reason: str) -> RoutingDecision:
    safety = ("unsafe_query",) if intent is ChatIntent.UNSAFE_OR_SENSITIVE else ()
    return RoutingDecision(
        intent=intent, confidence=confidence, reason=reason,
        safety_flags=safety, **_INTENT_CAPABILITIES[intent],
    )


# ── IntentRouter ─────────────────────────────────────────────────────────


class IntentRouter:
    """Three-layer intent classifier for HDFC banking queries."""

    def __init__(self, classifier: Optional[IntentClassificationProvider] = None) -> None:
        self._classifier = classifier

    def route(self, message: str) -> RoutingDecision:
        """Classify *message* into a structured routing decision."""
        self._validate_message(message)

        normalized = _normalize(message)
        affinity = _banking_affinity(normalized)

        # Layer 1: deterministic rules.
        decision = _apply_rules(normalized, affinity)
        if decision is not None:
            return decision

        # Layer 2: optional classifier for rule-inconclusive messages.
        if self._classifier is not None:
            try:
                classified = self._classifier.classify(message)
                if isinstance(classified, ChatIntent):
                    return _decision_for(classified, 0.65, "Classified by fallback provider.")
            except Exception:
                pass

        # Layer 3: safe fallback.
        if affinity:
            return _decision_for(
                ChatIntent.GENERAL_BANKING_QUERY, 0.40,
                "Banking-related query without a specific intent signal; "
                "defaulting to general banking.",
            )
        return _decision_for(
            ChatIntent.OUT_OF_SCOPE, 0.50,
            "No banking domain affinity detected; query is out of scope.",
        )

    @staticmethod
    def _validate_message(message: str) -> None:
        if not isinstance(message, str):
            raise ValueError(f"message must be a string, got {type(message).__name__}")
        stripped = message.strip()
        if not stripped:
            raise ValueError("message must not be empty or whitespace-only")
        if len(stripped) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"message exceeds {MAX_MESSAGE_LENGTH} characters (got {len(stripped)})"
            )
