import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from datamanager.data_manager import DataManager
from datamanager.data_model import User, DataModel

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Step(BaseModel):
    question: str
    user_answer: str


class Reasoning(BaseModel):
    steps: list[Step]
    final_value: int


class Chatbot:
    def __init__(self, user: User):
        self.user = user
        self.client = client

    def interactive_skill_test(self, skill_name: str):
        steps: list[Step] = []

        print(f"\n🧠 Starting skill evaluation for '{skill_name}'...\n")

        # Start the first message with context
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a psychoanalyst. Ask one question at a time to evaluate the user's skill "
                    f"in {skill_name}. After each answer, you'll get a response. Ask 3-5 questions total. "
                    "Do NOT give a final score until asked. Just return the next question."
                ),
            },
            {
                "role": "user",
                "content": f"Please start evaluating my skill in {skill_name}.",
            },
        ]

        for _ in range(5):  # maximum 5 questions
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
            )

            bot_message = response.choices[0].message.content.strip()
            print(f"🤖 {bot_message}")
            user_answer = input("🧑 Your answer: ")

            steps.append(Step(question=bot_message, user_answer=user_answer))

            messages.append({"role": "assistant", "content": bot_message})
            messages.append({"role": "user", "content": user_answer})

            # Option to stop early
            if user_answer.lower().strip() in {"stop", "enough", "exit"}:
                break

        # Request final evaluation
        messages.append(
            {
                "role": "user",
                "content": (
                    "Based on the previous questions and answers, please rate my skill "
                    f"in {skill_name} from 0 to 10. Provide a JSON response with this format:\n"
                    "{\n"
                    '  "steps": [\n'
                    '    {"question": "...", "user_answer": "..."},\n'
                    "    ...\n"
                    "  ],\n"
                    '  "final_value": 0-10\n'
                    "}"
                ),
            }
        )

        eval_response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )

        content = eval_response.choices[0].message.content
        try:
            parsed = json.loads(content)
            reasoning = Reasoning(**parsed)
        except Exception as e:
            print(f"[!] Failed to parse final result: {e}")
            print("Raw output:\n", content)
            return

        print(f"\n✅ Final skill level: {reasoning.final_value}/10")
        for step in reasoning.steps:
            print(f"- Q: {step.question}\n  A: {step.user_answer}")

        datamanager = DataManager()
        datamanager.add_skill(reasoning.final_value)


if __name__ == "__main__":
    db = DataModel()
    db.create_db_and_tables()

    data = DataManager()
    user = User(username="test_user", hashed_password="hashed_password", role="user")
    data.add_user(user)

    chatbot = Chatbot(user)
    skill = input("🎯 Enter the skill you'd like to evaluate: ")
    chatbot.interactive_skill_test(skill_name=skill)
