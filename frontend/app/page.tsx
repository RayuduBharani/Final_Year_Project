"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Job {
  id: string;
  _id?: string;
  title: string;
  department: string;
  description: string;
  requirements: string[];
  createdAt: string;
  created_at?: string;
  status: "active" | "closed";
  applicants: number;
  applicant_count?: number;
}

export default function Home() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "closed">("all");
  const [isHRLoggedIn, setIsHRLoggedIn] = useState(false);
  const [hrUser, setHrUser] = useState<{ name: string; email: string } | null>(null);
  const [mounted, setMounted] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if HR is logged in on mount
    const authenticated = localStorage.getItem("hr_authenticated");
    const userData = localStorage.getItem("hr_user");
    setIsHRLoggedIn(authenticated === "true" && !!userData);
    setHrUser(userData ? JSON.parse(userData) : null);
    setMounted(true);

    // Fetch jobs from API
    const fetchJobs = async () => {
      try {
        const response = await fetch("http://localhost:5000/api/jobs");
        const data = await response.json();
        if (response.ok) {
          // Transform API response to match frontend interface
          const transformedJobs: Job[] = data.jobs.map((job: Job) => ({
            id: job._id || job.id,
            title: job.title,
            department: job.department,
            description: job.description,
            requirements: job.requirements || [],
            createdAt: job.created_at || job.createdAt,
            status: job.status,
            applicants: job.applicant_count || job.applicants || 0,
          }));
          setJobs(transformedJobs);
        }
      } catch (error) {
        console.error("Failed to fetch jobs:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("hr_authenticated");
    localStorage.removeItem("hr_token");
    localStorage.removeItem("hr_user");
    setIsHRLoggedIn(false);
    setHrUser(null);
    router.refresh();
  };

  // Filter jobs based on search and status
  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const matchesSearch =
        job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.requirements.some((req) =>
          req.toLowerCase().includes(searchQuery.toLowerCase())
        );
      const matchesStatus = filterStatus === "all" || job.status === filterStatus;
      return matchesSearch && matchesStatus;
    });
  }, [jobs, searchQuery, filterStatus]);

  // Avoid hydration mismatch
  if (!mounted) {
    return null;
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Top Navigation Bar */}
      <nav className="bg-card border-b border-border sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-2xl">💼</span>
              <span className="text-xl font-bold text-foreground">JobPortal</span>
            </Link>
            
            <div className="flex items-center gap-3">
              {isHRLoggedIn ? (
                <>
                  <Link
                    href="/post"
                    className="text-muted-foreground hover:text-foreground px-4 py-2 rounded-lg transition-colors text-sm font-medium"
                  >
                    Post Job
                  </Link>
                  <Link
                    href="/review"
                    className="text-muted-foreground hover:text-foreground px-4 py-2 rounded-lg transition-colors text-sm font-medium"
                  >
                    Review Resumes
                  </Link>
                  <div className="h-6 w-px bg-border mx-2"></div>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                      <span className="text-primary text-sm font-medium">
                        {hrUser?.name?.charAt(0) || "H"}
                      </span>
                    </div>
                    <span className="text-foreground text-sm font-medium hidden sm:block">
                      {hrUser?.name}
                    </span>
                    <button
                      onClick={handleLogout}
                      className="text-muted-foreground hover:text-destructive px-3 py-2 rounded-lg transition-colors text-sm"
                    >
                      Logout
                    </button>
                  </div>
                </>
              ) : (
                <Link
                  href="/login"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground px-5 py-2 rounded-lg font-medium transition-colors text-sm"
                >
                  HR Login
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-10">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4 tracking-tight">
            {isHRLoggedIn ? "Manage Your Jobs" : "Find Your Dream Job"}
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            {isHRLoggedIn 
              ? "Review applications, manage postings, and find the perfect candidates for your team."
              : "Discover exciting opportunities from top companies. Your next career move starts here."}
          </p>
        </div>

        {/* Search Section */}
        <div className="bg-card rounded-2xl p-6 mb-8 border border-border shadow-sm">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <svg
                className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <input
                type="text"
                placeholder="Search by job title, department, or skills..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-muted border border-input rounded-xl pl-12 pr-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as "all" | "active" | "closed")}
              className="bg-muted border border-input rounded-xl px-4 py-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring cursor-pointer min-w-[140px]"
            >
              <option value="all">All Jobs</option>
              <option value="active">Active Only</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>

        {/* Results Header */}
        <div className="flex items-center justify-between mb-6">
          <p className="text-muted-foreground">
            Showing <span className="text-foreground font-semibold">{filteredJobs.length}</span> job{filteredJobs.length !== 1 ? "s" : ""}
          </p>
          {isHRLoggedIn && (
            <Link
              href="/post"
              className="bg-primary hover:bg-primary/90 text-primary-foreground px-5 py-2.5 rounded-xl font-medium transition-colors text-sm flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Job
            </Link>
          )}
        </div>

        {/* Jobs Grid */}
        {loading ? (
          <div className="text-center py-16 bg-card rounded-2xl border border-border">
            <div className="text-6xl mb-4 animate-pulse">💼</div>
            <h3 className="text-xl font-semibold text-foreground mb-2">Loading jobs...</h3>
            <p className="text-muted-foreground">Please wait while we fetch the latest opportunities.</p>
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="text-center py-16 bg-card rounded-2xl border border-border">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-foreground mb-2">No jobs found</h3>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              {searchQuery || filterStatus !== "all"
                ? "Try adjusting your search or filters to find what you're looking for."
                : "No job postings available at the moment. Check back soon!"}
            </p>
            {isHRLoggedIn && (
              <Link
                href="/post"
                className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-xl font-medium transition-colors inline-flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Post Your First Job
              </Link>
            )}
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredJobs.map((job) => (
              <div
                key={job.id}
                className="bg-card rounded-2xl p-6 border border-border hover:border-primary/50 hover:shadow-lg transition-all duration-200 group"
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
                  <div className="flex-1">
                    <div className="flex items-start gap-4 mb-3">
                      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <span className="text-xl">
                          {job.department === "Engineering" && "💻"}
                          {job.department === "Analytics" && "📊"}
                          {job.department === "Product" && "🎯"}
                          {job.department === "Design" && "🎨"}
                          {!["Engineering", "Analytics", "Product", "Design"].includes(job.department) && "💼"}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 flex-wrap">
                          <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                            {job.title}
                          </h3>
                          <span
                            className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                              job.status === "active"
                                ? "bg-green-500/15 text-green-600 dark:text-green-400"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {job.status === "active" ? "● Active" : "Closed"}
                          </span>
                        </div>
                        <p className="text-muted-foreground text-sm mt-0.5">{job.department}</p>
                      </div>
                    </div>
                    
                    <p className="text-muted-foreground text-sm mb-4 line-clamp-2 leading-relaxed">
                      {job.description}
                    </p>
                    
                    <div className="flex flex-wrap gap-2 mb-4">
                      {job.requirements.slice(0, 4).map((req, idx) => (
                        <span
                          key={idx}
                          className="bg-secondary text-secondary-foreground px-3 py-1 rounded-full text-xs font-medium"
                        >
                          {req}
                        </span>
                      ))}
                      {job.requirements.length > 4 && (
                        <span className="text-muted-foreground text-xs px-2 py-1">
                          +{job.requirements.length - 4} more
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1.5">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {job.createdAt}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        {job.applicants} applicants
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex flex-row lg:flex-col gap-2 lg:min-w-[160px]">
                    {!isHRLoggedIn && (
                      <Link
                        href={`/${job.id}`}
                        className="flex-1 lg:flex-none text-center bg-primary hover:bg-primary/90 text-primary-foreground py-2.5 px-5 rounded-xl font-medium transition-colors text-sm"
                      >
                        Apply Now
                      </Link>
                    )}
                    {isHRLoggedIn && (
                      <>
                        <Link
                          href={`/review?job=${job.id}`}
                          className="flex-1 lg:flex-none text-center bg-primary hover:bg-primary/90 text-primary-foreground py-2.5 px-5 rounded-xl font-medium transition-colors text-sm"
                        >
                          View Resumes
                        </Link>
                        <button className="flex-1 lg:flex-none text-center bg-secondary hover:bg-accent text-secondary-foreground py-2.5 px-5 rounded-xl font-medium transition-colors text-sm border border-border">
                          Edit
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
