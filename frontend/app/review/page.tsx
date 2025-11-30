"use client";

import { useState, useMemo, useEffect, useCallback } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";

interface Resume {
  id: string;
  _id?: string;
  studentName: string;
  student_name?: string;
  email: string;
  phone: string;
  college: string;
  degree: string;
  graduationYear: string;
  graduation_year?: string;
  skills: string[];
  experience: string;
  years_of_experience?: number;
  resumeUrl: string;
  resume_url?: string;
  submittedAt: string;
  submitted_at?: string;
  overallScore: number;
  overall_score?: number;
  skillMatchScore: number;
  skill_match_score?: number;
  experienceScore: number;
  experience_score?: number;
  educationScore: number;
  education_score?: number;
  keywordMatchScore?: number;
  keyword_match_score?: number;
  formattingScore?: number;
  formatting_score?: number;
  matchedKeywords?: string[];
  matched_keywords?: string[];
  missingKeywords?: string[];
  missing_keywords?: string[];
  matchedSkills?: string[];
  matched_skills?: string[];
  missingSkills?: string[];
  missing_skills?: string[];
  aiAnalysis?: string;
  ai_analysis?: string;
  status: "pending" | "shortlisted" | "rejected" | "interviewed";
}

interface Job {
  id: string;
  _id?: string;
  title: string;
  department: string;
  description: string;
  requirements: string[];
  location?: string;
  type?: string;
  applicants: number;
  applicant_count?: number;
  status: "active" | "closed";
  createdAt: string;
  created_at?: string;
}

