import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from datamanager.data_manager import DataManager
from datamanager.data_model import User, DataModel, Skill

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
        self.datamanager = DataManager()

    def create_basic_skills(self):
        """Creates and assigns basic skills to the user."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a psychoanalyst. When asked to list items, respond only with a valid JSON list of plain strings. "
                    "Do not include explanations, formatting, or code blocks — only output the raw JSON array."
                ),
            },
            {
                "role": "user",
                "content": (
                    "List 5 essential social skills needed for chat-based communication. "
                    'Respond ONLY with a JSON array of strings like this: ["Skill1", "Skill2", ...]'
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )

        try:
            response_text = response.choices[0].message.content.strip()
            skills_list = json.loads(response_text)
        except json.JSONDecodeError:
            print("[!] Failed to parse skill list")
            return

        if not isinstance(skills_list, list):
            print("[!] Parsed skills are not a list")
            return

        for skill_name in skills_list:
            skill = self.datamanager.get_or_create_skill(skill_name)
            self.datamanager.link_user_skill(self.user.id, skill.id)

        print("✅ Basic skills assigned to user.")

    def interactive_skill_test(self):
        steps: list[Step] = []

        # Ensure skill exists in DB
        for skill in next(data.get_db_session()).query(Skill).all():

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a psychoanalyst. Create a conversation to evaluate the user's skill "
                        f"in {skill.skill_name}. You'll get responses to your chosen topics. Enforce 5 responses for evaluation. "
                        "Do NOT give a final score until asked. Give the impression of a interesting conversation."
                        "Start the conversation with the following greeting and a summary topics to talk about. "
                        f"Hi {self.user.username} and welcome to the socializer training."
                        "First I want to see what topics we can talk about, for example:...."
                    ),
                },
                {"role": "user", "content": "Hi! "},
            ]

            for _ in range(5):
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

                if user_answer.lower().strip() in {"stop", "enough", "exit"}:
                    break

            # Ask for final evaluation
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Based on the previous conversation, please rate my skill "
                        f"in {skill.skill_name} from 1 to 10. Provide a JSON response with this format:\n"
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

            print(
                f"\n✅ Final skill level for '{skill.skill_name}': {reasoning.final_value}/10"
            )
            for step in reasoning.steps:
                print(f"- Q: {step.question}\n  A: {step.user_answer}")

            # Save skill level to DB
            self.datamanager.set_skill_for_user(
                self.user.id, skill.id, reasoning.final_value
            )
        print("I really enjoy our conversation.")
        return True


if __name__ == "__main__":
    db = DataModel()
    db.create_db_and_tables()

    data = DataManager()
    user = (
        next(db.get_session()).query(User).filter(User.username == "test_user").first()
    )
    if user is None:
        user = User(
            username="test_user", hashed_password="hashed_password", role="user"
        )
        data.add_user(user)

    chatbot = Chatbot(user)

    # Assign basic skills to user
    chatbot.create_basic_skills()

    # Test a specific skill

    chatbot.interactive_skill_test()
