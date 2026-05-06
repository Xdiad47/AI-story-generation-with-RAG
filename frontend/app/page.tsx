import Link from "next/link";
import { Story } from "./types";
import { ArrowRight, BookOpen } from "lucide-react";

async function getStories() {
  try {
    const res = await fetch("http://127.0.0.1:8000/stories", { cache: "no-store" });
    if (!res.ok) return [];
    return res.json() as Promise<Story[]>;
  } catch (e) {
    return [];
  }
}

export default async function Home() {
  const stories = await getStories();

  return (
    <main className="max-w-5xl mx-auto px-4 py-12 w-full">
      <header className="flex justify-between items-center mb-12">
        <h1 className="text-4xl font-serif font-bold text-terracotta flex items-center gap-3">
          <BookOpen className="w-10 h-10" />
          StoryNest
        </h1>
        <Link href="/admin" className="text-sm font-medium hover:text-terracotta transition-colors px-4 py-2 rounded-full border border-current">
          Admin Panel
        </Link>
      </header>

      <div className="flex gap-3 mb-10 overflow-x-auto pb-4 scrollbar-hide">
        {["All", "Epic", "Mythology", "Folktale", "Sci-Fi", "Fable", "Adventure"].map((cat) => (
          <button key={cat} className="px-5 py-2 rounded-full bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:border-terracotta hover:text-terracotta transition-colors whitespace-nowrap font-medium text-sm">
            {cat}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-8">
        {stories.map(story => (
          <Link href={`/story/${story.run_id}`} key={story.run_id} className="group flex flex-col md:flex-row bg-white dark:bg-zinc-900 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-zinc-100 dark:border-zinc-800 hover:-translate-y-1">
            <div className="relative w-full md:w-72 h-64 md:h-auto shrink-0">
              <img src={story.image_urls?.[0] || 'https://picsum.photos/800/500'} alt={story.title} className="w-full h-full object-cover" />
              <div className="absolute top-4 left-4 px-3 py-1 bg-white/90 dark:bg-black/80 backdrop-blur-sm rounded-full text-xs font-bold uppercase tracking-wider text-terracotta">
                {story.category}
              </div>
            </div>
            
            <div className="p-8 flex flex-col justify-center flex-grow">
              <span className="text-xs font-semibold text-zinc-500 mb-2 tracking-widest uppercase">Ages {story.age_range}</span>
              <h2 className="text-3xl font-serif font-bold mb-3 group-hover:text-terracotta transition-colors">{story.title}</h2>
              <p className="text-zinc-600 dark:text-zinc-400 mb-6 line-clamp-2 leading-relaxed">{story.summary}</p>
              
              <div className="mt-auto flex items-center justify-between">
                <p className="text-sm italic text-zinc-500 max-w-[70%] line-clamp-1">"{story.moral}"</p>
                <span className="font-medium text-terracotta flex items-center gap-2 group-hover:gap-4 transition-all">
                  Read Story <ArrowRight className="w-4 h-4" />
                </span>
              </div>
            </div>
          </Link>
        ))}
        {stories.length === 0 && (
          <div className="text-center py-20 text-zinc-500">
            <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-xl">No stories published yet.</p>
          </div>
        )}
      </div>
    </main>
  );
}
