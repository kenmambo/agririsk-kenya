"""Unit tests for county name standardizer."""

import pytest
from agririsk.ingestion.county_standardizer import (
    normalize_county_name,
    get_canonical_county_info,
)


def test_standard_county_names():
    """Verify standard county names are correctly returned."""
    assert normalize_county_name("Turkana") == "Turkana"
    assert normalize_county_name("Marsabit") == "Marsabit"
    assert normalize_county_name("Garissa") == "Garissa"


def test_case_and_whitespace_insensitivity():
    """Verify casing and surrounding whitespace are normalized."""
    assert normalize_county_name("  turkana  ") == "Turkana"
    assert normalize_county_name("MARSABIT") == "Marsabit"
    assert normalize_county_name("bArInGo") == "Baringo"


def test_alias_and_punctuation_handling():
    """Verify handling of apostrophes, hyphens, and common alternative spellings."""
    assert normalize_county_name("Muranga") == "Murang'a"
    assert normalize_county_name("murang'a") == "Murang'a"
    assert normalize_county_name("Tharaka Nithi") == "Tharaka-Nithi"
    assert normalize_county_name("tharaka-nithi") == "Tharaka-Nithi"
    assert normalize_county_name("Keiyo-Marakwet") == "Elgeyo-Marakwet"
    assert normalize_county_name("Elgeyo Marakwet") == "Elgeyo-Marakwet"
    assert normalize_county_name("Homabay") == "Homa Bay"
    assert normalize_county_name("West-Pokot") == "West Pokot"


def test_code_lookup():
    """Verify lookup using 3-digit county codes."""
    assert normalize_county_name("023") == "Turkana"
    assert normalize_county_name("23") == "Turkana"
    assert normalize_county_name("001") == "Mombasa"


def test_invalid_county_raises_error():
    """Verify ValueError is raised for unrecognized names."""
    with pytest.raises(ValueError, match="Unable to normalize"):
        normalize_county_name("NonExistentCounty")

    with pytest.raises(ValueError):
        normalize_county_name("")


def test_get_canonical_county_info():
    """Verify dictionary metadata retrieval."""
    info = get_canonical_county_info("turkana")
    assert info["code"] == "023"
    assert info["name"] == "Turkana"
    assert info["asal_category"] == "Arid"
