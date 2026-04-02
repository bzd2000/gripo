"""Custom Textual messages for inter-widget communication."""

from textual.message import Message


class DataChanged(Message):
    """Posted after any Database mutation so widgets can refresh themselves."""
