"""Canonical county reference dataset, geographic aliases, and spatial mapping audit."""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from agririsk.core.constants import KENYA_COUNTIES
from agririsk.core.logging import logger

# Regional groupings for Kenya's 47 counties
KENYA_REGIONS: Dict[str, List[str]] = {
    "Coast": ["Mombasa", "Kwale", "Kilifi", "Tana River", "Lamu", "Taita Taveta"],
    "North Eastern": ["Garissa", "Wajir", "Mandera"],
    "Eastern": ["Marsabit", "Isiolo", "Meru", "Tharaka-Nithi", "Embu", "Kitui", "Machakos", "Makueni"],
    "Central": ["Nyandarua", "Nyeri", "Kirinyaga", "Murang'a", "Kiambu"],
    "Rift Valley": [
        "Turkana", "West Pokot", "Samburu", "Trans Nzoia", "Uasin Gishu", "Elgeyo-Marakwet",
        "Nandi", "Baringo", "Laikipia", "Nakuru", "Narok", "Kajiado", "Kericho", "Bomet"
    ],
    "Western": ["Kakamega", "Vihiga", "Bungoma", "Busia"],
    "Nyanza": ["Siaya", "Kisumu", "Homa Bay", "Migori", "Kisii", "Nyamira"],
    "Nairobi": ["Nairobi"]
}

# Comprehensive alias mapping dictionary
CANONICAL_ALIASES: Dict[str, List[str]] = {
    "Elgeyo-Marakwet": ["elgeyo marakwet", "keiyo-marakwet", "keiyo marakwet", "marakwet", "e. marakwet", "elgeyo/marakwet"],
    "Tharaka-Nithi": ["tharaka nithi", "tharaka", "tharaka-nithi county", "tharaka/nithi"],
    "Murang'a": ["muranga", "murang'a county", "muranga county"],
    "Taita Taveta": ["taita-taveta", "taita taveta", "taita/taveta"],
    "Tana River": ["tana-river", "tana river", "tanariver"],
    "Trans Nzoia": ["trans-nzoia", "trans nzoia", "transnzoia"],
    "Uasin Gishu": ["uasin-gishu", "uasin gishu", "uasingishu"],
    "West Pokot": ["west-pokot", "west pokot", "pokot"],
    "Homa Bay": ["homa-bay", "homa bay", "homabay"],
}


class CountyReferenceRegistry:
    """Master reference authority for Kenya's 47 counties and geographic harmonization."""

    _master_table: Optional[pd.DataFrame] = None

    @classmethod
    def get_reference_table(cls) -> pd.DataFrame:
        """Return the canonical master DataFrame containing all 47 counties."""
        if cls._master_table is not None:
            return cls._master_table

        # Invert region map
        county_to_region = {}
        for region, counties in KENYA_REGIONS.items():
            for c in counties:
                county_to_region[c] = region

        records = []
        for c in KENYA_COUNTIES:
            name = c["name"]
            aliases = CANONICAL_ALIASES.get(name, [])
            records.append({
                "county_id": c["code"],
                "county_name": name,
                "canonical_name": name,
                "alternate_names": aliases,
                "centroid_lat": c["lat"],
                "centroid_lon": c["lon"],
                "asal_category": c["asal_category"],
                "region": county_to_region.get(name, "Unknown"),
            })

        cls._master_table = pd.DataFrame(records)
        return cls._master_table

    @classmethod
    def match_county(cls, input_name: str) -> Tuple[Optional[str], str]:
        """Resolve any raw or informal county string to its canonical official name.

        Args:
            input_name: Raw county name from source feed.

        Returns:
            Tuple of (canonical_name: Optional[str], match_type: 'exact'|'alias'|'unmatched').
        """
        if not input_name or not isinstance(input_name, str):
            return None, "unmatched"

        cleaned = input_name.strip()
        cleaned_lower = cleaned.lower()

        ref_df = cls.get_reference_table()

        # 1. Exact case-insensitive match
        for name in ref_df["canonical_name"]:
            if name.lower() == cleaned_lower:
                return name, "exact"

        # 2. Alias match
        for _, row in ref_df.iterrows():
            c_name = row["canonical_name"]
            for alias in row["alternate_names"]:
                if alias.lower() == cleaned_lower or alias.lower().replace("-", " ") == cleaned_lower.replace("-", " "):
                    return c_name, "alias"

        # 3. Stripped 'county' suffix match
        if "county" in cleaned_lower:
            stripped = cleaned_lower.replace("county", "").strip()
            for name in ref_df["canonical_name"]:
                if name.lower() == stripped:
                    return name, "alias"

        logger.warning("Unmatched county name detected: '%s'", input_name)
        return None, "unmatched"

    @classmethod
    def canonicalize(cls, input_name: str) -> Optional[str]:
        """Convenience method returning just canonical name or None."""
        name, _ = cls.match_county(input_name)
        return name

    @classmethod
    def all_counties(cls) -> List[str]:
        """Convenience method returning list of all 47 canonical county names."""
        return list(cls.get_reference_table()["canonical_name"])

    @classmethod
    def audit_geographic_coverage(cls, counties_list: List[str]) -> Dict[str, Any]:
        """Audit a list of counties against canonical geography and identify mismatches.

        Args:
            counties_list: Sequence of county names from an incoming dataset.

        Returns:
            Dictionary detailing matched, unmatched, and coverage statistics.
        """
        matched = []
        unmatched = []
        aliases_used = []

        for c in set(counties_list):
            canonical, match_type = cls.match_county(c)
            if match_type == "exact":
                matched.append(canonical)
            elif match_type == "alias":
                matched.append(canonical)
                aliases_used.append({"raw": c, "canonical": canonical})
            else:
                unmatched.append(c)

        total_official = len(cls.get_reference_table())
        matched_unique = list(set(matched))

        is_complete = len(unmatched) == 0
        if not is_complete:
            logger.warning("Geographic audit found %d unmatched entities: %s", len(unmatched), unmatched)

        return {
            "is_valid": is_complete,
            "total_official_counties": total_official,
            "matched_count": len(matched_unique),
            "matched_counties": sorted(matched_unique),
            "unmatched_count": len(unmatched),
            "unmatched_entities": sorted(unmatched),
            "aliases_resolved": aliases_used,
            "coverage_pct": round(len(matched_unique) / total_official * 100, 1)
        }
