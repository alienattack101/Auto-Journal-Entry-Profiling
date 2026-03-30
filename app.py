from flask import Flask, redirect, render_template, request, flash, session, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import sqlite3
import os
import io
from google import genai
from google.genai import types
from dotenv import load_dotenv
from rules import JE_RULES


load_dotenv()
app = Flask(__name__)
app.secret_key = "dev-secret-key"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'csv'}

# Gemini Configuration
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    MODEL_ID = 'gemini-2.0-flash'
else:
    client = None
    print("Warning: GEMINI_API_KEY not found in environment variables.")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["TEMPLATES_AUTO_RELOAD"] = True

REQUIRED_HEADERS = [
     "JE_ID",
     "Posting_Date",
     "GL_Account",
     "Debit",
     "Credit",
     "Preparer_ID",
     "Approver_ID"
]

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
def allowed_file(filename):
    return '.' in filename and filename.rsplit ('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def main():
    return render_template("index.html")

# app route for file upload:
@app.route("/upload", methods=["POST"])
def upload():
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect("/")   
        
        file = request.files['file']
        if file.filename == '':
            flash('no file selected')
            return redirect("/")
        if file and allowed_file(file.filename):
              try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
        #if file:
              #try:
                #stream = io.StringIO(file.stream.read().decode("UTF8"))
                df = pd.read_csv(filepath)
                uploaded_headers = list(df.columns)

                # Store headers and file data in session or temporary storage 
                session['uploaded_headers'] = uploaded_headers
                session['uploaded_filename'] = filename

                return redirect("/map")
              except Exception as e:
                    return f"Error processing file: {e}",400
        else:
             flash("Invalid file type")
             return redirect("/")

# app route for header mapping: 
@app.route('/map', methods=['GET', 'POST'])
def map_headers():
    headers = session.get('uploaded_headers', [])
    filename = session.get('uploaded_filename')

    if not headers or not filename:
        return redirect("/")
             
    if request.method == 'POST':
            mapping = {}
            for req_header in REQUIRED_HEADERS:
                  mapped_to = request.form.get(req_header + '_mapping')
                  
                  if not mapped_to:
                       return f"Missing mapping for {req_header}"
                  mapping[req_header] = mapped_to
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            df = pd.read_csv(filepath)
            
            reverse_mapping = {v: k for k, v in mapping.items()}
            df.rename(columns=reverse_mapping, inplace=True) 

            mapped_filename = "mapped_" + filename
            clean_path = os.path.join(app.config['UPLOAD_FOLDER'], mapped_filename)
            df.to_csv(clean_path, index=False)

            session['mapped_file'] = mapped_filename

            # Combine standard rules with any existing session rules
            current_rules = JE_RULES + session.get('session_rules', [])
            return render_template('successful.html', rules=current_rules)
            # return "File uploaded and validated successfully"
    else:
         return render_template('map.html', uploaded_headers=headers, required_headers=REQUIRED_HEADERS)     
                       
import json

# route to execute rulesets
@app.route('/execution', methods=['POST'])
def execution():
     filename = session.get('mapped_file')
     selected_rules = request.form.getlist('selected_rules')
     
     #uploaded_filename = session.get('uploaded_filename')
     #uploaded_headers = session.get('uploaded_headers')

     if not filename:
          return redirect("/")
    
     filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
     df = pd.read_csv(filepath)
     #reverse_mapping = {v: k for k, v in mapping.items()}
     #df.rename(columns=reverse_mapping, inplace=True)  

     #Load into SQLite
     conn = sqlite3.connect(':memory:')
     df.to_sql("JE_Table", conn, if_exists="replace", index=False)
     
     results = []

     # Combine standard rules with session-based custom rules
     session_rules = session.get('session_rules', [])
      
     # Create a combined list of all potential rules
     all_potential_rules = JE_RULES + session_rules
     print(f"DEBUG: All potential rules: {[r['rule_id'] for r in all_potential_rules]}")
     print(f"DEBUG: Selected rules: {selected_rules}")
 
     #cursor = conn.cursor()
     # Loop through rules and execute only selected ones
     for rule in all_potential_rules:
         rule_id = rule["rule_id"]
          
         # Skip if rule was not selected
         if selected_rules and rule_id not in selected_rules:
             print(f"DEBUG: Skipping rule {rule_id} (not selected)")
             continue
              
         sql_query = rule["sql"]
         print(f"DEBUG: Executing rule {rule_id}")
 
         try:
            flagged_entries = pd.read_sql(sql_query, conn)
            print(f"DEBUG: Rule {rule_id} executed. Rows found: {len(flagged_entries)}")

            if not flagged_entries.empty:
               table_html = flagged_entries.to_html(classes='table', index=False)
               #count = len(flagged_entries)
            else:
               table_html = None
               #count = 0

            results.append({
                    "id": rule_id,
                    #"count": count,
                    "table": table_html
            })
     
         except Exception as e:
               print(f"DEBUG: Error in rule {rule_id}: {e}")
               results.append({
                    "id": rule_id,
                    "count": 0,
                    "table": f"Error executing rule: {e}"
               })
     
     conn.close()
     return render_template('results.html', results=results)


@app.route('/chat_generate_rule', methods=['POST'])
def chat_generate_rule():
    if not client:
        return jsonify({'error': 'Gemini API not configured'}), 503

    user_input = request.json.get('prompt')
    if not user_input:
        return jsonify({'error': 'No prompt provided'}), 400
    
    # Retrieve chat history from session, or initialize if empty
    chat_history_dicts = session.get('chat_history', [])
    
    # Reconstruct history as Content objects for the SDK
    history = []
    for msg in chat_history_dicts:
        # Create Content objects. Note: SDK v2 uses 'parts' with 'text'
        parts = [types.Part(text=part_text) for part_text in msg.get('parts', [])]
        history.append(types.Content(role=msg.get('role'), parts=parts))

    # Context for Gemini about the table structure and goal
    system_instruction = """
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
    
    If the user asks for a modification (e.g., "change the limit to 5000"), modify the PREVIOUS rule and return the updated JSON.
    
    Return ONLY a valid JSON object with the following structure:
    {
        "rule_id": "Generated_Rule_ID_XXX",
        "rule_description": "Description of what the rule checks",
        "sql": "The SQL query to execute",
        "chat_response": "A friendly message explaining what this rule does or how it was modified."
    }
    Do not include markdown formatting or explanations outside the JSON.
    """
    
    try:
        # If history is empty, send system instruction first (as the first message in history)
        if not history:
             # Add system instruction as user message (common pattern if system role not explicitly supported in same way,
             # but with google-genai client we can often use config or just preload history)
             # Let's just add it as the first context piece.
             history.append(types.Content(role="user", parts=[types.Part(text=system_instruction)]))
             history.append(types.Content(role="model", parts=[types.Part(text="Understood. I'm ready to help with JE analysis SQL queries.")]))

        chat = client.chats.create(model=MODEL_ID, history=history)

        response = chat.send_message(user_input)
        generated_text = response.text
        
        # Cleanup potential markdown code blocks
        clean_text = generated_text.replace('```json', '').replace('```', '').strip()
        
        # Update session history
        # We need to manually reconstruct what we want to save because chat.history might be complex objects
        # We'll just append the new turn to our simple dict list for next time
        
        # Append the new user input
        chat_history_dicts.append({
            'role': 'user',
            'parts': [user_input]
        })
        # Append the model response
        chat_history_dicts.append({
             'role': 'model',
             'parts': [generated_text]
        })

        # If we started fresh, we should also save the system instruction turn so context isn't lost
        if len(chat_history_dicts) == 2: # Just added user+model, but we had system+ack before
             # We should prepend the system instruction interaction we did implicitly
             chat_history_dicts.insert(0, {'role': 'model', 'parts': ["Understood. I'm ready to help with JE analysis SQL queries."]})
             chat_history_dicts.insert(0, {'role': 'user', 'parts': [system_instruction]})
             
        session['chat_history'] = chat_history_dicts
        session.modified = True
        
        try:
            rule_obj = json.loads(clean_text)
            return jsonify({
                'message': rule_obj.get('chat_response', 'Here is the rule you requested.'),
                'rule_obj': rule_obj
            })
        except json.JSONDecodeError:
            # If AI didn't return valid JSON (e.g. conversational reply), return text
            return jsonify({'message': generated_text})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat_approve_rule', methods=['POST'])
def chat_approve_rule():
    rule_data = request.json.get('rule')
    if not rule_data:
        return jsonify({'error': 'No rule data provided'}), 400
    
    # Initialize session rules list if not present
    if 'session_rules' not in session:
        session['session_rules'] = []
    
    # Add the new rule to the session
    session['session_rules'].append(rule_data)
    session.modified = True
    
    return jsonify({'success': True})







 
         