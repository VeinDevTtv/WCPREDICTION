"""Team-name normalization shared across data, training, and simulation."""

TEAM_ALIASES = {
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Cabo Verde": "Cape Verde",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
    "Cote d'Ivoire": "Ivory Coast",
    "Côte d'Ivoire": "Ivory Coast",
    "Curaçao": "Curacao",
    "Czech Republic": "Czech Republic",
    "Czechia": "Czech Republic",
    "IR Iran": "Iran",
    "Korea Republic": "South Korea",
    "Türkiye": "Turkey",
    "Turkey": "Turkey",
    "USA": "United States",
    "United States of America": "United States",
}


def canonical_team(name: str) -> str:
    """Return the canonical team name used by the historical results dataset."""
    clean = " ".join(str(name).strip().split())
    return TEAM_ALIASES.get(clean, clean)
