"""
Job Search AI Assistant - Complete Framework
A LangChain-powered tool for automating job search with external APIs and OAuth
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
import sqlite3
from dataclasses import dataclass
from pathlib import Path

# LangChain imports
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.schema import Document

# OAuth and API libraries
import requests_oauthlib
from requests_oauthlib import OAuth2Session

@dataclass
class JobPosting:
    """Data class for job postings"""
    id: str
    title: str
    company: str
    location: str
    description: str
    requirements: str
    salary: Optional[str]
    url: str
    date_posted: str
    source: str
    match_score: Optional[float] = None

class JobSearchDatabase:
    """SQLite database for storing job search data"""
    
    def __init__(self, db_path: str = "job_search.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                requirements TEXT,
                salary TEXT,
                url TEXT,
                date_posted TEXT,
                source TEXT,
                match_score REAL,
                applied BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                cover_letter TEXT,
                application_date TEXT,
                status TEXT,
                notes TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_job(self, job: JobPosting):
        """Save job posting to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO jobs 
            (id, title, company, location, description, requirements, salary, url, date_posted, source, match_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job.id, job.title, job.company, job.location, job.description,
            job.requirements, job.salary, job.url, job.date_posted, job.source, job.match_score
        ))
        
        conn.commit()
        conn.close()
    
    def get_jobs(self, limit: int = 50) -> List[JobPosting]:
        """Retrieve jobs from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, company, location, description, requirements, salary, url, date_posted, source, match_score
            FROM jobs ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append(JobPosting(*row))
        
        conn.close()
        return jobs

class JobAPIClient:
    """Client for fetching jobs from various APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.reed_api_key = os.getenv("REED_API_KEY")  # Get from reed.co.uk
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")  # Get from adzuna.co.uk
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")
    
    def search_reed_jobs(self, keywords: str, location: str = "London", limit: int = 10) -> List[JobPosting]:
        """Search jobs using Reed.co.uk API"""
        if not self.reed_api_key:
            print("Reed API key not found. Get one from https://www.reed.co.uk/developers")
            return []
        
        url = "https://www.reed.co.uk/api/1.0/search"
        params = {
            "keywords": keywords,
            "locationName": location,
            "resultsToTake": limit,
            "employerType": "direct"
        }
        
        try:
            response = self.session.get(url, params=params, auth=(self.reed_api_key, ''))
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job_data in data.get('results', []):
                job = JobPosting(
                    id=f"reed_{job_data['jobId']}",
                    title=job_data['jobTitle'],
                    company=job_data['employerName'],
                    location=job_data['locationName'],
                    description=job_data['jobDescription'],
                    requirements=job_data.get('jobDescription', ''),  # Reed combines these
                    salary=job_data.get('minimumSalary', ''),
                    url=job_data['jobUrl'],
                    date_posted=job_data['date'],
                    source="Reed"
                )
                jobs.append(job)
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Error fetching Reed jobs: {e}")
            return []
    
    def search_adzuna_jobs(self, keywords: str, location: str = "London", limit: int = 10) -> List[JobPosting]:
        """Search jobs using Adzuna API"""
        if not self.adzuna_app_id or not self.adzuna_app_key:
            print("Adzuna API credentials not found. Get them from https://developer.adzuna.com/")
            return []
        
        url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1"
        params = {
            "app_id": self.adzuna_app_id,
            "app_key": self.adzuna_app_key,
            "what": keywords,
            "where": location,
            "results_per_page": limit,
            "content-type": "application/json"
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job_data in data.get('results', []):
                job = JobPosting(
                    id=f"adzuna_{job_data['id']}",
                    title=job_data['title'],
                    company=job_data['company']['display_name'],
                    location=job_data['location']['display_name'],
                    description=job_data['description'],
                    requirements=job_data.get('description', ''),
                    salary=job_data.get('salary_min', ''),
                    url=job_data['redirect_url'],
                    date_posted=job_data['created'],
                    source="Adzuna"
                )
                jobs.append(job)
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Error fetching Adzuna jobs: {e}")
            return []

class LinkedInOAuthClient:
    """OAuth client for LinkedIn API"""
    
    def __init__(self):
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.redirect_uri = "http://localhost:8080/callback"
        self.authorization_base_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.scope = ["r_liteprofile", "r_emailaddress"]
    
    def get_authorization_url(self) -> str:
        """Get LinkedIn authorization URL"""
        linkedin = OAuth2Session(
            self.client_id,
            scope=self.scope,
            redirect_uri=self.redirect_uri
        )
        authorization_url, state = linkedin.authorization_url(
            self.authorization_base_url,
            access_type="offline",
            prompt="select_account"
        )
        return authorization_url
    
    def get_token(self, authorization_response: str) -> dict:
        """Exchange authorization code for access token"""
        linkedin = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri
        )
        token = linkedin.fetch_token(
            self.token_url,
            authorization_response=authorization_response,
            client_secret=self.client_secret
        )
        return token
    
    def get_profile(self, token: dict) -> dict:
        """Get LinkedIn profile data"""
        linkedin = OAuth2Session(self.client_id, token=token)
        response = linkedin.get("https://api.linkedin.com/v2/people/~")
        return response.json()

