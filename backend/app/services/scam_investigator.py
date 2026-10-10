import ipaddress
import logging
import re
from typing import List, Optional, Set
from urllib.parse import urlsplit

from app.schemas.content_analysis import ClaimAnalysis, ContentAnalysis, EntityAnalysis, SuspiciousSignal, UrlTarget
from app.schemas.scam_assessment import (
    IndicatorCategory,
    ScamAssessmentResult,
    ScamAssessmentStatus,
    ScamIndicator,
    SignalProvenance,
)
from app.schemas.investigation import RiskLevel

logger = logging.getLogger("truthlens.scam_investigator")

# Known URL shortener hostnames
KNOWN_SHORTENERS: Set[str] = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "is.gd",
    "buff.ly",
    "ow.ly",
    "goo.gl",
    "cutt.ly",
    "rb.gy",
    "shorte.st",
    "tiny.cc",
    "v.gd",
    "qr.net",
    "shorturl.at",
    "trib.al",
    "lnkd.in",
}

# Common high-value targets frequently spoofed in phishing/smishing
KNOWN_TARGET_BRANDS: Set[str] = {
    "sbi",
    "statebank",
    "hdfc",
    "icici",
    "pnb",
    "rbi",
    "reservebank",
    "paytm",
    "amazon",
    "flipkart",
    "google",
    "apple",
    "microsoft",
    "netflix",
    "uidai",
    "aadhaar",
    "incometax",
    "cybercrime",
    "indiapost",
}

# Deceptive keywords often embedded in deceptive domains or paths
DECEPTIVE_PATH_KEYWORDS: Set[str] = {
    "kyc",
    "kyc-update",
    "otp",
    "verify",
    "verification",
    "unblock",
    "account-update",
    "claim-reward",
    "claim-prize",
    "secure-login",
    "banking-login",
    "pan-link",
}


def _is_ip_address(host: str) -> bool:
    """Safely check if host is a raw IPv4 or IPv6 address without crashing."""
    clean_host = host.split(":")[0].strip("[]")
    try:
        ipaddress.ip_address(clean_host)
        return True
    except (ValueError, AttributeError):
        return False


