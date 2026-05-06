import { Story } from "../../types";
import Link from "next/link";
import { ArrowLeft, Sparkles } from "lucide-react";
import { notFound } from "next/navigation";

async function getStory(id: string) {
  try {
    const res = await fetch(`http://127.0.0.1:8000/stories/${id}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json() as Promise<Story>;
  } catch (e) {
    return null;
  }
}

export default async function StoryPage({ params }: { params: { id: string } }) {
  const story = await getStory(params.id);
  if (!story) notFound();

  return (
    <main className="max-w-4xl mx-auto px-4 py-8 w-full bg-white dark:bg-zinc-950 shadow-2xl rounded-3xl my-8 border border-zinc-100 dark:border-zinc-800">
      <nav className="mb-8 pl-4">
        <Link href="/" className="inline-flex items-center gap-2 text-zinc-500 hover:text-terracotta transition-colors font-medium">
          <ArrowLeft className="w-5 h-5" />
          Back to Stories
        </Link>
      </nav>

      <div className="relative w-full aspect-[21/9] rounded-2xl overflow-hidden shadow-md mb-12">
        <img src={story.image_urls?.[0] || 'https://picsum.photos/1200/600'} alt={story.title} className="w-full h-full object-cover" />
      </div>

      <div className="px-4 md:px-12">
        <div className="flex items-center gap-4 mb-6">
          <span className="px-4 py-1.5 bg-terracotta/10 text-terracotta rounded-full text-sm font-bold uppercase tracking-wider">
            {story.category}
          </span>
          <span className="text-sm font-semibold text-zinc-500 tracking-widest uppercase">
            Ages {story.age_range}
          </span>
        </div>

        <h1 className="text-5xl md:text-6xl font-serif font-bold mb-6 text-charcoal dark:text-zinc-100 leading-tight">
          {story.title}
        </h1>

        <p className="text-xl text-zinc-600 dark:text-zinc-400 mb-12 pb-12 border-b border-zinc-100 dark:border-zinc-800 leading-relaxed">
          {story.summary}
        </p>

        <div className="space-y-16">
          {story.paragraphs.map((paragraph, index) => (
            <div key={index} className="space-y-12">
              <p className="text-2xl font-serif leading-[1.9] text-charcoal dark:text-zinc-300">
                {paragraph}
              </p>
              
              {index < story.paragraphs.length - 1 && story.image_urls?.[index + 1] && (
                <div className="flex flex-col items-center">
                  <div className="w-full aspect-video rounded-xl overflow-hidden shadow-lg border border-zinc-100 dark:border-zinc-800">
                    <img src={story.image_urls[index + 1]} alt={`Illustration for ${story.title}`} className="w-full h-full object-cover" />
                  </div>
                  <p className="mt-4 text-sm italic text-zinc-500 max-w-2xl text-center">
                    {story.image_prompts?.[index + 1] || "A beautiful illustration of the story."}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-20 mb-12 p-8 rounded-2xl bg-orange-50 dark:bg-orange-950/20 border border-orange-100 dark:border-orange-900/30 text-center">
          <div className="flex justify-center mb-4 text-terracotta">
            <Sparkles className="w-8 h-8" />
          </div>
          <h3 className="text-sm font-bold uppercase tracking-widest text-terracotta mb-4">Moral of the Story</h3>
          <p className="text-2xl font-serif italic text-charcoal dark:text-zinc-300">"{story.moral}"</p>
        </div>
      </div>
    </main>
  );
}
