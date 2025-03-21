#!/usr/bin/env python
# coding: utf-8


import litellm

litellm._turn_on_debug()

def query_litellm(model_name: str, prompt: str) -> str:
    """
    Query a LiteLLM-compatible model with a given prompt.

    Args:
        model_name (str): The model to use (e.g. 'ollama/qwen2.5' or 'huggingface/your-model').
        prompt (str): The user's input question.

    Returns:
        str: The model's response text.
    """
    response = litellm.completion(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )

    return response['choices'][0]['message']['content']


# In[2]:


from dotenv import load_dotenv

load_dotenv()


def callModels(prompt: str, model1_name:str='ollama/hf.co/ernanhughes/Fin-R1-Q8_0-GGUF', model2_name:str='ollama/phi3') -> tuple:
    """
    Call the two models and return their responses."
    """
    model1_response = query_litellm(model_name=model1_name, prompt=prompt)
    model2_response = query_litellm(model_name=model2_name, prompt=prompt)
    return model1_response, model2_response


# In[3]:


def build_comparison_prompt(question: str, response_a: str, response_b: str) -> str:
    return f"""
        ### Task:
        You are a financial reasoning expert. Two models have provided investment advice in CoT format.
        Evaluate which advice is more helpful, complete, and appropriate based on reasoning and financial knowledge.

        ### Instructions:
        1. Assess each response based on:
        - Accuracy and factual correctness
        - Clarity and coherence
        - Depth of explanation
        - Relevance to the question

        2. Assign each response a score from **0 to 10**.

        3. Provide a short justification for your scoring.

        ---

        ### Question:
        {question}

        ---

        ### Response A:
        {response_a}

        ---

        ### Response B:
        {response_b}

        ---

        ### Output Format:

        Response A Score: X/10 Response B Score: Y/10

        Winner: Response A or Response B or Tie

        Justification: <your analysis here>
        """


# In[4]:


import sqlite3
from pprint import pprint

# --- Step 1: Define a UserProfile class ---
class UserProfile:
    def __init__(self, name, age, gender, risk_tolerance, investment_goal, investment_horizon_years, current_portfolio, economic_context):
        self.name = name
        self.age = age
        self.gender = gender
        self.risk_tolerance = risk_tolerance
        self.investment_goal = investment_goal
        self.investment_horizon_years = investment_horizon_years
        self.current_portfolio = current_portfolio
        self.economic_context = economic_context

    def to_dict(self):
        return self.__dict__

# --- Step 2: Initialize user profiles ---
user_profiles = [
    UserProfile(
        name="User A",
        age=35,
        gender="female",
        risk_tolerance="moderate",
        investment_goal="retirement",
        investment_horizon_years=20,
        current_portfolio={"stocks": 6000, "bonds": 300, "cash": 1000},
        economic_context="Fed is expected to raise interest rates next quarter"
    ),
    UserProfile(
        name="User B",
        age=25,
        gender="male",
        risk_tolerance="high",
        investment_goal="wealth_growth",
        investment_horizon_years=10,
        current_portfolio={"stocks": 20000, "bonds": 10000, "cash": 300000},
        economic_context="Inflation is steady and market volatility is growing"
    )
]



# In[5]:


def gen_robo_request(user_profile: UserProfile) -> str:
    profile = user_profile.to_dict()
    return f"<think>{profile['name']} is {profile['age']} years old with a {profile['risk_tolerance']} risk tolerance. " \
        f"Goal is {profile['investment_goal']} in {profile['investment_horizon_years']} years. " \
        f"Current portfolio: {profile['current_portfolio']}. Economic context: {profile['economic_context']}."


# In[6]:


conn = sqlite3.connect("fin_r1_advisory.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_profiles (
    name TEXT PRIMARY KEY,
    age INTEGER,
    gender TEXT,
    risk_tolerance TEXT,
    investment_goal TEXT,
    horizon_years INTEGER,
    economic_context TEXT,
    current_portfolio TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS advisory_results (
    user_name TEXT,
    request TEXT,
    fin_r1_output TEXT,
    model_output TEXT,
    report_prompt TEXT,           
    report TEXT,
    FOREIGN KEY(user_name) REFERENCES user_profiles(name)
)
""")
conn.commit()


# In[ ]:


for profile in user_profiles:
    cursor.execute("""
    INSERT OR REPLACE INTO user_profiles (
        name, age, gender, risk_tolerance, investment_goal, horizon_years,
        economic_context, current_portfolio
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    (
        profile.name, profile.age, profile.gender, profile.risk_tolerance,
        profile.investment_goal, profile.investment_horizon_years,
        profile.economic_context, str(profile.current_portfolio)
    ))


    request = gen_robo_request(profile)
    qwen_response, phi_response = callModels(request)
    report_prompt = build_comparison_prompt(request, qwen_response, phi_response)
    report = query_litellm('ollama/qwen2.5', report_prompt)

    cursor.execute("""
    INSERT INTO advisory_results (
        user_name, request, fin_r1_output, model_output, report_prompt, report
    ) VALUES (?, ?, ?, ?, ?, ?)""",
    (
        profile.name, request, qwen_response, phi_response, report_prompt, report
    ))

    conn.commit()

    print(report)




# In[ ]:




