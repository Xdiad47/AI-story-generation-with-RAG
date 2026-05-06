"use client";

import { useState } from "react";
import { Story } from "../types";
import { format } from "date-fns";
import { Check, X, RefreshCw, ChevronDown, ChevronUp, Link as LinkIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function AdminClient({ initialStats, initialStories }: { initialStats: any, initialStories: Story[] }) {
  const [stories, setStories] = useState<Story[]>(initialStories);
  const [stats, setStats] = useState(initialStats);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [message, setMessage] = useState<{text: string, type: 'success' | 'info'} | null>(null);
  const router = useRouter();

  const fetchUpdatedData = async () => {
    try {
      const statsRes = await fetch("http://127.0.0.1:8000/admin/stats", { cache: "no-store" });
      const storiesRes = await fetch("http://127.0.0.1:8000/admin/stories", { cache: "no-store" });
      if (statsRes.ok) setStats(await statsRes.json());
      if (storiesRes.ok) setStories(await storiesRes.json());
    } catch (e) {}
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await fetch("http://127.0.0.1:8000/admin/generate", { method: "POST" });
      setMessage({ text: "↺ Triggered story generation in background...", type: 'info' });
      await fetchUpdatedData();
      router.refresh();
      setTimeout(() => setMessage(null), 3000);
    } catch (e) {
      alert("Failed to trigger generation");
    }
    setIsGenerating(false);
  };

  const handleApprove = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`http://127.0.0.1:8000/admin/approve/${id}`, { method: "POST" });
      setMessage({ text: "✓ Story approved and published!", type: 'success' });
      await fetchUpdatedData();
      router.refresh();
      setTimeout(() => setMessage(null), 3000);
    } catch (e) {}
  };

  const handleReject = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const feedback = prompt("Enter feedback for the AI:");
    if (!feedback) return;
    try {
      await fetch(`http://127.0.0.1:8000/admin/reject/${id}`, { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback })
      });
      setMessage({ text: "↺ Story rejected. Regenerating...", type: 'info' });
      await fetchUpdatedData();
      router.refresh();
      setTimeout(() => setMessage(null), 3000);
    } catch (e) {}
  };

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button 
          onClick={handleGenerate} 
          disabled={isGenerating || (stats && stats.today_count >= 3)}
          className="flex items-center gap-2 bg-terracotta text-white px-4 py-2 rounded-lg font-medium hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isGenerating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          Generate Story (Manual)
        </button>
      </div>

      {message && (
        <div className={`p-4 rounded-xl text-center font-bold ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
          {message.text}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
            <p className="text-sm font-semibold text-zinc-500 uppercase">Today's Stories</p>
            <p className="text-3xl font-bold text-charcoal dark:text-zinc-100">{stats.today_count} <span className="text-lg text-zinc-400">/ 3</span></p>
          </div>
          <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
            <p className="text-sm font-semibold text-zinc-500 uppercase">Pending Approval</p>
            <p className="text-3xl font-bold text-amber-500">{stats.pending}</p>
          </div>
          <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
            <p className="text-sm font-semibold text-zinc-500 uppercase">Published</p>
            <p className="text-3xl font-bold text-green-500">{stats.published}</p>
          </div>
          <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
            <p className="text-sm font-semibold text-zinc-500 uppercase">Total Stories</p>
            <p className="text-3xl font-bold text-charcoal dark:text-zinc-100">{stats.total}</p>
          </div>
        </div>
      )}

      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden">
        {stories.map(story => (
          <div key={story.run_id} className="border-b border-zinc-200 dark:border-zinc-800 last:border-0">
            <div 
              className="p-4 flex items-center gap-4 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
              onClick={() => toggleExpand(story.run_id)}
            >
              <img src={story.image_urls?.[0] || 'https://picsum.photos/100/100'} alt="Thumb" className="w-16 h-16 rounded-lg object-cover" />
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-bold text-lg truncate">{story.title || 'Untitled'}</h3>
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                    story.status === 'published' ? 'bg-green-100 text-green-700' :
                    story.status === 'pending_approval' ? 'bg-amber-100 text-amber-700' :
                    story.status === 'rejected_by_client' ? 'bg-red-100 text-red-700' :
                    'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
                  }`}>
                    {story.status.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="text-sm text-zinc-500 flex gap-4">
                  <span>{story.category}</span>
                  <span>•</span>
                  <span>Ages {story.age_range}</span>
                  <span>•</span>
                  <span>{story.created_at ? format(new Date(story.created_at), 'MMM d, yyyy h:mm a') : ''}</span>
                </div>
              </div>

              {story.status === 'pending_approval' && (
                <div className="flex gap-2">
                  <button onClick={(e) => handleApprove(story.run_id, e)} className="p-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors" title="Approve">
                    <Check className="w-5 h-5" />
                  </button>
                  <button onClick={(e) => handleReject(story.run_id, e)} className="p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors" title="Reject">
                    <X className="w-5 h-5" />
                  </button>
                </div>
              )}
              
              <Link href={`/admin/story/${story.run_id}`} onClick={e => e.stopPropagation()} className="p-2 text-zinc-400 hover:text-terracotta" title="Full Review Page">
                <LinkIcon className="w-5 h-5" />
              </Link>

              <div className="p-2 text-zinc-400">
                {expandedId === story.run_id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </div>
            </div>

            {expandedId === story.run_id && (
              <div className="p-6 bg-zinc-50 dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800">
                <p className="font-serif text-lg leading-relaxed mb-6 whitespace-pre-wrap">{story.story_text}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white dark:bg-zinc-950 p-4 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <h4 className="text-xs font-bold uppercase text-blue-600 mb-2">Facebook</h4>
                    <p className="text-sm">{story.facebook_caption}</p>
                  </div>
                  <div className="bg-white dark:bg-zinc-950 p-4 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <h4 className="text-xs font-bold uppercase text-pink-600 mb-2">Instagram</h4>
                    <p className="text-sm">{story.instagram_caption}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
        {stories.length === 0 && (
          <div className="p-8 text-center text-zinc-500">No stories found.</div>
        )}
      </div>
    </div>
  );
}
