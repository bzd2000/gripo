"""Custom Textual messages for inter-widget communication."""

from textual.message import Message


class DataChanged(Message):
    """Posted after any Database mutation so widgets can refresh themselves."""


class ShowContent(Message):
    """Posted to request the content pane to display a specific view.

    Attributes:
        content_type: Identifies which content view to show (e.g. 'task', 'open_point').
        data: Arbitrary dict of data passed to the content view (e.g. record id, subject_id).
    """

    def __init__(self, content_type: str, data: dict) -> None:
        super().__init__()
        self.content_type = content_type
        self.data = data


class ContentSaved(Message):
    """Posted by a content pane widget after a successful save.

    Attributes:
        content_type: Identifies which content view emitted this message.
        data: Arbitrary dict containing the saved state (e.g. updated record id).
    """

    def __init__(self, content_type: str, data: dict) -> None:
        super().__init__()
        self.content_type = content_type
        self.data = data


class ContentCancelled(Message):
    """Posted by a content pane widget when the user cancels an edit."""
