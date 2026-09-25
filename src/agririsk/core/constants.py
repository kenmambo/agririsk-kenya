"""Constants for AgriRisk Kenya, including the 47 official counties and coordinates."""

from typing import Dict, Any, List

# Official 47 Counties of Kenya with code, ASAL status, and approximate centroids (WGS84)
# ASAL Category:
# - Arid: ~85-100% arid land, high pastoralist dependency, extreme drought vulnerability
# - Semi-Arid: ~30-84% arid land, mixed agropastoral
# - Non-ASAL: High to medium agricultural potential (highlands, Lake Victoria basin, central)
KENYA_COUNTIES: List[Dict[str, Any]] = [
    {"code": "001", "name": "Mombasa", "asal_category": "Non-ASAL", "lat": -4.0435, "lon": 39.6682},
    {"code": "002", "name": "Kwale", "asal_category": "Semi-Arid", "lat": -4.1744, "lon": 39.4606},
    {"code": "003", "name": "Kilifi", "asal_category": "Semi-Arid", "lat": -3.5107, "lon": 39.9093},
    {"code": "004", "name": "Tana River", "asal_category": "Arid", "lat": -1.5000, "lon": 39.8000},
    {"code": "005", "name": "Lamu", "asal_category": "Semi-Arid", "lat": -2.2717, "lon": 40.9020},
    {"code": "006", "name": "Taita Taveta", "asal_category": "Semi-Arid", "lat": -3.3161, "lon": 38.4850},
    {"code": "007", "name": "Garissa", "asal_category": "Arid", "lat": -0.4532, "lon": 39.6461},
    {"code": "008", "name": "Wajir", "asal_category": "Arid", "lat": 1.7471, "lon": 40.0573},
    {"code": "009", "name": "Mandera", "asal_category": "Arid", "lat": 3.9373, "lon": 41.8569},
    {"code": "010", "name": "Marsabit", "asal_category": "Arid", "lat": 2.3369, "lon": 37.9904},
    {"code": "011", "name": "Isiolo", "asal_category": "Arid", "lat": 0.3546, "lon": 37.5822},
    {"code": "012", "name": "Meru", "asal_category": "Semi-Arid", "lat": 0.0463, "lon": 37.6559},
    {"code": "013", "name": "Tharaka-Nithi", "asal_category": "Semi-Arid", "lat": -0.2974, "lon": 37.8686},
    {"code": "014", "name": "Embu", "asal_category": "Semi-Arid", "lat": -0.5390, "lon": 37.4586},
    {"code": "015", "name": "Kitui", "asal_category": "Arid", "lat": -1.3746, "lon": 38.0106},
    {"code": "016", "name": "Machakos", "asal_category": "Semi-Arid", "lat": -1.5177, "lon": 37.2634},
    {"code": "017", "name": "Makueni", "asal_category": "Semi-Arid", "lat": -1.8037, "lon": 37.6203},
    {"code": "018", "name": "Nyandarua", "asal_category": "Non-ASAL", "lat": -0.1804, "lon": 36.5230},
    {"code": "019", "name": "Nyeri", "asal_category": "Semi-Arid", "lat": -0.4201, "lon": 36.9476},
    {"code": "020", "name": "Kirinyaga", "asal_category": "Non-ASAL", "lat": -0.5000, "lon": 37.2800},
    {"code": "021", "name": "Murang'a", "asal_category": "Non-ASAL", "lat": -0.7167, "lon": 37.1500},
    {"code": "022", "name": "Kiambu", "asal_category": "Non-ASAL", "lat": -1.1714, "lon": 36.8356},
    {"code": "023", "name": "Turkana", "asal_category": "Arid", "lat": 3.1167, "lon": 35.6000},
    {"code": "024", "name": "West Pokot", "asal_category": "Semi-Arid", "lat": 1.4889, "lon": 35.1167},
    {"code": "025", "name": "Samburu", "asal_category": "Arid", "lat": 1.2500, "lon": 36.8000},
    {"code": "026", "name": "Trans Nzoia", "asal_category": "Non-ASAL", "lat": 1.0560, "lon": 34.9500},
    {"code": "027", "name": "Uasin Gishu", "asal_category": "Non-ASAL", "lat": 0.5143, "lon": 35.2698},
    {"code": "028", "name": "Elgeyo-Marakwet", "asal_category": "Semi-Arid", "lat": 0.8000, "lon": 35.5000},
    {"code": "029", "name": "Nandi", "asal_category": "Non-ASAL", "lat": 0.1833, "lon": 35.1000},
    {"code": "030", "name": "Baringo", "asal_category": "Arid", "lat": 0.4833, "lon": 35.9667},
    {"code": "031", "name": "Laikipia", "asal_category": "Semi-Arid", "lat": 0.3667, "lon": 36.7833},
    {"code": "032", "name": "Nakuru", "asal_category": "Semi-Arid", "lat": -0.3031, "lon": 36.0800},
    {"code": "033", "name": "Narok", "asal_category": "Semi-Arid", "lat": -1.0833, "lon": 35.8667},
    {"code": "034", "name": "Kajiado", "asal_category": "Semi-Arid", "lat": -2.0000, "lon": 36.8667},
    {"code": "035", "name": "Kericho", "asal_category": "Non-ASAL", "lat": -0.3689, "lon": 35.2863},
    {"code": "036", "name": "Bomet", "asal_category": "Non-ASAL", "lat": -0.7813, "lon": 35.3416},
    {"code": "037", "name": "Kakamega", "asal_category": "Non-ASAL", "lat": 0.2827, "lon": 34.7519},
    {"code": "038", "name": "Vihiga", "asal_category": "Non-ASAL", "lat": 0.0833, "lon": 34.7167},
    {"code": "039", "name": "Bungoma", "asal_category": "Non-ASAL", "lat": 0.5695, "lon": 34.5584},
    {"code": "040", "name": "Busia", "asal_category": "Non-ASAL", "lat": 0.4608, "lon": 34.1115},
    {"code": "041", "name": "Siaya", "asal_category": "Non-ASAL", "lat": 0.0607, "lon": 34.2882},
    {"code": "042", "name": "Kisumu", "asal_category": "Non-ASAL", "lat": -0.0917, "lon": 34.7680},
    {"code": "043", "name": "Homa Bay", "asal_category": "Semi-Arid", "lat": -0.5273, "lon": 34.4571},
    {"code": "044", "name": "Migori", "asal_category": "Semi-Arid", "lat": -1.0634, "lon": 34.4731},
    {"code": "045", "name": "Kisii", "asal_category": "Non-ASAL", "lat": -0.6817, "lon": 34.7667},
    {"code": "046", "name": "Nyamira", "asal_category": "Non-ASAL", "lat": -0.5633, "lon": 34.9358},
    {"code": "047", "name": "Nairobi", "asal_category": "Non-ASAL", "lat": -1.2921, "lon": 36.8219}
]

COUNTY_CODE_MAP = {c["code"]: c for c in KENYA_COUNTIES}
COUNTY_NAME_MAP = {c["name"].lower(): c for c in KENYA_COUNTIES}

# IPC Acute Food Insecurity Phase Reference
# Phase 1: Minimal
# Phase 2: Stressed
# Phase 3: Crisis
# Phase 4: Emergency
# Phase 5: Catastrophe / Famine
IPC_PHASES = {
    1: {"name": "Phase 1 - Minimal", "color": "#2ca02c", "risk_range": (0, 20)},
    2: {"name": "Phase 2 - Stressed", "color": "#ffbb78", "risk_range": (20, 45)},
    3: {"name": "Phase 3 - Crisis", "color": "#ff7f0e", "risk_range": (45, 70)},
    4: {"name": "Phase 4 - Emergency", "color": "#d62728", "risk_range": (70, 90)},
    5: {"name": "Phase 5 - Famine", "color": "#7f0000", "risk_range": (90, 100)},
}

# Seasonal cycles in Kenya:
# Long Rains: March to May (MAM)
# Short Rains: October to December (OND)
RAIN_SEASONS = {
    "MAM": [3, 4, 5],
    "OND": [10, 11, 12]
}
