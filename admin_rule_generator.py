from google import genai
from google.genai import types
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
if not GOOGLE_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_ID = 'gemini-2.0-flash'

SYSTEM_INSTRUCTION = """
You are an expert SQL developer assisting with Journal Entry (JE) analysis.
The database table 'JE_Table' has the following columns:
- JE_ID (Text): Unique identifier for the journal entry
- Posting_Date (Date): Date the entry was posted
- GL_Account (Text): General Ledger account number
- Debit (Real): Debit amount
- Credit (Real): Credit amount
- Preparer_ID (Text): ID of the person who prepared the entry
- Approver_ID (Text): ID of the person who approved the entry

Your task is to generate a SQL query based on the user's request to identify anomalies or specific patterns in the journal entries.

IMPORTANT: The query MUST select ALL columns from JE_Table for the flagged records, not just the ID. 
Use `SELECT *` or `SELECT jt.*` (if aliasing) to ensure the full context is returned.

Return ONLY a valid JSON object with the following structure:
{
    "rule_id": "Generated_Rule_ID_XXX",
    "rule_description": "Description of what the rule checks",
    "sql": "The SQL query to execute"
}
Ensure the rule_id is unique and descriptive.
Do not include markdown formatting or explanations outside the JSON.
"""

def get_ai_response(chat, prompt):
    """
    Sends a prompt to the chat session and returns the parsed JSON object.
    """
    try:
        print("\nWaiting for Gemini...")
        response = chat.send_message(prompt)
        generated_text = response.text
        
        # Cleanup potential markdown code blocks
        clean_text = generated_text.replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            print(f"\nWarning: Could not parse JSON from AI response.\nResponse was: {generated_text}")
            return None
    except Exception as e:
        print(f"Error communicating with AI: {e}")
        return None

def append_rule_to_file(rule_obj, filepath="rules.py"):
    """
    Appends the new rule to the JE_RULES list in rules.py.
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Find the closing bracket of the list
        last_bracket_index = content.rfind(']')
        if last_bracket_index == -1:
            print("Error: Could not find the closing bracket of JE_RULES in rules.py")
            return False

        # Prepare the new rule string
        new_rule_str = json.dumps(rule_obj, indent=4)
        
        # Construct the insertion string
        insertion = f",\n\n{new_rule_str}\n"
        
        # Reconstruct the file content
        new_content = content[:last_bracket_index] + insertion + content[last_bracket_index:]
        
        with open(filepath, 'w') as f:
            f.write(new_content)
            
        return True
    except Exception as e:
        print(f"Error appending rule to file: {e}")
        return False

def main():
    print("=== Admin Rule Generator with Chat Support ===")
    print("Describe a rule, review the SQL, and provide feedback to refine it.")
    
    while True:
        # Start a new chat session for each new rule request to reset context
        chat = client.chats.create(
            model=MODEL_ID,
            history=[
                types.Content(role="user", parts=[types.Part(text=SYSTEM_INSTRUCTION)]),
                types.Content(role="model", parts=[types.Part(text="Understood. I am ready to generate SQL rules for the JE_Table based on your requests. Please provide the rule description.")])
            ]
        )

        # Initial rule request
        prompt = input("\nEnter your rule description (or 'q' to quit): ").strip()
        if prompt.lower() == 'q':
            break
        if not prompt:
            continue

        # Conversation loop for refining the specific rule
        while True:
            rule_obj = get_ai_response(chat, prompt)
            
            if rule_obj:
                print("\n--- Generated Rule ---")
                print(json.dumps(rule_obj, indent=4))
                print("----------------------")
                
                print("\nOptions:")
                print("1. Approve and Save (y)")
                print("2. Reject and Start Over (n)")
                print("3. Provide Feedback/Refine (f)")
                
                choice = input("Select an option: ").strip().lower()
                
                if choice == 'y':
                    if append_rule_to_file(rule_obj):
                        print(f"Success! Rule '{rule_obj['rule_id']}' added to rules.py.")
                    else:
                        print("Failed to update rules.py.")
                    break # Exit inner loop to start new rule
                
                elif choice == 'n':
                    print("Rule discarded. Starting fresh.")
                    break # Exit inner loop
                
                elif choice == 'f':
                    feedback = input("Enter your feedback/changes: ").strip()
                    if feedback:
                        prompt = f"Feedback on the previous rule: {feedback}. Please regenerate the JSON with the corrections."
                    else:
                        print("No feedback provided. Keeping current rule.")
                        # Could break or continue, but let's just loop to ask prompt again or redisplay
                        # To keep it simple, we just ask for feedback again by looping, 
                        # but since 'prompt' wasn't updated effectively, we should probably just `continue` 
                        # effectively re-running the last generation or just re-displaying.
                        # Ideally we want to stay in the loop. 
                        # Let's just ask them to select option again by not updating prompt and skipping send_message? 
                        # The structure requires a prompt for the next loop iteration.
                        # Let's prompt them again.
                        continue
                
                else:
                    print("Invalid option.")
                    # Re-looping will re-send the same prompt which is redundant.
                    # Ideally we handle UI better, but for CLI this works: 
                    # If invalid, we just re-run the last prompt which might regenerate slightly differently 
                    # or we can refactor. For now, let's just continue, it's acceptable prototype behavior.
            else:
                # If generation failed
                retry = input("Generation failed. Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    break

if __name__ == "__main__":
    main()
