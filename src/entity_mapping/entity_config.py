# src/entity_mapping/entity_config.py

from typing import Dict, Tuple, List

AU_ENTITY_SEVERITY_MAP: Dict[str, str] = {
    "AU_TFN": "critical",
    "AU_MEDICARE": "critical",
    "AU_PASSPORT": "critical",
    "AU_CENTRELINK_CRN": "critical",

    "AU_DRIVER_LICENSE": "high",
    "AU_ABN": "high",
    "AU_ACN": "high",
    "AU_BANK_ACCOUNT": "high",
    "AU_BSB": "high",
    "CREDIT_CARD": "high",
    "IBAN_CODE": "high",
    "AU_ACCOUNT_NUMBER": "high",

    "PERSON": "medium",
    "PERSON_WITH_TITLE": "medium",
    "PERSON_AFTER_GREETING": "medium",
    "REPEATED_NAME": "medium",
    "EMAIL_ADDRESS": "medium",
    "AU_PHONE_NUMBER": "medium",
    "PHONE_NUMBER": "medium",
    "DATE_TIME": "medium",
    "AU_ADDRESS": "medium",
    "ORGANIZATION": "medium",
    "IP_ADDRESS": "medium",
    "URL": "medium",

    "AU_STATE": "low",
    "AU_POSTCODE": "low",
    "NAME_TITLE": "low",
    "LOCATION": "low",
    "CITY": "low",
}


AU_ENTITY_COLOR_MAP: Dict[str, Tuple[float, float, float]] = {
    "critical": (0.90, 0.00, 0.00),    # bright red
    "high": (0.85, 0.10, 0.10),        # dark red
    "medium": (1.00, 0.55, 0.00),      # orange
    "low": (0.10, 0.40, 0.85),         # blue
    "_default": (0.00, 0.00, 0.00),    # black
}


ALL_AU_ENTITY_TYPES: List[str] = [
    "AU_TFN",
    "AU_MEDICARE",
    "AU_PASSPORT",
    "AU_CENTRELINK_CRN",
    "AU_DRIVER_LICENSE",

    "AU_ABN",
    "AU_ACN",
    "AU_BANK_ACCOUNT",
    "AU_BSB",

    "AU_PHONE_NUMBER",

    "AU_STATE",
    "AU_POSTCODE",

    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "DATE_TIME",
    "LOCATION",
    "ORGANIZATION",
]


AU_ENTITY_GROUPS: Dict[str, List[str]] = {
    "financial": [
        "AU_ABN",
        "AU_ACN",
        "AU_BANK_ACCOUNT",
        "AU_BSB",
        "CREDIT_CARD",
        "IBAN_CODE",
    ],
    "government_id": [
        "AU_TFN",
        "AU_MEDICARE",
        "AU_PASSPORT",
        "AU_DRIVER_LICENSE",
        "AU_CENTRELINK_CRN",
    ],
    "personal": [
        "PERSON",
        "PERSON_WITH_TITLE",
        "PERSON_AFTER_GREETING",
        "REPEATED_NAME",
        "EMAIL_ADDRESS",
        "AU_PHONE_NUMBER",
        "PHONE_NUMBER",
        "DATE_TIME",
    ],
    "geographic": [
        "AU_STATE",
        "AU_POSTCODE",
        "LOCATION",
        "CITY",
        "AU_ADDRESS",
    ],
    "all_au_specific": [
        "AU_TFN",
        "AU_MEDICARE",
        "AU_PASSPORT",
        "AU_CENTRELINK_CRN",
        "AU_DRIVER_LICENSE",
        "AU_ABN",
        "AU_ACN",
        "AU_BANK_ACCOUNT",
        "AU_BSB",
        "AU_PHONE_NUMBER",
        "AU_STATE",
        "AU_POSTCODE",
    ],
    "all_au": ALL_AU_ENTITY_TYPES,
}


def get_entity_severity(entity_type: str) -> str:
    return AU_ENTITY_SEVERITY_MAP.get(entity_type, "medium")


def get_entity_color(entity_type: str) -> Tuple[float, float, float]:
    severity = get_entity_severity(entity_type)
    return AU_ENTITY_COLOR_MAP.get(severity, AU_ENTITY_COLOR_MAP["_default"])


def get_entities_by_group(group_name: str) -> List[str]:
    return AU_ENTITY_GROUPS.get(group_name, [])
