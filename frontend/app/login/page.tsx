"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function HRLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim()) {
      setError("Please enter your email");
      return;
    }
    if (!password.trim()) {
      setError("Please enter your password");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("http://localhost:5000/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("hr_authenticated", "true");
        localStorage.setItem("hr_token", data.token);
        localStorage.setItem("hr_user", JSON.stringify(data.user));
        router.push("/");
      } else {
        setError(data.error || "Invalid email or password");
      }
    } catch {
      setError("Failed to connect to server. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-background flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">👔</div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            HR Portal Login
          </h1>
          <p className="text-muted-foreground">
            Sign in to manage job postings and review resumes
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-card rounded-2xl p-8 border border-border shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Field */}
            <div>
              <label className="block text-foreground mb-2 font-medium">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground">
                  📧
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="hr@company.com"
                  className="w-full bg-muted border border-input rounded-lg pl-12 pr-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-foreground mb-2 font-medium">
                Password
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground">
                  🔒
                </span>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full bg-muted border border-input rounded-lg pl-12 pr-12 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-input bg-muted text-primary focus:ring-ring"
                />
                <span className="text-muted-foreground">Remember me</span>
              </label>
              <button
                type="button"
                className="text-primary hover:underline"
              >
                Forgot password?
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-4 bg-destructive/20 border border-destructive rounded-lg text-destructive text-sm flex items-center gap-2">
                <span>⚠️</span>
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3 rounded-lg font-semibold transition-all text-lg ${
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
                  Signing in...
                </span>
              ) : (
                "🔐 Sign In"
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-4">
            <div className="flex-1 h-px bg-border"></div>
            <span className="text-muted-foreground text-sm">or</span>
            <div className="flex-1 h-px bg-border"></div>
          </div>

          {/* Alternative Actions */}
          <div className="space-y-3">
            <button className="w-full py-3 rounded-lg font-medium border border-border bg-secondary hover:bg-accent text-secondary-foreground transition-colors flex items-center justify-center gap-2">
              <span>🔗</span> Sign in with SSO
            </button>
          </div>
        </div>

        {/* Demo Credentials */}
        <div className="mt-6 p-4 bg-card rounded-xl border border-border">
          <p className="text-muted-foreground text-sm text-center mb-2">
            <span className="text-foreground font-medium">Demo Credentials:</span>
          </p>
          <div className="flex justify-center gap-4 text-sm">
            <code className="bg-muted px-2 py-1 rounded text-foreground">hr@company.com</code>
            <code className="bg-muted px-2 py-1 rounded text-foreground">hr123</code>
          </div>
        </div>

        {/* Back to Jobs Link */}
        <div className="mt-6 text-center">
          <Link
            href="/"
            className="text-muted-foreground hover:text-foreground transition-colors text-sm"
          >
            ← Back to job listings
          </Link>
        </div>
      </div>
    </main>
  );
}
