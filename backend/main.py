import requests
import json
import sqlite3
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ==========================================
# Database Configuration & Initialization
# ==========================================
DB_FILE = "peerguard.db"

def init_db():
    """Initialize SQLite database and create tables if they do not exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rubrics (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            rubric_data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# FastAPI Application Setup
# ==========================================
app = FastAPI(title="PeerGuard AI - Backend API")

class AssignmentRequest(BaseModel):
    prompt: str

# ==========================================
# Core API Routes
# ==========================================
@app.post("/api/generate-rubric")
def generate_and_save_rubric(request: AssignmentRequest):
    print(f"Received generation request for prompt: {request.prompt[:30]}...")
    
    url = "http://localhost:11434/api/generate"
    
    # English prompt to ensure the LLM generates English content
    system_instruction = f"""
    You are a senior Computer Science professor. Based on the following [Assignment Prompt], 
    generate a comprehensive grading rubric for peer assessment.
    You MUST output strictly in JSON format. Do not include markdown blocks.
    
    The JSON structure MUST be exactly as follows:
    {{
      "assignment_title": "Title of the assignment",
      "rubric_items": [
        {{ 
          "dimension": "Grading dimension (e.g., Code Logic, Error Handling)", 
          "description": "Specific grading criteria and expectations" 
        }}
      ]
    }}

    [Assignment Prompt]:
    {request.prompt}
    """
    
    payload = {
        "model": "qwen3:8b", 
        "prompt": system_instruction,
        "stream": False,
        "format": "json"
    }

    try:
        # Request generation from local Ollama
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Local LLM service failed to respond.")
            
        raw_text = response.json().get("response")
        rubric_json = json.loads(raw_text)
        
        # Save to SQLite database
        rubric_id = str(uuid.uuid4())
        title = rubric_json.get("assignment_title", "Untitled Assignment")
        rubric_string = json.dumps(rubric_json)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rubrics (id, title, rubric_data) VALUES (?, ?, ?)", 
            (rubric_id, title, rubric_string)
        )
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "Rubric successfully generated and saved.",
            "data": {
                "id": rubric_id,
                "rubric": rubric_json
            }
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON format returned by LLM.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to local Ollama service. Is it running?")


# ==========================================
# Schema for Slice 2 (Student Review Validation)
# ==========================================
class ReviewValidationRequest(BaseModel):
    rubric_id: str
    review_text: str

# ==========================================
# Slice 2 API: The AI Interceptor (SQL-based RAG)
# ==========================================
@app.post("/api/validate-review")
def validate_peer_review(request: ReviewValidationRequest):
    print(f"Validating review for rubric_id: {request.rubric_id}")

    # ---------------------------------------------------------
    # Step 1: [R]etrieval - Fetch the specific Rubric from SQLite
    # ---------------------------------------------------------
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Execute SQL to find the exact grading criteria
    cursor.execute(
        "SELECT rubric_data FROM rubrics WHERE id = ?", (request.rubric_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Rubric not found.")
    rubric_data_string = row[0]

    # ---------------------------------------------------------
    # Step 2: [A]ugmented - Construct the strict validation prompt
    # ---------------------------------------------------------
    system_instruction = f"""
    You are a strict Teaching Assistant evaluating a student's peer review.
    Your task is to check if the [Student's Review] meets the criteria defined in the [Grading Rubric].
    A valid review MUST specifically mention concepts or details from the rubric. 
    Generic comments like "Good job", "Code works perfectly", or "Nice report" are INVALID and must be rejected.

    [Grading Rubric]:
    {rubric_data_string}

    Student's Review:
    {request.review_text}

    You MUST output strictly in JSON format.
    The JSON structure MUST be exactly as follows:
    {{
      "is_valid": true or false,
      "feedback_to_reviewer": "If invalid, tell them which specific dimension from the rubric they need to address. If valid, say 'Great feedback, ready to submit.'"
    }}

    """

    # ---------------------------------------------------------
    # Step 3: [G]eneration - Ask local LLM to make the decision
    # ---------------------------------------------------------
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen3:8b",
        "prompt": system_instruction,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(url, json = payload)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Local LLM service failed to respond.")
        
        raw_text = response.json().get("response")
        validation_result = json.loads(raw_text)

        return {
            "status": "success",
            "data": validation_result
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON format returned by LLM.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to Ollama.")