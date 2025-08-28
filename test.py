"""Tool Based Generative UI feature.

No special handling is required for this feature.
"""

from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


from pydantic_ai import Agent

agent = Agent("openai:gpt-4o-mini")
mat = agent.to_ag_ui()

if __name__ == "__main__":
    uvicorn.run(mat)
