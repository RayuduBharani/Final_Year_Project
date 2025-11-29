"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface Job {
  id: string;
  _id?: string;
  title: string;
  department: string;
  description: string;
  requirements: string[];
  responsibilities?: string[];
  location?: string;
  type?: string;
  experience?: string;
  salary?: string;
  createdAt: string;
  created_at?: string;
  deadline?: string;
  status: "active" | "closed";
  applicants: number;
  applicant_count?: number;
}

export default function JobApplyPage() {
  const params = useParams();
  const jobId = params.id as string;
  
  const [job, setJob] = useState<Job | null>(null);
  const [jobLoading, setJobLoading] = useState(true);
  const [jobError, setJobError] = useState<string | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [college, setCollege] = useState("");
  const [degree, setDegree] = useState("");
  const [graduationYear, setGraduationYear] = useState("");
  const [experience, setExperience] = useState("");
  const [coverLetter, setCoverLetter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/jobs/${jobId}`);
        const data = await response.json();
        
        if (response.ok) {
          const jobData: Job = {
            id: data.job._id || data.job.id,
            title: data.job.title,
            department: data.job.department,
            description: data.job.description,
            requirements: data.job.requirements || [],
            responsibilities: data.job.responsibilities || [],
            location: data.job.location || "India",
            type: data.job.type || "Full-time",
            experience: data.job.experience || "Not specified",
            salary: data.job.salary || "Competitive",
            createdAt: data.job.created_at || data.job.createdAt,
            deadline: data.job.deadline,
            status: data.job.status,
            applicants: data.job.applicant_count || 0,
          };
          setJob(jobData);
        } else {
          setJobError(data.error || "Job not found");
        }
      } catch {
        setJobError("Failed to fetch job details");
      } finally {
        setJobLoading(false);
      }
    };

    fetchJob();
  }, [jobId]);

  if (jobLoading) {
    return (
      <main className="min-h-screen bg-background py-12 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="text-6xl mb-4 animate-pulse">💼</div>
          <h1 className="text-2xl font-bold text-foreground mb-4">Loading Job Details...</h1>
          <p className="text-muted-foreground">Please wait while we fetch the job information.</p>
        </div>
      </main>
    );
  }

  if (jobError || !job) {
    return (
      <main className="min-h-screen bg-background py-12 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="text-6xl mb-4">😕</div>
          <h1 className="text-2xl font-bold text-foreground mb-4">Job Not Found</h1>
          <p className="text-muted-foreground mb-6">
            {jobError || "The job you're looking for doesn't exist or has been removed."}
          </p>
          <Link
            href="/"
            className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-lg font-medium transition-colors inline-block"
          >
            ← Back to Jobs
          </Link>
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
    
    if (!fullName.trim()) {
      setError("Please enter your full name");
      return;
    }
    if (!email.trim()) {
      setError("Please enter your email");
      return;
    }
    if (!phone.trim()) {
      setError("Please enter your phone number");
      return;
    }
    if (!file) {
      setError("Please upload your resume");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("student_name", fullName);
      formData.append("email", email);
      formData.append("phone", phone);
      formData.append("college", college);
      formData.append("degree", degree);
      formData.append("graduation_year", graduationYear);
      formData.append("experience", experience);
      formData.append("cover_letter", coverLetter);
      formData.append("resume", file);

      const response = await fetch(`http://localhost:5000/api/jobs/${jobId}/apply`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
      } else {
        setError(data.error || "Failed to submit application");
      }
    } catch {
      setError("Failed to connect to server. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <main className="min-h-screen bg-background py-12 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="bg-card rounded-2xl p-12 border border-border">
            <div className="text-6xl mb-6">🎉</div>
            <h1 className="text-3xl font-bold text-foreground mb-4">
              Application Submitted!
            </h1>
            <p className="text-muted-foreground mb-2">
              Thank you for applying to <span className="text-foreground font-medium">{job.title}</span>
            </p>
            <p className="text-muted-foreground mb-8">
              We&apos;ve received your application and will review it shortly. You&apos;ll hear from us soon!
            </p>
            <div className="flex justify-center gap-4">
              <Link
                href="/"
                className="bg-secondary hover:bg-accent text-secondary-foreground px-6 py-3 rounded-lg font-medium transition-colors"
              >
                ← Browse More Jobs
              </Link>
            </div>
          </div>
        </div>
      </main>
    );
  }

  const isDeadlinePassed = job.deadline ? new Date(job.deadline) < new Date() : false;

  return (
    <main className="min-h-screen bg-background py-12 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Back Button */}
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors"
        >
          ← Back to all jobs
        </Link>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Job Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header */}
            <div className="bg-card rounded-2xl p-8 border border-border">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-3xl font-bold text-foreground mb-2">
                    {job.title}
                  </h1>
                  <p className="text-muted-foreground text-lg">{job.department}</p>
                </div>
                <span
                  className={`px-4 py-2 rounded-full text-sm font-medium ${
                    job.status === "active"
                      ? "bg-chart-1/20 text-chart-1"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {job.status === "active" ? "🟢 Active" : "🔴 Closed"}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-secondary rounded-lg p-3">
                  <p className="text-muted-foreground text-xs">📍 Location</p>
                  <p className="text-foreground font-medium text-sm">{job.location}</p>
                </div>
                <div className="bg-secondary rounded-lg p-3">
                  <p className="text-muted-foreground text-xs">💼 Type</p>
                  <p className="text-foreground font-medium text-sm">{job.type}</p>
                </div>
                <div className="bg-secondary rounded-lg p-3">
                  <p className="text-muted-foreground text-xs">📅 Experience</p>
                  <p className="text-foreground font-medium text-sm">{job.experience}</p>
                </div>
                <div className="bg-secondary rounded-lg p-3">
                  <p className="text-muted-foreground text-xs">💰 Salary</p>
                  <p className="text-foreground font-medium text-sm">{job.salary}</p>
                </div>
              </div>

              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>📅 Posted: {job.createdAt}</span>
                <span>⏰ Deadline: {job.deadline}</span>
                <span>👥 {job.applicants} applicants</span>
              </div>
            </div>

            {/* Description */}
            <div className="bg-card rounded-2xl p-8 border border-border">
              <h2 className="text-xl font-bold text-foreground mb-4">About the Role</h2>
              <p className="text-muted-foreground leading-relaxed">{job.description}</p>
            </div>

            {/* Requirements */}
            <div className="bg-card rounded-2xl p-8 border border-border">
              <h2 className="text-xl font-bold text-foreground mb-4">Requirements</h2>
              <div className="flex flex-wrap gap-2">
                {job.requirements.map((req, idx) => (
                  <span
                    key={idx}
                    className="bg-primary/20 text-primary px-3 py-2 rounded-lg text-sm"
                  >
                    {req}
                  </span>
                ))}
              </div>
            </div>

            {/* Responsibilities */}
            {job.responsibilities && job.responsibilities.length > 0 && (
              <div className="bg-card rounded-2xl p-8 border border-border">
                <h2 className="text-xl font-bold text-foreground mb-4">Responsibilities</h2>
                <ul className="space-y-3">
                  {job.responsibilities.map((resp, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                      <span className="text-primary mt-1">✓</span>
                      {resp}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Application Form */}
          <div className="lg:col-span-1">
            <div className="bg-card rounded-2xl p-6 border border-border sticky top-8">
              <h2 className="text-xl font-bold text-foreground mb-6">Apply Now</h2>

              {job.status === "closed" || isDeadlinePassed ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">🚫</div>
                  <p className="text-muted-foreground">
                    {job.status === "closed" 
                      ? "This position is no longer accepting applications." 
                      : "The application deadline has passed."}
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Full Name */}
                  <div>
                    <label className="block text-foreground mb-1 text-sm font-medium">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="John Doe"
                      className="w-full bg-muted border border-input rounded-lg px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-foreground mb-1 text-sm font-medium">
                      Email *
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="john@example.com"
                      className="w-full bg-muted border border-input rounded-lg px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                    />
                  </div>

                  {/* Phone */}
                  <div>
                    <label className="block text-foreground mb-1 text-sm font-medium">
                      Phone Number *
                    </label>
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+91 98765 43210"
                      className="w-full bg-muted border border-input rounded-lg px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                    />
                  </div>

                  {/* College */}
                  <div>
                    <label className="block text-foreground mb-1 text-sm font-medium">
                      College/University
                    </label>
                    <input
                      type="text"
                      value={college}
                      onChange={(e) => setCollege(e.target.value)}
                      placeholder="IIT Delhi"
                      className="w-full bg-muted border border-input rounded-lg px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                    />
                  </div>

                  {/* Degree & Graduation Year */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-foreground mb-1 text-sm font-medium">
                        Degree
                      </label>
                      <input
                        type="text"
                        value={degree}
                        onChange={(e) => setDegree(e.target.value)}
                        placeholder="B.Tech CSE"
                        className="w-full bg-muted border border-input rounded-lg px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-foreground mb-1 text-sm font-medium">
                        Grad Year
                      </label>
                      <input
                        type="text"
                        value={graduationYear}
                        onChange={(e) => setGraduationYear(e.target.value)}
                        placeholder="2025"
                        className="w-full bg-muted border border-input rounded-lg px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                      />
                    </div>
                  </div>

                  {/* Experience */}
                  <div>
                    <label className="block text-foreground mb-1 text-sm font-medium">
                      Years of Experience
                    </label>
                    <select
                      value={experience}
                      onChange={(e) => setExperience(e.target.value)}
                      className="w-full bg-muted border border-input rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                    >
                      <option value="">Select</option>
                      <option value="0">Fresher (0 years)</option>
                      <option value="1">1 year</option>
                      <option value="2">2 years</option>
                      <option value="3">3 years</option>
                      <option value="4">4 years</option>
                      <option value="5+">5+ years</option>
                    </select>
                  </div>

                  {/* Resume Upload */}
                  <div>
                    <label className="block text-foreground mb-1 text-sm font-medium">
                      Resume *
                    </label>
                    <div
                      className={`border-2 border-dashed rounded-lg p-4 text-center transition-all ${
                        dragActive
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-muted-foreground"
                      }`}
                      onDragEnter={handleDrag}
                      onDragLeave={handleDrag}
                      onDragOver={handleDrag}
                      onDrop={handleDrop}
                    >
                      <div className="text-2xl mb-2">📄</div>
                      <p className="text-muted-foreground text-xs mb-2">
                        Drop your resume here or
                      </p>
                      <label className="cursor-pointer">
                        <span className="bg-primary hover:bg-primary/90 text-primary-foreground px-3 py-1 rounded-lg font-medium transition-colors text-xs">
                          Browse
                        </span>
                        <input
                          type="file"
                          accept=".pdf,.doc,.docx"
                          onChange={handleFileChange}
                          className="hidden"
                        />
                      </label>
                      {file && (
                        <div className="mt-3 p-2 bg-secondary rounded-lg inline-flex items-center gap-2 text-xs">
                          <span>📎</span>
                          <span className="text-secondary-foreground truncate max-w-[150px]">
                            {file.name}
                          </span>
                          <button
                            type="button"
                            onClick={() => setFile(null)}
                            className="text-muted-foreground hover:text-destructive"
                          >
                            ✕
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Cover Letter */}
                  <div>
                    <label className="block text-foreground mb-1 text-sm font-medium">
                      Cover Letter (Optional)
                    </label>
                    <textarea
                      value={coverLetter}
                      onChange={(e) => setCoverLetter(e.target.value)}
                      placeholder="Tell us why you're a great fit..."
                      rows={3}
                      className="w-full bg-muted border border-input rounded-lg px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm resize-none"
                    />
                  </div>

                  {/* Error Message */}
                  {error && (
                    <div className="p-3 bg-destructive/20 border border-destructive rounded-lg text-destructive text-xs">
                      {error}
                    </div>
                  )}

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={loading}
                    className={`w-full py-3 rounded-lg font-semibold transition-all ${
                      loading
                        ? "bg-muted text-muted-foreground cursor-not-allowed"
                        : "bg-primary hover:bg-primary/90 text-primary-foreground"
                    }`}
                  >
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
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
                        Submitting...
                      </span>
                    ) : (
                      "🚀 Submit Application"
                    )}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