export default function ReviewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job") || "";

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [sortBy, setSortBy] = useState<"score" | "date" | "name">("score");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  
  const [job, setJob] = useState<Job | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<Job[]>([]);

  const fetchApplications = useCallback(async (selectedJobId: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/applications?job_id=${selectedJobId}`);
      const data = await response.json();
      
      if (response.ok) {
        const transformedResumes: Resume[] = data.applications.map((app: Resume) => ({
          id: app._id || app.id,
          studentName: app.student_name || app.studentName,
          email: app.email,
          phone: app.phone,
          college: app.college || "",
          degree: app.degree || "",
          graduationYear: app.graduation_year || app.graduationYear || "",
          skills: app.skills || [],
          experience: app.experience || "",
          years_of_experience: app.years_of_experience || 0,
          resumeUrl: app.resume_url || app.resumeUrl || "#",
          submittedAt: app.submitted_at || app.submittedAt || new Date().toISOString(),
          overallScore: app.overall_score || app.overallScore || 0,
          skillMatchScore: app.skill_match_score || app.skillMatchScore || 0,
          experienceScore: app.experience_score || app.experienceScore || 0,
          educationScore: app.education_score || app.educationScore || 0,
          keywordMatchScore: app.keyword_match_score || app.keywordMatchScore || 0,
          formattingScore: app.formatting_score || app.formattingScore || 0,
          matchedKeywords: app.matched_keywords || app.matchedKeywords || [],
          missingKeywords: app.missing_keywords || app.missingKeywords || [],
          matchedSkills: app.matched_skills || app.matchedSkills || [],
          missingSkills: app.missing_skills || app.missingSkills || [],
          aiAnalysis: app.ai_analysis || app.aiAnalysis || "",
          status: app.status || "pending",
        }));
        setResumes(transformedResumes);
      }
    } catch (error) {
      console.error("Failed to fetch applications:", error);
    }
  }, []);

  useEffect(() => {
    const authenticated = localStorage.getItem("hr_authenticated");
    if (authenticated !== "true") {
      router.push("/login");
      return;
    }
    setIsAuthenticated(true);
    setMounted(true);

    // Fetch all jobs for the dropdown
    const fetchJobs = async () => {
      try {
        const response = await fetch("http://localhost:5000/api/jobs");
        const data = await response.json();
        
        if (response.ok) {
          const transformedJobs: Job[] = data.jobs.map((j: Job) => ({
            id: j._id || j.id,
            title: j.title,
            department: j.department,
            description: j.description,
            requirements: j.requirements || [],
            location: j.location || "India",
            type: j.type || "Full-time",
            applicants: j.applicant_count || j.applicants || 0,
            status: j.status,
            createdAt: j.created_at || j.createdAt,
          }));
          setJobs(transformedJobs);
          
          // Set current job
          const currentJobId = jobId || (transformedJobs.length > 0 ? transformedJobs[0].id : "");
          if (currentJobId) {
            const currentJob = transformedJobs.find((j: Job) => j.id === currentJobId);
            if (currentJob) {
              setJob(currentJob);
              await fetchApplications(currentJobId);
            }
          }
        }
      } catch (error) {
        console.error("Failed to fetch jobs:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, [router, jobId, fetchApplications]);

  const handleJobChange = async (newJobId: string) => {
    const selectedJob = jobs.find((j) => j.id === newJobId);
    if (selectedJob) {
      setJob(selectedJob);
      setSelectedResume(null);
      router.push(`/review?job=${newJobId}`);
      await fetchApplications(newJobId);
    }
  };

  const filteredResumes = useMemo(() => {
    return resumes
      .filter((resume) => {
        if (filterStatus !== "all" && resume.status !== filterStatus) return false;
        if (searchQuery) {
          const query = searchQuery.toLowerCase();
          return (
            resume.studentName.toLowerCase().includes(query) ||
            resume.email.toLowerCase().includes(query) ||
            resume.college.toLowerCase().includes(query) ||
            resume.skills.some((skill) => skill.toLowerCase().includes(query))
          );
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === "score") return b.overallScore - a.overallScore;
        if (sortBy === "date")
          return new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime();
        return a.studentName.localeCompare(b.studentName);
      });
  }, [resumes, filterStatus, searchQuery, sortBy]);

  const getScoreColor = (score: number) => {
    if (score >= 85) return "text-green-500";
    if (score >= 70) return "text-amber-500";
    return "text-red-500";
  };

  const getScoreBg = (score: number) => {
    if (score >= 85) return "bg-green-500/10 border-green-500/30";
    if (score >= 70) return "bg-amber-500/10 border-amber-500/30";
    return "bg-red-500/10 border-red-500/30";
  };

  const getStatusStyle = (status: string) => {
    switch (status) {
      case "shortlisted":
        return "bg-green-500/15 text-green-600 dark:text-green-400";
      case "rejected":
        return "bg-red-500/15 text-red-600 dark:text-red-400";
      case "interviewed":
        return "bg-blue-500/15 text-blue-600 dark:text-blue-400";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const [rescoring, setRescoring] = useState(false);

  const rescoreAllApplications = async () => {
    if (!job?.id) return;
    
    setRescoring(true);
    try {
      const token = localStorage.getItem("hr_token");
      const response = await fetch(`http://localhost:5000/api/jobs/${job.id}/rescore-all`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Successfully rescored ${data.rescored} applications with new ATS algorithm!`);
        // Refresh applications
        await fetchApplications(job.id);
      } else {
        alert("Failed to rescore applications");
      }
    } catch (error) {
      console.error("Failed to rescore:", error);
      alert("Error rescoring applications");
    } finally {
      setRescoring(false);
    }
  };

  const updateStatus = async (resumeId: string, newStatus: Resume["status"]) => {
    try {
      const token = localStorage.getItem("hr_token");
      const response = await fetch(`http://localhost:5000/api/applications/${resumeId}/status`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        setResumes((prev) =>
          prev.map((r) => (r.id === resumeId ? { ...r, status: newStatus } : r))
        );
        if (selectedResume?.id === resumeId) {
          setSelectedResume({ ...selectedResume, status: newStatus });
        }
      }
    } catch (error) {
      console.error("Failed to update status:", error);
    }
  };

  if (!mounted || !isAuthenticated) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </main>
    );
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading job data...</p>
        </div>
      </main>
    );
  }

  if (!job && jobs.length === 0) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">📋</div>
          <h1 className="text-2xl font-bold text-foreground mb-2">No Jobs Found</h1>
          <p className="text-muted-foreground mb-6">Create a job posting to start reviewing resumes.</p>
          <Link
            href="/post"
            className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-xl font-medium transition-colors"
          >
            Post a Job
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="bg-card border-b border-border sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/" className="flex items-center gap-2">
                <span className="text-2xl">💼</span>
                <span className="text-xl font-bold text-foreground">JobPortal</span>
              </Link>
              <div className="h-6 w-px bg-border"></div>
              <span className="text-muted-foreground">Resume Review</span>
            </div>
            <div className="flex items-center gap-4">
              {/* Job Selector */}
              <select
                value={job?.id || ""}
                onChange={(e) => handleJobChange(e.target.value)}
                className="bg-muted border border-input rounded-xl px-4 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring cursor-pointer"
              >
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} ({j.applicants} applicants)
                  </option>
                ))}
              </select>
              <Link
                href="/"
                className="text-muted-foreground hover:text-foreground transition-colors text-sm flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Jobs
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Filters */}
        <div className="bg-card rounded-2xl p-4 border border-border mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <svg
                className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search candidates by name, email, or skills..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-muted border border-input rounded-xl pl-12 pr-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-muted border border-input rounded-xl px-4 py-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring cursor-pointer"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="shortlisted">Shortlisted</option>
              <option value="interviewed">Interviewed</option>
              <option value="rejected">Rejected</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as "score" | "date" | "name")}
              className="bg-muted border border-input rounded-xl px-4 py-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring cursor-pointer"
            >
              <option value="score">Highest Score</option>
              <option value="date">Latest First</option>
              <option value="name">Name A-Z</option>
            </select>
          </div>
        </div>

        {/* Results Count */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-muted-foreground text-sm">
            Showing <span className="text-foreground font-medium">{filteredResumes.length}</span> of {resumes.length} candidates
          </p>
          <button
            onClick={rescoreAllApplications}
            disabled={rescoring || resumes.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {rescoring ? (
              <>
                <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                Rescoring...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Rescore All with ATS
              </>
            )}
          </button>
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-5 gap-6">
          {/* Resume List */}
          <div className="lg:col-span-3 space-y-3">
            {filteredResumes.length === 0 ? (
              <div className="bg-card rounded-2xl p-12 text-center border border-border">
                <div className="text-5xl mb-4">🔍</div>
                <h3 className="text-lg font-semibold text-foreground mb-2">No candidates found</h3>
                <p className="text-muted-foreground text-sm">Try adjusting your search or filters</p>
              </div>
            ) : (
              filteredResumes.map((resume, index) => (
                <div
                  key={resume.id}
                  onClick={() => setSelectedResume(resume)}
                  className={`bg-card rounded-2xl p-5 border cursor-pointer transition-all duration-200 ${
                    selectedResume?.id === resume.id
                      ? "border-primary shadow-lg ring-1 ring-primary/20"
                      : "border-border hover:border-primary/50 hover:shadow-md"
                  }`}
                >
                  <div className="flex items-start gap-4">
                    {/* Rank */}
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shrink-0 ${
                        index === 0
                          ? "bg-amber-400 text-amber-950"
                          : index === 1
                          ? "bg-slate-300 text-slate-800"
                          : index === 2
                          ? "bg-amber-600 text-amber-50"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      #{index + 1}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="font-semibold text-foreground">{resume.studentName}</h3>
                          <p className="text-muted-foreground text-sm">{resume.college}</p>
                          <p className="text-muted-foreground/70 text-xs mt-0.5">
                            {resume.degree} • Class of {resume.graduationYear}
                          </p>
                        </div>
                        {/* Score */}
                        <div className={`w-14 h-14 rounded-xl border-2 flex items-center justify-center shrink-0 ${getScoreBg(resume.overallScore)}`}>
                          <span className={`text-lg font-bold ${getScoreColor(resume.overallScore)}`}>
                            {resume.overallScore}
                          </span>
                        </div>
                      </div>

                      {/* Skills */}
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {resume.skills.slice(0, 4).map((skill, idx) => {
                          const isMatch = job?.requirements?.some(
                            (r) => r.toLowerCase() === skill.toLowerCase()
                          ) || false;
                          return (
                            <span
                              key={idx}
                              className={`px-2 py-0.5 rounded text-xs ${
                                isMatch
                                  ? "bg-green-500/15 text-green-600 dark:text-green-400"
                                  : "bg-secondary text-secondary-foreground"
                              }`}
                            >
                              {skill}
                            </span>
                          );
                        })}
                        {resume.skills.length > 4 && (
                          <span className="text-muted-foreground text-xs px-1">
                            +{resume.skills.length - 4}
                          </span>
                        )}
                      </div>

                      {/* Meta */}
                      <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                            {resume.years_of_experience || 0} yrs
                          </span>
                          <span className="flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            {new Date(resume.submittedAt).toLocaleDateString()}
                          </span>
                        </div>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${getStatusStyle(resume.status)}`}>
                          {resume.status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Detail Panel */}
          <div className="lg:col-span-2">
            <div className="sticky top-24">
              {selectedResume ? (
                <div className="bg-card rounded-2xl border border-border overflow-hidden">
                  {/* Header */}
                  <div className="bg-gradient-to-br from-primary/10 to-primary/5 p-6 text-center">
                    <div className={`w-20 h-20 rounded-2xl border-4 flex items-center justify-center mx-auto mb-4 ${getScoreBg(selectedResume.overallScore)}`}>
                      <span className={`text-3xl font-bold ${getScoreColor(selectedResume.overallScore)}`}>
                        {selectedResume.overallScore}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-foreground">{selectedResume.studentName}</h3>
                    <p className="text-muted-foreground text-sm">{selectedResume.college}</p>
                    <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium capitalize ${getStatusStyle(selectedResume.status)}`}>
                      {selectedResume.status}
                    </span>
                  </div>

                  <div className="p-6 space-y-6">
                    {/* Score Breakdown */}
                    <div>
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                        ATS Score Breakdown
                      </h4>
                      <div className="space-y-3">
                        {[
                          { label: "Keyword Match", score: selectedResume.keywordMatchScore || 0, color: "bg-purple-500" },
                          { label: "Skill Match", score: selectedResume.skillMatchScore, color: "bg-primary" },
                          { label: "Experience", score: selectedResume.experienceScore, color: "bg-blue-500" },
                          { label: "Education", score: selectedResume.educationScore, color: "bg-green-500" },
                          { label: "Resume Format", score: selectedResume.formattingScore || 0, color: "bg-orange-500" },
                        ].map((item) => (
                          <div key={item.label}>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-muted-foreground">{item.label}</span>
                              <span className="font-medium text-foreground">{item.score}%</span>
                            </div>
                            <div className="h-2 bg-secondary rounded-full overflow-hidden">
                              <div
                                className={`h-full ${item.color} rounded-full transition-all duration-500`}
                                style={{ width: `${item.score}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Matched Skills */}
                    {selectedResume.matchedSkills && selectedResume.matchedSkills.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-green-600 uppercase tracking-wider mb-2">
                          ✓ Matched Skills
                        </h4>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedResume.matchedSkills.slice(0, 10).map((skill, idx) => (
                            <span key={idx} className="px-2 py-0.5 rounded text-xs bg-green-500/15 text-green-600 dark:text-green-400">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Missing Skills */}
                    {selectedResume.missingSkills && selectedResume.missingSkills.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-red-600 uppercase tracking-wider mb-2">
                          ✗ Missing Skills
                        </h4>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedResume.missingSkills.slice(0, 8).map((skill, idx) => (
                            <span key={idx} className="px-2 py-0.5 rounded text-xs bg-red-500/15 text-red-600 dark:text-red-400">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* AI Analysis */}
                    {selectedResume.aiAnalysis && (
                      <div className="bg-muted/50 rounded-xl p-4">
                        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                          🤖 AI Analysis
                        </h4>
                        <p className="text-sm text-foreground whitespace-pre-line">
                          {selectedResume.aiAnalysis}
                        </p>
                      </div>
                    )}

                    {/* Contact */}
                    <div className="bg-muted/50 rounded-xl p-4">
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                        Contact
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p className="flex items-center gap-2 text-foreground">
                          <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                          {selectedResume.email}
                        </p>
                        <p className="flex items-center gap-2 text-foreground">
                          <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                          </svg>
                          {selectedResume.phone}
                        </p>
                      </div>
                    </div>

                    {/* Details */}
                    <div>
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                        Details
                      </h4>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <p className="text-muted-foreground text-xs">Degree</p>
                          <p className="text-foreground font-medium">{selectedResume.degree}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground text-xs">Graduation</p>
                          <p className="text-foreground font-medium">{selectedResume.graduationYear}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground text-xs">Experience</p>
                          <p className="text-foreground font-medium">{selectedResume.experience} years</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground text-xs">Applied</p>
                          <p className="text-foreground font-medium">{selectedResume.submittedAt}</p>
                        </div>
                      </div>
                    </div>

                    {/* Skills */}
                    <div>
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                        Skills
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedResume.skills.map((skill, idx) => {
                          const isMatch = job?.requirements?.some(
                            (r) => r.toLowerCase() === skill.toLowerCase()
                          ) || false;
                          return (
                            <span
                              key={idx}
                              className={`px-2.5 py-1 rounded-lg text-xs font-medium ${
                                isMatch
                                  ? "bg-green-500/15 text-green-600 dark:text-green-400 border border-green-500/30"
                                  : "bg-secondary text-secondary-foreground"
                              }`}
                            >
                              {skill}
                              {isMatch && " ✓"}
                            </span>
                          );
                        })}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="space-y-2 pt-2">
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => updateStatus(selectedResume.id, "shortlisted")}
                          className={`py-2.5 rounded-xl font-medium text-sm transition-colors ${
                            selectedResume.status === "shortlisted"
                              ? "bg-green-500 text-white"
                              : "bg-green-500/15 text-green-600 hover:bg-green-500/25"
                          }`}
                        >
                          Shortlist
                        </button>
                        <button
                          onClick={() => updateStatus(selectedResume.id, "interviewed")}
                          className={`py-2.5 rounded-xl font-medium text-sm transition-colors ${
                            selectedResume.status === "interviewed"
                              ? "bg-blue-500 text-white"
                              : "bg-blue-500/15 text-blue-600 hover:bg-blue-500/25"
                          }`}
                        >
                          Interview
                        </button>
                      </div>
                      <button
                        onClick={() => updateStatus(selectedResume.id, "rejected")}
                        className={`w-full py-2.5 rounded-xl font-medium text-sm transition-colors ${
                          selectedResume.status === "rejected"
                            ? "bg-red-500 text-white"
                            : "bg-red-500/15 text-red-600 hover:bg-red-500/25"
                        }`}
                      >
                        Reject
                      </button>
                      <a
                        href={selectedResume.resumeUrl}
                        className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl font-medium text-sm transition-colors flex items-center justify-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Download Resume
                      </a>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-card rounded-2xl p-12 text-center border border-border">
                  <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">Select a Candidate</h3>
                  <p className="text-muted-foreground text-sm">
                    Click on a candidate to view their detailed profile and take actions
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
