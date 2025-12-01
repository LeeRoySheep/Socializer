import json

from langchain_core.messages import ToolMessage

from state import State


class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

    # Define tool node to handle social skills training
    def train_social_skills(self, state: State, llm_with_tools=None):
        if state["messages"][-1]["role"] == "user":
            prompt = """
            You are a social skills trainer. Based on the conversation so far, identify areas where you can improve and provide targeted exercises.
            Use tools like Tavily Search to find research or models for training scenarios.
            Example response: "You need more confidence in conversations. Try practicing with real chat scenario."
            """

            # Generate feedback using AI
            response = llm_with_tools.invoke({"query": prompt})
            return {"messages": [{"role": "assistant", "content": response["response"]}]}
        return {"messages": state["messages"]}
