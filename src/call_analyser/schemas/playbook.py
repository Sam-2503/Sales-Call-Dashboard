"""Persistent-playbook contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class PlaybookChunk(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    embedding_text: str = Field(min_length=1)
    book_slug: str = Field(min_length=1)
    chapter: str = Field(min_length=1)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    ordinal: int = Field(ge=0)
    token_estimate: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered_pages(self) -> PlaybookChunk:
        if self.page_start > self.page_end:
            raise ValueError("page_start must not exceed page_end")
        return self


class PlaybookPassage(BaseModel):
    chunk: PlaybookChunk
    score: float = Field(ge=0, le=1)


class PlaybookChapter(BaseModel):
    title: str = Field(min_length=1)
    start_page: int = Field(ge=1)
    end_page: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered_pages(self) -> PlaybookChapter:
        if self.start_page > self.end_page:
            raise ValueError("start_page must not exceed end_page")
        return self


class PlaybookRef(BaseModel):
    passage_id: str = Field(min_length=1)
    book_title: str = Field(min_length=1)
    chapter: str = Field(min_length=1)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    excerpt: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_reference(self) -> PlaybookRef:
        if self.page_start > self.page_end:
            raise ValueError("page_start must not exceed page_end")
        if len(self.excerpt.split()) > 25:
            raise ValueError("excerpt must be at most MAX_EXCERPT_WORDS (25) words")
        return self
