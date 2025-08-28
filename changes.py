# Assuming you have a database connection setup already (e.g., using SQLAlchemy)
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData


metadata = MetaData()
user_data = Table('user_data', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_preferences', String),
    # Add other columns as necessary
)

engine = create_engine('sqlite:///user_data.db')  # Example SQLite database
metadata.create_all(engine)  # Create the table if it doesn't exist

# Function to update user preferences in the database
def update_user_preferences(user_id, new_preferences):
    conn = engine.connect()
    query = user_data.update().where(user_data.c.id == user_id).values(user_preferences=new_preferences)
    conn.execute(query)

# Example of integrating a tool for research
tool = TavilySearch(max_results=5)

def check_latest_research():
    result = tool.invoke({"query": "latest research on social skills and conscious training"})
    return result['articles']

# In the user_response function, you can now call this tool to get latest research updates
def user_response(state: State):
    # Existing code...
    if "research" in state["messages"][-1].content.lower():
        response = check_latest_research()
        return {"messages": [llm_with_tools.invoke({"content": response, "role": "assistant"})]
