from pathlib import Path
from job_search_core import JobSearchAgent

def main():
    """Main function to run the Job Search AI Assistant"""

    agent = JobSearchAgent()

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
                # For simplicity, you can extract or summarize CV info here
                cv_summary = "Experienced full-stack developer with SaaS and automation background"
                materials = agent.generate_application_materials(selected_job.id, cv_summary)
                print(f"\nGenerated application materials for {materials['job_title']}:")
                print("=" * 50)
                print(materials['cover_letter'])
        except ValueError:
            print("Invalid selection")

if __name__ == "__main__":
    main()