class CVAnalyzer:
    """Analyze CV using LangChain and RAG"""
    
    def __init__(self):
        self.llm = OpenAI(temperature=0.3)
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.qa_chain = None
    
    def load_cv(self, cv_path: str):
        """Load and process CV document"""
        if cv_path.endswith('.pdf'):
            loader = PyPDFLoader(cv_path)
        else:
            loader = TextLoader(cv_path)
        
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        texts = text_splitter.split_documents(documents)
        self.vector_store = FAISS.from_documents(texts, self.embeddings)
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever()
        )
    
    def analyze_job_match(self, job: JobPosting) -> float:
        """Analyze how well a job matches the CV"""
        if not self.qa_chain:
            return 0.0
        
        query = f"""
        Based on my CV, how well do I match this job posting?
        
        Job Title: {job.title}
        Company: {job.company}
        Requirements: {job.requirements}
        
        Please provide a match score from 0-100 and explain the reasoning.
        """
        
        try:
            result = self.qa_chain.run(query)
            # Extract numeric score from result (simplified)
            # In practice, you'd want more sophisticated parsing
            score = self._extract_score(result)
            return score
        except Exception as e:
            print(f"Error analyzing job match: {e}")
            return 0.0
    
    def _extract_score(self, result: str) -> float:
        """Extract numeric score from LLM result"""
        # Simple regex to find score (you'd want to improve this)
        import re
        match = re.search(r'(\d+(?:\.\d+)?)', result)
        if match:
            return float(match.group(1))
        return 0.0

