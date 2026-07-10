from dataclasses import dataclass, field, asdict


@dataclass
class Job:
    """One job listing from a search results page."""

    title: str
    company: str
    url: str
    board: str
    id: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JobDetails:
    """Full detail of a single posting."""

    title: str
    company: str
    url: str
    location: str = ""
    date_posted: str = ""
    apply_by: str = ""
    employment_type: str = ""
    description: str = ""
    qualifications: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
