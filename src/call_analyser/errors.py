"""Typed failures exposed by the pipeline."""


class PipelineError(Exception):
    """Base class for expected pipeline failures."""


class AudioValidationError(PipelineError):
    """Audio input is unsupported or violates configured limits."""


class TranscriptionError(PipelineError):
    """Transcription could not be completed."""


class LLMBlockedError(PipelineError):
    """A provider block or refusal prevented completion."""


class StructuredOutputError(PipelineError):
    """A model response failed structured-output validation."""


class RubricError(PipelineError):
    """A rubric cannot be loaded or is invalid."""


class PlaybookExtractionError(PipelineError):
    """A playbook PDF cannot be extracted safely."""


class PlaybookNotIndexedError(PipelineError):
    """A required persistent playbook index does not exist."""


class PlaybookIndexMismatchError(PipelineError):
    """An existing index does not match the current configuration."""
