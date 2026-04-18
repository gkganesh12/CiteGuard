"""CourtListener API response schemas."""

from pydantic import BaseModel


class OpinionResult(BaseModel):
    """Parsed result from CourtListener opinion lookup."""

    id: int
    case_name: str
    court: str
    date_filed: str | None = None
    absolute_url: str | None = None
    plain_text: str | None = None
    html: str | None = None

    @property
    def full_url(self) -> str:
        base = "https://www.courtlistener.com"
        return f"{base}{self.absolute_url}" if self.absolute_url else base


class CitationLookupResult(BaseModel):
    """Result of resolving a citation against CourtListener."""

    found: bool
    opinion: OpinionResult | None = None
    error: str | None = None


class NegativeTreatment(BaseModel):
    """Negative treatment information from citation graph."""

    treatment_type: str  # overruled, abrogated, superseded, etc.
    citing_case: str
    citing_case_url: str | None = None
    date: str | None = None
