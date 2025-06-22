from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ActionType(str, Enum):
    """
    Enumeration of possible user action types.

    Attributes:
        VIEW_START: User started watching content
        VIEW_END: User stopped watching content
        PAUSE: User paused playback
        SEEK: User seeked in playback
        RATING: User rated content
        FAVORITE: User favorited content
    """

    VIEW_START = "view_start"
    VIEW_END = "view_end"
    PAUSE = "pause"
    SEEK = "seek"
    RATING = "rating"
    FAVORITE = "favorite"


class ViewMetadata(BaseModel):
    """
    Metadata model for viewing-related actions.

    Attributes:
        duration_seconds: Total content duration in seconds (required for VIEW_START/VIEW_END)
        current_time: Current playback position in seconds
        percent_watched: Percentage of content watched (0-100, required for VIEW_END)
        device_type: Type of device used for playback
    """

    duration_seconds: float | None = Field(
        None, description="Total content duration in seconds"
    )
    current_time: float | None = Field(
        None, description="Current playback position in seconds"
    )
    percent_watched: float | None = Field(
        None, ge=0, le=100, description="Percentage of content watched (0-100)"
    )
    device_type: str | None = Field(
        None, description="Device type (mobile, tv, web, etc.)"
    )


class UserAction(BaseModel):
    """
    Main model representing a user action event.

    Attributes:
        user_id: Unique identifier of the user
        movie_id: Unique identifier of the content
        action_type: Type of action performed
        timestamp: Unix timestamp of the event (millisecond precision)
        metadata: Action-specific metadata
    """

    user_id: str = Field(..., description="User UUID")
    movie_id: str = Field(..., description="Movie/TV Show UUID")
    action_type: ActionType = Field(..., description="Action type")
    timestamp: float = Field(
        ..., description="Event timestamp (Unix time with milliseconds)"
    )
    metadata: ViewMetadata = Field(
        default_factory=ViewMetadata, description="Action metadata"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_metadata(cls, values: Any) -> Any:
        """
        Validate metadata constraints based on action type.

        Rules:
        - VIEW_START/VIEW_END require duration_seconds
        - VIEW_END requires current_time

        Returns:
            Validated UserActionEvent instance

        Raises:
            ValueError: If required fields are missing for the action type
        """

        if isinstance(values, dict):
            if "action_type" not in values:
                raise ValueError("action_type is required")

        action_type = values.get("action_type")
        metadata = values.get("metadata", {})

        if not metadata:
            metadata = ViewMetadata()
            values["metadata"] = metadata

        if action_type in [ActionType.VIEW_START, ActionType.VIEW_END]:
            if metadata.get("duration_seconds") is None:
                raise ValueError("duration_seconds is required for this action type")

            if action_type == ActionType.VIEW_END:
                if metadata.get("current_time") is None:
                    raise ValueError("current_time is required for VIEW_END action")

        return values
