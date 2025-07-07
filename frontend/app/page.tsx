"use client";

import { useState } from "react";
import toast from "react-hot-toast";

export default function Home() {
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [matches, setMatches] = useState<any[]>([]);

  // Clear uploaded file handler
  const clearFile = () => setCvFile(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cvFile || !jobTitle) {
      toast.error("Please upload a CV and enter a job title.");
      return;
    }

    const jobQuery = location ? `${jobTitle} ${location}` : jobTitle;

    const formData = new FormData();
    formData.append("cv", cvFile);
    formData.append("job_query", jobQuery);

    setLoading(true);
    setMatches([]);

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Something went wrong");
      }

      setMatches(data.matches || []);
    } catch (err: any) {
      toast.error(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-tr from-teal-300 via-amber-200 to-indigo-600 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <h1 className="text-5xl font-extrabold mb-12 text-white drop-shadow-lg tracking-wide select-none">
        Job Search AI
      </h1>

      <form
        onSubmit={handleSubmit}
        className="bg-white bg-opacity-90 backdrop-blur-md rounded-3xl shadow-xl p-10 max-w-3xl w-full space-y-8"
      >
        {/* File upload with clear */}
        <div>
          <label
            htmlFor="cv-upload"
            className="flex items-center justify-center cursor-pointer border-2 border-dashed border-teal-500 rounded-2xl py-6 px-4 hover:bg-teal-50 transition-colors text-teal-700 font-semibold text-lg select-none"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-7 w-7 mr-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 4v16m8-8H4"
              />
            </svg>

            {cvFile ? (
              <>
                <span className="text-teal-800">{cvFile.name}</span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    clearFile();
                  }}
                  className="ml-4 bg-red-400 text-white rounded px-3 py-1 hover:bg-red-500 transition"
                >
                  Clear
                </button>
              </>
            ) : (
              "Click or drag your CV (PDF)"
            )}
          </label>
          <input
            id="cv-upload"
            type="file"
            accept=".pdf"
            onChange={(e) => setCvFile(e.target.files?.[0] || null)}
            className="hidden"
          />
        </div>

        {/* Job title and location inputs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label
              htmlFor="job-title"
              className="block text-gray-700 font-semibold mb-2"
            >
              Job Title
            </label>
            <input
              id="job-title"
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="Data Scientist"
              className="w-full rounded-xl border border-teal-400 px-4 py-3 text-lg placeholder-teal-300 focus:outline-none focus:ring-4 focus:ring-teal-300 transition-shadow shadow-md"
            />
          </div>

          <div>
            <label
              htmlFor="location"
              className="block text-gray-700 font-semibold mb-2"
            >
              Location (optional)
            </label>
            <input
              id="location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Remote or New York"
              className="w-full rounded-xl border border-teal-400 px-4 py-3 text-lg placeholder-teal-300 focus:outline-none focus:ring-4 focus:ring-teal-300 transition-shadow shadow-md"
            />
          </div>
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-teal-600 text-white py-4 rounded-xl font-bold text-xl shadow-lg hover:bg-teal-700 active:bg-teal-800 transition-colors flex justify-center items-center disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading && (
            <svg
              className="animate-spin h-6 w-6 mr-3 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              ></path>
            </svg>
          )}
          {loading ? "Searching..." : "Find Jobs"}
        </button>
      </form>

      {matches.length > 0 && (
        <section className="mt-12 max-w-3xl w-full">
          <h2 className="text-3xl font-extrabold text-teal-800 mb-6 text-center tracking-tight">
            Matched Jobs
          </h2>
          <ul className="space-y-8">
            {matches.map((job, idx) => (
              <li
                key={idx}
                className="p-6 rounded-2xl bg-gradient-to-br from-teal-50 to-amber-50 shadow-xl hover:shadow-2xl transition-shadow cursor-pointer"
              >
                <h3 className="text-2xl font-bold text-indigo-700">
                  {job.title}
                </h3>
                <p className="font-semibold text-amber-600">{job.company}</p>
                <p className="mt-3 text-indigo-900">{job.description}</p>
                {job.link && (
                  <a
                    href={job.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 inline-block text-indigo-700 font-semibold underline hover:text-indigo-900"
                  >
                    View Job
                  </a>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
