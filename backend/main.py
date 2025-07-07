# File: backend/main.py
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import shutil
from job_search_core import process_cv, search_jobs, match_jobs_to_cv

app = FastAPI()

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(cv: UploadFile, job_query: str = Form(...)):
    try:
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(cv.file, tmp)
            tmp_path = tmp.name

        # Run analysis pipeline
        cv_text = process_cv(tmp_path)
        jobs = search_jobs(job_query)
        matches = match_jobs_to_cv(cv_text, jobs)

        return JSONResponse(content={"matches": matches})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
