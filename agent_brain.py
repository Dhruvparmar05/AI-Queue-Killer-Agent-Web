from google import genai
from google.genai import types
import json

def ask_agent_for_plan(user_input):
    client = genai.Client()
    
    system_instruction = """
    You are an Autonomous Queue Killer Agent. Your job is to analyze user requests for various government or private domains (RTO, Passport, Hospital, etc.) and output a strict JSON action plan.
    Identify the domain and generate the exact step-by-step fields required for automation.
    """
    
    prompt = f"Analyze this request and build a execution map: '{user_input}'"
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            # We enforce a dynamic schema based on domain detection
        ),
    )
    return json.loads(response.text)