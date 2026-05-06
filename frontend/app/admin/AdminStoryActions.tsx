"use client";

import { useState } from "react";
import { Story } from "../types";
import { Check, X, RefreshCw, CheckCircle2 } from "lucide-react";
import { useRouter } from "next/navigation";

export default function AdminStoryActions({ story }: { story: Story }) {
  const [isRejecting, setIsRejecting] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "info" } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  if (story.status !== "pending_approval") {
    return (
      <div className="mt-12 p-8 rounded-2xl bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-center">
        <p className="font-semibold text-lg">
          Status:{" "}
          <span className="uppercase text-terracotta">
            {story.status.replace(/_/g, " ")}
          </span>
        </p>
      </div>
    );
  }

  const handleApprove = async () => {
    if (isSubmitting) return; // prevent double-click
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/admin/approve/${story.run_id}`, {
        method: "POST",
      });
      // ✅ FIX 1: Check res.ok — fetch() does NOT throw on non-2xx
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail || `Server error: ${res.status}`);
      }
      setMessage({ text: "✓ Story approved and published!", type: "success" });
      // ✅ FIX 2: Wait for message to show, THEN navigate — no race condition
      setTimeout(() => {
        router.push("/admin");
        // refresh() on the destination, not before push
        router.refresh();
      }, 1500);
    } catch (e: any) {
      setError(e.message || "Failed to approve. Is the backend running?");
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!feedback.trim()) return alert("Please provide feedback");
    if (isSubmitting) return; // prevent double-click
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/admin/reject/${story.run_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback }),
      });
      // ✅ FIX 1: Check res.ok
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail || `Server error: ${res.status}`);
      }
      setMessage({ text: "↺ Story rejected. AI is regenerating...", type: "info" });
      setFeedback("");
      setIsRejecting(false);
      // ✅ FIX 2: Navigate AFTER showing message
      setTimeout(() => {
        router.push("/admin");
        router.refresh();
      }, 1500);
    } catch (e: any) {
      setError(e.message || "Failed to reject. Is the backend running?");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mt-12 p-8 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-lg">
      <h3 className="text-xl font-bold mb-6">Admin Actions</h3>

      {/* Success / Info message */}
      {message && (
        <div
          className={`mb-6 p-4 rounded-xl text-center font-bold flex items-center justify-center gap-2 ${message.type === "success"
              ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
              : "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
            }`}
        >
          <CheckCircle2 className="w-5 h-5" />
          {message.text}
        </div>
      )}

      {/* ✅ FIX 3: Show actual error instead of silent fail */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm font-medium">
          ⚠ {error}
        </div>
      )}

      {!isRejecting ? (
        <div className="flex gap-4">
          {/* ✅ FIX 4: Button disabled + spinner while submitting */}
          <button
            onClick={handleApprove}
            disabled={isSubmitting}
            className="flex-1 flex justify-center items-center gap-2 bg-green-600 text-white px-6 py-4 rounded-xl font-bold hover:bg-green-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Check className="w-6 h-6" />
            )}
            {isSubmitting ? "Publishing..." : "Approve & Publish"}
          </button>
          <button
            onClick={() => setIsRejecting(true)}
            disabled={isSubmitting}
            className="flex-1 flex justify-center items-center gap-2 bg-red-100 text-red-700 px-6 py-4 rounded-xl font-bold hover:bg-red-200 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <X className="w-6 h-6" /> Reject
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Feedback for AI agent (e.g. 'Make it more about space exploration')..."
            className="w-full h-32 p-4 border border-zinc-300 dark:border-zinc-700 rounded-xl bg-transparent focus:ring-2 focus:ring-terracotta outline-none resize-none"
          />
          <div className="flex gap-4">
            <button
              onClick={handleReject}
              disabled={isSubmitting || !feedback.trim()}
              className="flex-1 flex justify-center items-center gap-2 bg-red-600 text-white px-6 py-4 rounded-xl font-bold hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <RefreshCw className="w-5 h-5" />
              )}
              {isSubmitting ? "Sending feedback..." : "Send & Regenerate"}
            </button>
            <button
              onClick={() => { setIsRejecting(false); setError(null); }}
              disabled={isSubmitting}
              className="px-6 py-4 rounded-xl font-bold hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Social previews */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-xl border border-blue-100 dark:border-blue-900/30">
          <h4 className="text-sm font-bold uppercase text-blue-600 mb-3">
            Facebook Preview
          </h4>
          <p className="text-sm">{story.facebook_caption}</p>
        </div>
        <div className="bg-pink-50 dark:bg-pink-900/20 p-6 rounded-xl border border-pink-100 dark:border-pink-900/30">
          <h4 className="text-sm font-bold uppercase text-pink-600 mb-3">
            Instagram Preview
          </h4>
          <p className="text-sm">{story.instagram_caption}</p>
        </div>
      </div>
    </div>
  );
}