class CoverLetterGenerator:
    """Generate personalized cover letters using LangChain"""
    
    def __init__(self):
        self.llm = OpenAI(temperature=0.7)
        self.template = """
        You are a professional cover letter writer. Create a compelling cover letter based on:
        
        Job Details:
        - Position: {job_title}
        - Company: {company}
        - Requirements: {requirements}
        
        Candidate Background:
        {cv_summary}
        
        Key Instructions:
        1. Make it specific to this role and company
        2. Highlight relevant experience and skills
        3. Show enthusiasm for the position
        4. Keep it professional but personable
        5. Maximum 300 words
        
        Cover Letter:
        """
        
        self.prompt = PromptTemplate(
            input_variables=["job_title", "company", "requirements", "cv_summary"],
            template=self.template
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def generate_cover_letter(self, job: JobPosting, cv_summary: str) -> str:
        """Generate a personalized cover letter"""
        try:
            cover_letter = self.chain.run(
                job_title=job.title,
                company=job.company,
                requirements=job.requirements,
                cv_summary=cv_summary
            )
            return cover_letter
        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return ""

class JobSearchAgent:
    """Main agent orchestrating the job search process"""
    
    def __init__(self):
        self.db = JobSearchDatabase()
        self.api_client = JobAPIClient()
        self.linkedin_client = LinkedInOAuthClient()
        self.cv_analyzer = CVAnalyzer()
        self.cover_letter_generator = CoverLetterGenerator()
        self.llm = OpenAI(temperature=0.3)
    
    def setup_cv(self, cv_path: str):
        """Setup CV analysis"""
        self.cv_analyzer.load_cv(cv_path)
        print("CV loaded and analyzed successfully!")
    
    def search_and_analyze_jobs(self, keywords: str, location: str = "London", limit: int = 10):
        """Search for jobs and analyze matches"""
        print(f"Searching for '{keywords}' jobs in {location}...")
        
        # Search multiple sources
        reed_jobs = self.api_client.search_reed_jobs(keywords, location, limit)
        adzuna_jobs = self.api_client.search_adzuna_jobs(keywords, location, limit)
        
        all_jobs = reed_jobs + adzuna_jobs
        print(f"Found {len(all_jobs)} jobs")
        
        # Analyze each job
        for job in all_jobs:
            if self.cv_analyzer.qa_chain:
                job.match_score = self.cv_analyzer.analyze_job_match(job)
            
            # Save to database
            self.db.save_job(job)
        
        # Sort by match score
        all_jobs.sort(key=lambda x: x.match_score or 0, reverse=True)
        
        return all_jobs
    
    def generate_application_materials(self, job_id: str, cv_summary: str) -> Dict[str, str]:
        """Generate cover letter and application materials"""
        # Get job from database
        jobs = self.db.get_jobs()
        job = next((j for j in jobs if j.id == job_id), None)
        
        if not job:
            return {"error": "Job not found"}
        
        # Generate cover letter
        cover_letter = self.cover_letter_generator.generate_cover_letter(job, cv_summary)
        
        return {
            "job_title": job.title,
            "company": job.company,
            "cover_letter": cover_letter,
            "job_url": job.url
        }
    
    def get_job_recommendations(self, limit: int = 5) -> List[JobPosting]:
        """Get top job recommendations based on match scores"""
        jobs = self.db.get_jobs()
        scored_jobs = [job for job in jobs if job.match_score is not None]
        scored_jobs.sort(key=lambda x: x.match_score, reverse=True)
        
        return scored_jobs[:limit]

# Example usage and setup
def main():
    """Main function demonstrating the job search assistant"""
    
    # Initialize the agent
    agent = JobSearchAgent()
    
    # Setup (you'll need to provide these)
    print("Job Search AI Assistant")
    print("=" * 50)
    
    # 1. Load CV
    cv_path = input("Enter path to your CV (PDF or TXT): ")
    if Path(cv_path).exists():
        agent.setup_cv(cv_path)
    else:
        print("CV file not found. Some features will be limited.")
    
    # 2. Search for jobs
    keywords = input("Enter job search keywords (e.g., 'AI Engineer', 'Solutions Engineer'): ")
    location = input("Enter location (default: London): ") or "London"
    
    jobs = agent.search_and_analyze_jobs(keywords, location)
    
    # 3. Display top matches
    print(f"\nTop {min(5, len(jobs))} job matches:")
    for i, job in enumerate(jobs[:5]):
        print(f"\n{i+1}. {job.title} at {job.company}")
        print(f"   Location: {job.location}")
        print(f"   Match Score: {job.match_score:.1f}%" if job.match_score else "   Match Score: Not calculated")
        print(f"   URL: {job.url}")
    
    # 4. Generate application materials
    if jobs:
        job_choice = input("\nGenerate cover letter for job number (1-5): ")
        try:
            job_index = int(job_choice) - 1
            if 0 <= job_index < len(jobs):
                selected_job = jobs[job_index]
                cv_summary = "Experienced full-stack developer with SaaS and automation background"  # You'd extract this from CV
                
                materials = agent.generate_application_materials(selected_job.id, cv_summary)
                print(f"\nGenerated application materials for {materials['job_title']}:")
                print("=" * 50)
                print(materials['cover_letter'])
        except ValueError:
            print("Invalid selection")

if __name__ == "__main__":
    # Set up environment variables
    print("Before running, set these environment variables:")
    print("export OPENAI_API_KEY='your_openai_key'")
    print("export REED_API_KEY='your_reed_key'")
    print("export ADZUNA_APP_ID='your_adzuna_id'")
    print("export ADZUNA_APP_KEY='your_adzuna_key'")
    print("export LINKEDIN_CLIENT_ID='your_linkedin_id'")
    print("export LINKEDIN_CLIENT_SECRET='your_linkedin_secret'")
    print("\nInstall required packages:")
    print("pip install langchain openai faiss-cpu requests-oauthlib sqlite3")
    
    # Uncomment to run
    # main()