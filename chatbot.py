import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from datamanager.data_manager import DataManager
from datamanager.data_model import User, DataModel, Skill, Training

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
        self.standard_prompt = (
            "You are a psychoanalyst. When asked to list items, respond only with a valid JSON"
            " list of plain strings. \nDo not include explanations, formatting, or code blocks"
            " — only output the raw JSON array."
        )

    def create_basic_skills(self):
        """Creates and assigns basic skills to the user."""
        if len(self.datamanager.get_skills_for_user(self.user.id)) > 0:
            messages = [
                {
                    "role": "system",
                    "content": self.standard_prompt,
                },
                {
                    "role": "user",
                    "content": (
                        f"List 3 essential social skills not included in the following old skills list:"
                        f"{self.datamanager.get_skills_for_user(self.user.id)}"
                        "Choose them regarding following user preferences:"
                        f'{self.user.preferences or "Basic chatting skills"}. '
                        "Respond ONLY with a JSON array of strings like this: "
                        '["OldSkill1", "OldSkill2", ..., "NewSkill1",...]'
                    ),
                },
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=self.user.temperature,
            )

            try:
                response_text = response.choices[0].message.content.strip()
                skills_list = json.loads(response_text)
            except json.JSONDecodeError:
                print("[!] Failed to parse skill list")
                return False

            if not isinstance(skills_list, list):
                print("[!] Parsed skills are not a list")
                return False

            for skill_name in skills_list:
                skill = self.datamanager.get_or_create_skill(skill_name)
                self.datamanager.link_user_skill(self.user.id, skill.id)

            print("✅ Basic skills advanced.")
            return True

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
                    "List 3 essential social skills needed for chat-based communication. "
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

    def interactive_skill_test(self, input_type: int = 0, skill_name: str = ""):
        steps: list[Step] = []
        temperature = self.user.temperature
        if skill_name != "":
            skill = self.datamanager.get_or_create_skill(skill_name)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a psychoanalyst. Create a conversation to evaluate the user's skill "
                        f"in {skill_name}. You'll get responses to your chosen topics. Enforce 5 responses for evaluation. "
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
                    temperature=self.user.temperature,
                )

                bot_message = response.choices[0].message.content.strip()
                print(f"🤖 {bot_message}")
                user_answer = self.get_user_input(
                    input_text="Your answer:", input_type=input_type
                )

                steps.append(Step(question=bot_message, user_answer=user_answer))
                messages.append({"role": "assistant", "content": bot_message})
                messages.append({"role": "user", "content": user_answer})

                if user_answer.lower().strip() in {"stop", "enough", "exit"}:
                    return False

            # Ask for final evaluation
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Based on the previous conversation, rate the skill "
                        f"in {skill_name} from 1 to 10. Provide a JSON response with this format:\n"
                        "{\n"
                        '  "final_value": 0-10\n'
                        "}"
                    ),
                }
            )

            eval_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=self.user.temperature,
            )

            content = eval_response.choices[0].message.content
            try:
                parsed = json.loads(content)
                # reasoning = Reasoning(**parsed)
            except Exception as e:
                print(f"[!] Failed to parse final result: {e}")
                print("Raw output:\n", content)
                return False

            print(f'🤖 {parsed["final_value"]}')

            # Save skill level to DB
            self.datamanager.set_skill_for_user(
                self.user.id, skill, parsed["final_value"]
            )
            print("I really enjoy our conversation.")
            return True

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
                    temperature=self.user.temperature,
                )

                bot_message = response.choices[0].message.content.strip()
                print(f"🤖 {bot_message}")
                user_answer = self.get_user_input(
                    input_text="Your answer:", input_type=input_type
                )

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
                        "Based on the previous conversation, rate the skill "
                        f"in {skill.skill_name} from 1 to 10."
                        "Also try to evaluate the temperature for the messages with the given user."
                        "Provide a JSON response with this format:\n"
                        "{\n"
                        '  "final_value": 0-10\n'
                        '  "user_temperature": 0.0-1.0'
                        "}"
                    ),
                }
            )

            eval_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=self.user.temperature,
            )

            content = eval_response.choices[0].message.content
            try:
                parsed = json.loads(content)
                # reasoning = Reasoning(**parsed)
            except Exception as e:
                print(f"[!] Failed to parse final result: {e}")
                print("Raw output:\n", content)
                return False

            print(f'🤖{skill.skill_name}: {parsed["final_value"]}')
            if self.user.temperature != parsed["user_temperature"]:
                print(f'User_Id: {self.user.id} Temp: {parsed["user_temperature"]}')
                self.user.temperature = parsed["user_temperature"]
                self.datamanager.set_user_temperature(
                    self.user.id, parsed["user_temperature"]
                )

            # Save skill level to DB
            self.datamanager.set_skill_for_user(
                self.user.id, skill, parsed["final_value"]
            )
        print("I really enjoy our conversation.")
        return True

    def create_training(self):
        """
        Create a new training for the user based on their current skill levels.

        :return: True if successful, False otherwise
        """
        # Get user skills and their levels
        try:
            skills = self.datamanager.get_skills_for_user(self.user.id)
            skill_levels = {}
            for skill in skills:
                level = self.datamanager.get_skilllevel_for_user(self.user.id, skill.id)
                skill_levels[skill.skill_name] = (
                    level  # Assuming 'skill_name' is the attribute to access skill names
                )
        except Exception as e:
            print(f"Error fetching user skills or levels: {e}")
            return False

        if not skill_levels:
            print("User has no skills assigned.")
            return False

        # Check if all skills are at maximum level (assuming level 10)
        if all(level == 10 for level in skill_levels.values()):
            try:
                # Create new training
                self.create_basic_skills()
                self.interactive_skill_test()
            except Exception as e:
                print(f"Error creating new skills: {e}")
                return False

        # Create a training based on the current skill levels
        topic_prompts = [
            (
                f"Create a training focusing on improving the user's {skill.skill_name}, "
                f"regarding his current level: {skill_levels[skill.skill_name]}. "
                f"Adapt the training to the user's"
                f" preferences:"
                f" {self.user.preferences} "
            )
            for skill in skills
        ]

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are still psychoanalyst and live coach. Create a training plans for {self.user.username} "
                        f"with topics: {' '.join(topic_prompts)}."
                        "Provide a JSON response with exactly this format and no further text:\n"
                        '{"skills":[skill_name0, skill_name1,...],\n'
                        '"bodies":[(Text for skill_name0 describing training plan for this skill),'
                        " (Text for skill_name1 describing training plan for this skill),"
                        "...]}"
                    ),
                }
            ]
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=self.user.temperature,
            )
            raw_content = response.choices[0].message.content
            parsed_response = json.loads(raw_content)
            """if not isinstance(parsed_response, dict) or "skills" not in parsed_response:
                print("Unexpected response format from GPT-4o-mini")
                return False"""
        except ValueError as e:
            print(f"Error parsing JSON response: {e}")
            print("Raw output:\n", raw_content)
            return False
        except Exception as e:
            print(f"Error creating training: {e}")
            return False

        # Add trainings based on the parsed response
        try:
            for ind, skill in enumerate(skills):
                body = parsed_response["bodies"][ind]
                try:
                    self.datamanager.add_training(
                        Training(user_id=self.user.id, skill_id=skill.id, body=body)
                    )
                except Exception as e:
                    print(f"[!] Failed to add training for {skill}: {e}")
            print("Training added successfully!")
        except Exception as e:
            print(f"Error adding training: {e}")
            return False

        return True

    def get_user_input(self, input_text: str, input_type: int = 0) -> str | None:
        """
        Get user input from chosen input type...
        :param input_text: Text to display to user
        :param input_type: 0 for console, 1 for html form, 2 for GUI
        :return str: User input
        """
        if input_type == 0:
            return input(input_text)
        elif input_type == 1:
            return None
        elif input_type == 2:
            return None
        else:
            print("Invalid input type. Using console input.")
            return input(input_text)


if __name__ == "__main__":
    db = DataModel()
    db.create_db_and_tables()

    data = DataManager()

    user = data.get_user_by_username("test_user")
    # Assign basic skills to user if not already existing

    if user is None:
        user = User(
            username="test_user", hashed_password="hashed_password", role="user"
        )
        data.add_user(user)
    chatbot = Chatbot(user)
    chatbot.create_basic_skills()

    # Test a specific skill
    # chatbot.interactive_skill_test()

    # Create training for existing skills not yet at 10

    chatbot.create_training()
