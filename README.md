# Job Search AI Assistant *(In Progress)*  
**Fighting AI with AI — Automate your job hunt and stand out in a saturated market.**

---

## 🚀 Overview

In an era of AI-generated resumes, automated filters, and thousands of applicants per role, finding a meaningful job has become more frustrating than ever — especially for junior or transitioning developers.

**Job Search AI Assistant** is an intelligent, AI-powered platform that tackles this problem head-on — automating and enhancing every step of the job search using the same technology being used against job seekers.

> Built to help developers break through the noise — not just apply, but stand out.

---

## ✨ Key Features

### 🔍 Smart Job Matching
- Aggregates listings from GitHub Jobs, Reed.co.uk, and Indeed.
- Filters jobs by skills, location, and preferences.
- Continuously updates using free public APIs.

### 📝 AI-Powered Cover Letter Generation
- Uses LangChain + OpenAI to craft tailored, high-quality cover letters.
- Analyzes each job description alongside your uploaded CV.
- Designed to be role-specific and personalized, not generic templates.

### 🧾 RAG-Powered CV Matching
- Upload your CV and paste job descriptions.
- Uses Retrieval-Augmented Generation (RAG) to evaluate fit and extract personalized talking points.
- Matches your experience with job requirements intelligently.

### 🔗 LinkedIn Integration (Coming Soon)
- Connects with LinkedIn API (OAuth).
- Auto-fills personal and professional data to streamline submissions.
- Enables smarter prep and potential auto-apply features.

---

## 💡 Why This Project?

The job market is flooded with auto-generated applications — ironically, driven by the same AI that now filters out candidates.

I'm building this tool to **fight AI with AI** — using smart automation to help job seekers:
- Save hours of repetitive effort
- Deliver higher-quality applications
- Stand out in a competitive market

It's also a way for me to level up my technical skills in AI, automation, and full-stack development.

---

## 🖼️ UI Preview

<img width="100%" alt="Job Search AI – CV Upload UI" src="https://github.com/user-attachments/assets/6f098db3-97d2-46ef-8cd4-a20408505ef6" />

> Simple, clean, and focused on what matters: relevance and speed.  
> *(Upload your CV, search jobs by title and location, then let AI take it from there.)*

---

## 📝 Sample Output

Coming soon: A sample AI-generated cover letter PDF created from a real CV and job description.  
Check back for updates!

---

## 🛠️ Tech Stack

| Area        | Tools / Technologies                |
|-------------|-------------------------------------|
| Language    | Python, JavaScript (OAuth logic)    |
| Backend     | FastAPI (planned)                   |
| AI & NLP    | LangChain, OpenAI API               |
| RAG Search  | FAISS (or Pinecone – TBD)           |
| Job APIs    | GitHub Jobs, Reed.co.uk, Indeed     |
| Frontend    | React (MVP complete)                |
| Auth        | LinkedIn OAuth 2.0 (planned)        |
| Deployment  | Currently in local development      |

> **Note:** FAISS and Pinecone are vector search libraries used in Retrieval-Augmented Generation. FAISS is local and open-source; Pinecone is hosted and scalable.

---

## 🗺️ Roadmap

- [x] Basic job aggregation from public APIs
- [x] LangChain-powered cover letter generator
- [x] CV/Job Description upload + RAG
- [x] Frontend UI MVP
- [ ] LinkedIn OAuth integration
- [ ] Application tracking dashboard (optional)
- [ ] Hosted deployment (Vercel / Streamlit / Render)
- [ ] Auth & user account system (planned)

---

## 🔐 Security & Privacy (Planned)

- All data is processed locally in the current version.
- Future hosted version will include secure file upload handling and OAuth token management.
- No user data is stored or transmitted to third parties beyond necessary API calls.

---

## 🤝 Contributing

Feedback, ideas, and contributions are always welcome!

1. Fork the repo
2. Create a feature branch
3. Submit a pull request or open an issue

---

## 📫 Contact

**Eleni Salamouri**  
📧 [elenisalamouri@gmail.com](mailto:elenisalamouri@gmail.com)  
🔗 [linkedin.com/in/eleni-salamouri](https://www.linkedin.com/in/eleni-salamouri/)


---

## 📄 License

MIT License — see [LICENSE](./LICENSE)

