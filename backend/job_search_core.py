import os
import re
import sqlite3
from typing import List, Optional, Dict
from dataclasses import dataclass

from langchain_community.llms import OpenAI
from langchain.chains import LLMChain, RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

import requests
from dotenv import load_dotenv

load_dotenv()

@dataclass
class JobPosting:
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
    def __init__(self, db_path: str = "job_search.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, company, location, description, requirements, salary, url, date_posted, source, match_score
            FROM jobs ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        jobs = [JobPosting(*row) for row in cursor.fetchall()]
        conn.close()
        return jobs

class JobAPIClient:
    def __init__(self):
        self.session = requests.Session()
        self.reed_api_key = os.getenv("REED_API_KEY")
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")

    def search_reed_jobs(self, keywords: str, location: str = "London", limit: int = 10) -> List[JobPosting]:
        if not self.reed_api_key:
            print("Reed API key missing.")
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
                jobs.append(JobPosting(
                    id=f"reed_{job_data['jobId']}",
                    title=job_data['jobTitle'],
                    company=job_data['employerName'],
                    location=job_data['locationName'],
                    description=job_data['jobDescription'],
                    requirements=job_data.get('jobDescription', ''),
                    salary=job_data.get('minimumSalary', ''),
                    url=job_data['jobUrl'],
                    date_posted=job_data['date'],
                    source="Reed"
                ))
            return jobs
        except requests.RequestException as e:
            print(f"Error fetching Reed jobs: {e}")
            return []

    def search_adzuna_jobs(self, keywords: str, location: str = "London", limit: int = 10) -> List[JobPosting]:
        if not self.adzuna_app_id or not self.adzuna_app_key:
            print("Adzuna API credentials missing.")
            return []
        url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
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
                jobs.append(JobPosting(
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
                ))
            return jobs
        except requests.RequestException as e:
            print(f"Error fetching Adzuna jobs: {e}")
            return []

class CVAnalyzer:
    def __init__(self):
        self.llm = OpenAI(temperature=0.3)
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.qa_chain = None

    def load_cv(self, cv_path: str):
        if cv_path.endswith('.pdf'):
            loader = PyPDFLoader(cv_path)
        else:
            loader = TextLoader(cv_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        texts = text_splitter.split_documents(documents)
        self.vector_store = FAISS.from_documents(texts, self.embeddings)
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever()
        )

    def analyze_job_match(self, job: JobPosting) -> float:
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
            result = self.qa_chain.invoke(query)
            return self._extract_score(result)
        except Exception as e:
            print(f"Error analyzing job match: {e}")
            return 0.0

    def _extract_score(self, result: str) -> float:
        match = re.search(r'(\d+(?:\.\d+)?)', result)
        if match:
            return float(match.group(1))
        return 0.0

class CoverLetterGenerator:
    def __init__(self):
        self.llm = OpenAI(temperature=0.7)
        template = """
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
            template=template
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def generate_cover_letter(self, job: JobPosting, cv_summary: str) -> str:
        try:
            return self.chain.run(
                job_title=job.title,
                company=job.company,
                requirements=job.requirements,
                cv_summary=cv_summary
            )
        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return ""

class JobSearchAgent:
    def __init__(self):
        self.db = JobSearchDatabase()
        self.api_client = JobAPIClient()
        self.cv_analyzer = CVAnalyzer()
        self.cover_letter_generator = CoverLetterGenerator()
        self.llm = OpenAI(temperature=0.3)

    def setup_cv(self, cv_path: str):
        self.cv_analyzer.load_cv(cv_path)

    def search_and_analyze_jobs(self, keywords: str, location: str = "London", limit: int = 10) -> List[JobPosting]:
        reed_jobs = self.api_client.search_reed_jobs(keywords, location, limit)
        adzuna_jobs = self.api_client.search_adzuna_jobs(keywords, location, limit)
        all_jobs = reed_jobs + adzuna_jobs

        for job in all_jobs:
            if self.cv_analyzer.qa_chain:
                job.match_score = self.cv_analyzer.analyze_job_match(job)
            self.db.save_job(job)

        all_jobs.sort(key=lambda j: j.match_score or 0, reverse=True)
        return all_jobs

    def generate_application_materials(self, job_id: str, cv_summary: str) -> Dict[str, str]:
        jobs = self.db.get_jobs()
        job = next((j for j in jobs if j.id == job_id), None)
        if not job:
            return {"error": "Job not found"}
        cover_letter = self.cover_letter_generator.generate_cover_letter(job, cv_summary)
        return {
            "job_title": job.title,
            "company": job.company,
            "cover_letter": cover_letter,
            "job_url": job.url
        }

    def get_job_recommendations(self, limit: int = 5) -> List[JobPosting]:
        jobs = self.db.get_jobs()
        scored_jobs = [job for job in jobs if job.match_score is not None]
        scored_jobs.sort(key=lambda j: j.match_score, reverse=True)
        return scored_jobs[:limit]