def analyze_url_heuristics(
    url_target: UrlTarget,
    detected_entities: Optional[List[EntityAnalysis]] = None,
) -> List[ScamIndicator]:
    """Execute deterministic URL heuristics with safe parsing.
    
    URL heuristics are structural risk indicators, NOT proof of domain reputation,
    DNS ownership, or confirmed malice.
    """
    indicators: List[ScamIndicator] = []
    raw_url = url_target.url.strip()
    if not raw_url:
        return indicators

    # Safe parsing: handle missing scheme, ports, unicode
    try:
        if not (raw_url.startswith("http://") or raw_url.startswith("https://") or raw_url.startswith("ftp://")):
            parse_target = "http://" + raw_url
        else:
            parse_target = raw_url
        parsed = urlsplit(parse_target)
    except Exception as e:
        logger.debug(f"Failed to parse URL '{raw_url}': {e}")
        return indicators

    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    full_url_lower = raw_url.lower()

    if not host:
        return indicators

    # 1. Known URL Shortener
    if host in KNOWN_SHORTENERS or any(host.endswith("." + s) for s in KNOWN_SHORTENERS):
        indicators.append(
            ScamIndicator(
                id=f"ind-url-shortener-{abs(hash(raw_url)) % 10000}",
                category=IndicatorCategory.URL_INDICATOR,
                name="URL Shortener Detected",
                severity_weight=12,
                provenance=SignalProvenance.DETERMINISTIC_URL_CHECK,
                evidence_excerpt=raw_url,
                associated_claim_ids=[],
                explanation=(
                    f"Destination URL uses shortener service '{host}'. Shortened links conceal destination "
                    "domains and are frequently utilized in phishing to bypass domain scrutiny."
                ),
                confidence=1.0,
                is_directly_observed=True,
            )
        )

    # 2. Raw IP-address host
    if _is_ip_address(host):
        indicators.append(
            ScamIndicator(
                id=f"ind-url-ip-{abs(hash(raw_url)) % 10000}",
                category=IndicatorCategory.URL_INDICATOR,
                name="Raw IP Address Host",
                severity_weight=20,
                provenance=SignalProvenance.DETERMINISTIC_URL_CHECK,
                evidence_excerpt=raw_url,
                associated_claim_ids=[],
                explanation=(
                    f"URL host '{host}' is a raw IP address rather than a registered domain name. "
                    "Legitimate commercial institutions virtually never direct end users to bare IP hosts."
                ),
                confidence=1.0,
                is_directly_observed=True,
            )
        )

    # 3. Punycode / IDN Domain (xn--)
    if "xn--" in host:
        indicators.append(
            ScamIndicator(
                id=f"ind-url-punycode-{abs(hash(raw_url)) % 10000}",
                category=IndicatorCategory.URL_INDICATOR,
                name="Internationalized Domain (Punycode)",
                severity_weight=15,
                provenance=SignalProvenance.DETERMINISTIC_URL_CHECK,
                evidence_excerpt=raw_url,
                associated_claim_ids=[],
                explanation=(
                    f"Domain '{host}' uses Punycode encoding (xn--). Punycode homograph techniques "
                    "can mimic authentic brand spellings with look-alike characters from other scripts."
                ),
                confidence=1.0,
                is_directly_observed=True,
            )
        )

    # 4. Brand-in-subdomain or Mismatched Domain
    # Check if a known brand or an extracted entity name appears as a subdomain/slug on an unrelated root domain
    entity_names = set()
    if detected_entities:
        for ent in detected_entities:
            clean_name = re.sub(r"[^a-zA-Z0-9]", "", ent.name.lower())
            if len(clean_name) >= 3:
                entity_names.add(clean_name)
    all_targets = KNOWN_TARGET_BRANDS.union(entity_names)

    host_parts = host.split(".")
    for brand in all_targets:
        # If brand is in host, but host is not the authentic domain
        if brand in host:
            # Check if brand is in subdomain or embedded in hyphenated name (e.g. sbi-support.xyz)
            # but domain is not an official domain (e.g. not sbi.co.in or amazon.com)
            is_standalone_domain = (len(host_parts) >= 2 and host_parts[-2] == brand)
            if not is_standalone_domain:
                indicators.append(
                    ScamIndicator(
                        id=f"ind-url-brand-mismatch-{abs(hash(raw_url)) % 10000}",
                        category=IndicatorCategory.IMPERSONATION,
                        name=f"Brand String in Mismatched Host: '{brand.upper()}'",
                        severity_weight=18,
                        provenance=SignalProvenance.DETERMINISTIC_URL_CHECK,
                        evidence_excerpt=raw_url,
                        associated_claim_ids=[],
                        explanation=(
                            f"The brand identifier '{brand.upper()}' appears inside host '{host}', "
                            "which does not match the official organizational root domain structure. "
                            "This pattern is characteristic of deceptive brand lures."
                        ),
                        confidence=0.90,
                        is_directly_observed=True,
                    )
                )
                break

    # 5. Deceptive keywords in path or host
    for keyword in DECEPTIVE_PATH_KEYWORDS:
        if keyword in full_url_lower:
            indicators.append(
                ScamIndicator(
                    id=f"ind-url-deceptive-{abs(hash(keyword + raw_url)) % 10000}",
                    category=IndicatorCategory.URL_INDICATOR,
                    name=f"Deceptive Action Pattern in URL: '{keyword}'",
                    severity_weight=15,
                    provenance=SignalProvenance.DETERMINISTIC_URL_CHECK,
                    evidence_excerpt=raw_url,
                    associated_claim_ids=[],
                    explanation=(
                        f"URL path or hostname contains high-risk action pattern '{keyword}'. "
                        "Urgent credential or verification keywords in external URLs correlate strongly with phishing vectors."
                    ),
                    confidence=0.85,
                    is_directly_observed=True,
                )
            )
            break

    return indicators


