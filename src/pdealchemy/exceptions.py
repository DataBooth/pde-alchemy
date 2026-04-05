"""Custom exception hierarchy for PDEAlchemy."""

from __future__ import annotations


class PDEAlchemyError(Exception):
    """Base exception for user-facing PDEAlchemy errors."""

    def __init__(
        self,
        message: str,
        *,
        suggestion: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialise an error with optional details and remediation guidance."""
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion
        self.details = details

    def to_cli_message(self) -> str:
        """Render a rich-friendly error message."""
        lines = [f"[bold red]Error:[/bold red] {self.message}"]
        if self.details:
            lines.append(f"[dim]{self.details}[/dim]")
        if self.suggestion:
            lines.append(f"[bold]Suggestion:[/bold] {self.suggestion}")
        return "\n".join(lines)


class ConfigError(PDEAlchemyError):
    """Raised when configuration files are missing or invalid."""


class ValidationError(PDEAlchemyError):
    """Raised when validation fails."""


class PricingError(PDEAlchemyError):
    """Raised when pricing cannot be completed."""


class RenderError(PDEAlchemyError):
    """Raised when explain rendering cannot be completed."""


class MathBridgeError(PDEAlchemyError):
    """Raised when symbolic parsing or compilation fails."""
