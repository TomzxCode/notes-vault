"""Pydantic data models for notes-vault."""

from pydantic import BaseModel, Field


class FileGroup(BaseModel):
    """Defines a group of files to be synced."""

    name: str
    path: str


class Consumer(BaseModel):
    """Defines a consumer and its file matching rules."""

    name: str
    target: str
    include_queries: list[str] = Field(default_factory=list)
    exclude_queries: list[str] = Field(default_factory=list)
    rename: bool = False


class Config(BaseModel):
    """Application configuration."""

    files: dict[str, FileGroup] = Field(default_factory=dict)
    consumers: dict[str, Consumer] = Field(default_factory=dict)
