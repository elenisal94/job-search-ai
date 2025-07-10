from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import shutil
from job_search_core import JobSearchAgent 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = JobSearchAgent() 

@app.post("/analyze")
async def analyze(cv: UploadFile, job_query: str = Form(...)):
    try:

        # Save uploaded CV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(cv.file, tmp)
            tmp_path = tmp.name

        # Setup CV and search/analyze jobs
        agent.setup_cv(tmp_path)

        matches = agent.search_and_analyze_jobs(job_query)

        return JSONResponse(content={"matches": [m.__dict__ for m in matches]})
    except Exception as e:
        import traceback
        print("❌ Error during /analyze request:")
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)
