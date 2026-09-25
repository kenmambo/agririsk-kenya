"""County name standardisation and normalization utility for Kenya."""

import re
import unicodedata
from typing import Dict, Optional, Tuple
from agririsk.core.constants import KENYA_COUNTIES, COUNTY_NAME_MAP, COUNTY_CODE_MAP

# Extended alias mapping to capture common spelling variants, punctuation differences,
# and historical/alternative designations in Kenyan administrative records.
COUNTY_ALIASES: Dict[str, str] = {
    "muranga": "Murang'a",
    "murang'a": "Murang'a",
    "tharaka nithi": "Tharaka-Nithi",
    "tharaka-nithi": "Tharaka-Nithi",
    "tharaka": "Tharaka-Nithi",
    "elgeyo marakwet": "Elgeyo-Marakwet",
    "elgeyo-marakwet": "Elgeyo-Marakwet",
    "keiyo marakwet": "Elgeyo-Marakwet",
    "keiyo-marakwet": "Elgeyo-Marakwet",
    "taita taveta": "Taita Taveta",
    "taita/taveta": "Taita Taveta",
    "taita-taveta": "Taita Taveta",
    "trans nzoia": "Trans Nzoia",
    "trans-nzoia": "Trans Nzoia",
    "uasin gishu": "Uasin Gishu",
    "uasin-gishu": "Uasin Gishu",
    "homa bay": "Homa Bay",
    "homabay": "Homa Bay",
    "west pokot": "West Pokot",
    "west-pokot": "West Pokot",
    "pokot": "West Pokot",
}


def clean_string(val: str) -> str:
    """Normalize string by removing accents, extra whitespace, and standardizing characters."""
    if not isinstance(val, str):
        return ""
    normalized = unicodedata.normalize("NFKD", val)
    cleaned = "".join(c for c in normalized if not unicodedata.combining(c))
    cleaned = cleaned.strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def normalize_county_name(raw_name: str) -> str:
    """Normalize an arbitrary input county name into its official canonical Kenya name.

    Args:
        raw_name: Raw input string representing a county.

    Returns:
        Official canonical county name (e.g. 'Turkana', 'Elgeyo-Marakwet', "Murang'a").

    Raises:
        ValueError: If the raw name cannot be mapped to any of Kenya's 47 counties.
    """
    if not raw_name or not isinstance(raw_name, str):
        raise ValueError(f"Invalid county name input: {raw_name}")

    cleaned = clean_string(raw_name)

    # 1. Direct match in alias map
    if cleaned in COUNTY_ALIASES:
        return COUNTY_ALIASES[cleaned]

    # 2. Check canonical lowercase map
    if cleaned in COUNTY_NAME_MAP:
        return COUNTY_NAME_MAP[cleaned]["name"]

    # 3. Strip internal hyphens/slashes and try matching
    stripped = re.sub(r"[-_/']", " ", cleaned)
    stripped = re.sub(r"\s+", " ", stripped).strip()

    if stripped in COUNTY_ALIASES:
        return COUNTY_ALIASES[stripped]

    for key, c in COUNTY_NAME_MAP.items():
        key_stripped = re.sub(r"[-_/']", " ", key).strip()
        if stripped == key_stripped:
            return c["name"]

    # 4. Check if raw_name is a 3-digit code
    code_candidate = cleaned.zfill(3)
    if code_candidate in COUNTY_CODE_MAP:
        return COUNTY_CODE_MAP[code_candidate]["name"]

    raise ValueError(f"Unable to normalize '{raw_name}' to any recognized Kenya county.")


def get_canonical_county_info(raw_name_or_code: str) -> Dict[str, str]:
    """Retrieve full canonical metadata for a county (code, name, asal_category).

    Args:
        raw_name_or_code: Raw county name or 3-digit code.

    Returns:
        Dictionary containing 'code', 'name', and 'asal_category'.
    """
    canonical_name = normalize_county_name(raw_name_or_code)
    return COUNTY_NAME_MAP[canonical_name.lower()]
