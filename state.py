from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    """
    create State class to keep track of chat
    """

    messages: Annotated[list, add_messages]
