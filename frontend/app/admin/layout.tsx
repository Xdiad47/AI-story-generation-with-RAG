import { ReactNode } from "react";
import Link from "next/link";
import { BookOpen } from "lucide-react";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 w-full flex-grow">
      <header className="bg-white dark:bg-zinc-900 border-b border-orange-200 dark:border-orange-900/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/admin" className="flex items-center gap-2 font-bold text-xl text-terracotta">
            <BookOpen className="w-6 h-6" />
            StoryNest Admin
          </Link>
          <Link href="/" className="text-sm font-medium hover:text-terracotta">
            Public Site &rarr;
          </Link>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
}
