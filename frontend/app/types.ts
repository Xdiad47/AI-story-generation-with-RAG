export interface Story {
  run_id: string;
  category: string;
  title: string;
  story_text: string;
  paragraphs: string[];
  summary: string;
  moral: string;
  age_range: string;
  review_passed?: boolean;
  review_notes?: string;
  image_prompts: string[];
  image_urls: string[];
  facebook_caption: string;
  instagram_caption: string;
  status: "generating" | "review_failed" | "pending_approval" | "approved" | "rejected_by_client" | "published";
  client_feedback?: string;
  retry_count?: number;
  created_at: string;
  published_at?: string;
}
