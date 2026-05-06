export const dynamic = 'force-dynamic';

import AdminClient from "./AdminClient";
import { Story } from "../types";

async function getStats() {
  try {
    const res = await fetch("http://127.0.0.1:8000/admin/stats", { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch (e) {
    return null;
  }
}

async function getAdminStories() {
  try {
    const res = await fetch("http://127.0.0.1:8000/admin/stories", { cache: "no-store" });
    if (!res.ok) return [];
    return res.json() as Promise<Story[]>;
  } catch (e) {
    return [];
  }
}

export default async function AdminPage() {
  const stats = await getStats();
  const stories = await getAdminStories();

  return <AdminClient initialStats={stats} initialStories={stories} />;
}
