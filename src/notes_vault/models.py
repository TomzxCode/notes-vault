"""Pydantic data models for notes-vault."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SensitivityLevel(BaseModel):
    """Defines a sensitivity level with detection rules and access hierarchy."""

    name: str
    description: str
    query: str  # Regex pattern for hashtag detection
    includes: set[str] = Field(default_factory=set)  # Other levels this includes

    def model_post_init(self, __context: Any) -> None:
        """Ensure includes is a set after validation."""
        if isinstance(self.includes, list):
            self.includes = set(self.includes)


class FileGroup(BaseModel):
    """Defines a group of files with common settings."""

    name: str
    path: str  # Glob pattern
    sensitivity: str  # Default sensitivity for files in this group


class ApiKey(BaseModel):
    """Defines an API key and its access permissions."""

    key_name: str
    key_hash: str  # SHA-256 hash of the secret key used for authentication
    sensitivities: set[str] = Field(default_factory=set)  # Accessible sensitivity levels

    def model_post_init(self, __context: Any) -> None:
        """Ensure sensitivities is a set after validation."""
        if isinstance(self.sensitivities, list):
            self.sensitivities = set(self.sensitivities)


class NoteMetadata(BaseModel):
    """Metadata for an indexed note."""

    uuid: UUID
    file_path: str
    file_group: str
    detected_sensitivities: set[str] = Field(default_factory=set)
    last_modified: datetime
    last_indexed: datetime
    content_hash: str


class Config(BaseModel):
    """Application configuration."""

    defaults: dict[str, str] = Field(default_factory=dict)
    files: dict[str, FileGroup] = Field(default_factory=dict)
    keys: dict[str, ApiKey] = Field(default_factory=dict)
    sensitivities: dict[str, SensitivityLevel] = Field(default_factory=dict)


class AccessLogEntry(BaseModel):
    """Log entry for access control audit trail."""

    timestamp: datetime
    api_key: str
    action: str
    note_uuid: UUID | None = None
    granted: bool
