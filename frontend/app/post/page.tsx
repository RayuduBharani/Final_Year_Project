"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function PostJob() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    const authenticated = localStorage.getItem("hr_authenticated");
    if (authenticated !== "true") {
      router.push("/login");
    } else {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsAuthenticated(true);
    }
    setMounted(true);
  }, [router]);

  if (!mounted || !isAuthenticated) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-muted-foreground">Checking authentication...</p>
        </div>
      </main>
    );
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (
        droppedFile.type === "application/pdf" ||
        droppedFile.type === "application/msword" ||
        droppedFile.type ===
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      ) {
        setFile(droppedFile);
        setError(null);
      } else {
        setError("Please upload a PDF or Word document");
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobTitle.trim()) {
      setError("Please enter a job title");
      return;
    }
    if (!department.trim()) {
      setError("Please enter a department");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const token = localStorage.getItem("hr_token");
      
      const formData = new FormData();
      formData.append("title", jobTitle);
      formData.append("department", department);
      formData.append("description", description);
      formData.append("requirements", requirements);
      formData.append("status", "active");
      if (file) {
        formData.append("jd_file", file);
      }

      const response = await fetch("http://localhost:5000/api/jobs", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess("Job posted successfully! Students can now submit their resumes.");
        setFile(null);
        setJobTitle("");
        setDepartment("");
        setDescription("");
        setRequirements("");
      } else {
        setError(data.error || "Failed to post job");
      }
    } catch {
      setError("Failed to connect to server. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-background py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            📝 Post New Job
          </h1>
          <p className="text-muted-foreground text-lg">
            Create a new job posting and collect resumes from candidates
          </p>
        </div>

        {/* Navigation */}
        <div className="flex justify-center gap-4 mb-8">
          <Link
            href="/"
            className="bg-secondary hover:bg-accent text-secondary-foreground px-6 py-3 rounded-lg font-medium transition-colors"
          >
            💼 All Jobs
          </Link>
          <Link
            href="/post"
            className="bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium"
          >
            ➕ Post Job
          </Link>
          <Link
            href="/review"
            className="bg-secondary hover:bg-accent text-secondary-foreground px-6 py-3 rounded-lg font-medium transition-colors"
          >
            📊 Review Resumes
          </Link>
        </div>

        {/* Post Job Form */}
        <div className="bg-card rounded-2xl shadow-2xl p-8 border border-border">
          <form onSubmit={handleSubmit}>
            {/* Job Title */}
            <div className="mb-6">
              <label className="block text-foreground mb-2 font-medium">
                Job Title *
              </label>
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g., Senior Software Engineer"
                className="w-full bg-muted border border-input rounded-lg px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
              />
            </div>

            {/* Department */}
            <div className="mb-6">
              <label className="block text-foreground mb-2 font-medium">
                Department *
              </label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="e.g., Engineering"
                className="w-full bg-muted border border-input rounded-lg px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
              />
            </div>

            {/* Job Description */}
            <div className="mb-6">
              <label className="block text-foreground mb-2 font-medium">
                Job Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter a detailed job description..."
                rows={4}
                className="w-full bg-muted border border-input rounded-lg px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-colors resize-none"
              />
            </div>

            {/* Requirements */}
            <div className="mb-6">
              <label className="block text-foreground mb-2 font-medium">
                Required Skills (comma separated)
              </label>
              <input
                type="text"
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="e.g., React, TypeScript, Node.js, CSS"
                className="w-full bg-muted border border-input rounded-lg px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
              />
              {requirements && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {requirements.split(",").map((skill, idx) => (
                    skill.trim() && (
                      <span
                        key={idx}
                        className="bg-primary/20 text-primary px-3 py-1 rounded-full text-sm"
                      >
                        {skill.trim()}
                      </span>
                    )
                  ))}
                </div>
              )}
            </div>

            {/* Drag and Drop Zone */}
            <div className="mb-6">
              <label className="block text-foreground mb-2 font-medium">
                Job Description Document (Optional)
              </label>
              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
                  dragActive
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-muted-foreground"
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <div className="text-4xl mb-3">📁</div>
                <p className="text-muted-foreground mb-3 text-sm">
                  Drag and drop your JD file here, or
                </p>
                <label className="cursor-pointer">
                  <span className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-lg font-medium transition-colors text-sm">
                    Browse Files
                  </span>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
                <p className="text-muted-foreground text-xs mt-3">
                  Supports PDF, DOC, DOCX
                </p>
                {file && (
                  <div className="mt-4 p-3 bg-secondary rounded-lg inline-flex items-center gap-2">
                    <span className="text-xl">📎</span>
                    <span className="text-secondary-foreground text-sm">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => setFile(null)}
                      className="text-muted-foreground hover:text-destructive ml-2"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-4 bg-destructive/20 border border-destructive rounded-lg text-destructive text-sm">
                {error}
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="mb-4 p-4 bg-chart-1/20 border border-chart-1 rounded-lg text-chart-1 text-sm">
                {success}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-4 rounded-xl font-semibold text-lg transition-all duration-300 ${
                loading
                  ? "bg-muted text-muted-foreground cursor-not-allowed"
                  : "bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg hover:shadow-xl"
              }`}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-3">
                  <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Posting Job...
                </span>
              ) : (
                "🚀 Post Job"
              )}
            </button>
          </form>
        </div>

        {/* Tips Section */}
        <div className="mt-8 bg-card rounded-xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">💡 Tips for a Great Job Post</h3>
          <ul className="space-y-2 text-muted-foreground text-sm">
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              Be specific about required skills and experience level
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              Include key responsibilities and expectations
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              Upload a detailed JD document for better resume matching
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              List both required and preferred qualifications
            </li>
          </ul>
        </div>
      </div>
    </main>
  );
}