def _map_signal_to_indicator(
    sig: SuspiciousSignal,
    idx: int,
    original_text: str,
    claims: List[ClaimAnalysis],
) -> ScamIndicator:
    """Map a Content Intelligence suspicious signal into a normalized ScamIndicator."""
    stype = sig.type.lower()
    desc = sig.description
    evidence = sig.evidence.strip() if sig.evidence else ""

    # Check if evidence excerpt is directly observed verbatim in original text
    is_directly_observed = bool(evidence and evidence.lower() in original_text.lower())

    # Find associated claim IDs by matching keywords or statements
    associated_claim_ids = []
    for cl in claims:
        if any(w in cl.statement.lower() for w in [stype, "payment", "fee", "otp", "password", "bank", "prize", "urgent"]):
            associated_claim_ids.append(cl.id)

    # Categorize and assign base weight
    if any(k in stype for k in ["advance_payment", "payment", "fee", "deposit", "transfer"]):
        category = IndicatorCategory.FINANCIAL_REQUEST
        name = "Advance Fee or Payment Demand"
        weight = 25 if "advance" in stype or "reward" in desc.lower() else 22
        explanation = f"Direct or indirect financial payment requested: {desc}."
    elif any(k in stype for k in ["credential", "password", "pin", "otp", "banking", "sensitive"]):
        category = IndicatorCategory.CREDENTIAL_THEFT
        name = "Credential or Sensitive Data Solicitation"
        weight = 30 if any(k in stype or k in desc.lower() for k in ["password", "pin", "otp"]) else 25
        explanation = f"Solicitation of secret authentication credentials or account disclosures: {desc}."
    elif any(k in stype for k in ["urgency", "deadline", "fear", "threat", "coercion"]):
        category = IndicatorCategory.MANIPULATION_PERSUASION
        name = "Artificial Urgency or Coercive Threat"
        weight = 12 if "threat" in stype or "fear" in stype else 10
        explanation = f"Psychological manipulation utilizing manufactured urgency or pressure: {desc}."
    elif any(k in stype for k in ["reward_lure", "prize", "lottery", "investment", "guarantee"]):
        category = IndicatorCategory.MANIPULATION_PERSUASION
        name = "Unrealistic Reward or Investment Lure"
        weight = 18
        explanation = f"Unrealistic incentive or guaranteed financial return lure: {desc}."
    elif any(k in stype for k in ["impersonation", "authority", "brand", "official"]):
        category = IndicatorCategory.IMPERSONATION
        name = "Institutional or Authority Impersonation"
        weight = 18
        explanation = f"Claimed institutional or regulatory authority without verifiable affiliation: {desc}."
    else:
        category = IndicatorCategory.MANIPULATION_PERSUASION
        name = stype.replace("_", " ").title()
        weight = 10
        explanation = f"Behavioral deception indicator detected: {desc}."

    provenance = (
        SignalProvenance.ORIGINAL_MESSAGE
        if is_directly_observed
        else SignalProvenance.GEMINI_EXTRACTED_SIGNAL
    )

    return ScamIndicator(
        id=f"ind-sig-{idx+1}-{abs(hash(stype)) % 1000}",
        category=category,
        name=name,
        severity_weight=weight,
        provenance=provenance,
        evidence_excerpt=evidence if evidence else None,
        associated_claim_ids=associated_claim_ids,
        explanation=explanation,
        confidence=round(sig.confidence, 2),
        is_directly_observed=is_directly_observed,
    )


class ScamInvestigator:
    """Service to evaluate behavioral deception indicators and structural URL heuristics.
    
    Normalizes candidate signals from Content Intelligence, evaluates deterministic URL heuristics,
    and constructs traceable ScamIndicator records.
    """

    def investigate(
        self,
        original_text: str,
        content_analysis: ContentAnalysis,
    ) -> List[ScamIndicator]:
        """Produce normalized list of indicators with traceable basis and provenance."""
        indicators: List[ScamIndicator] = []

        # 1. Map candidate suspicious signals extracted during Content Intelligence
        for idx, sig in enumerate(content_analysis.suspicious_signals):
            indicator = _map_signal_to_indicator(
                sig=sig,
                idx=idx,
                original_text=original_text,
                claims=content_analysis.claims,
            )
            indicators.append(indicator)

        # 2. Execute deterministic URL heuristics
        for url_target in content_analysis.urls:
            url_indicators = analyze_url_heuristics(
                url_target=url_target,
                detected_entities=content_analysis.entities,
            )
            indicators.extend(url_indicators)

        return indicators
