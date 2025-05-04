// frontend/src/types/telegram.ts
export interface TelegramGroup {
    id: string;
    group_id: string;
    name: string;
    created_at: string;
    settings: Record<string, any>;
  }
  
  export interface Moderator {
    id: string;
    telegram_user_id: string;
    name: string;
    created_at: string;
  }
  
  export interface ModeratorMetrics {
    id: string;
    moderator_id: string;
    group_id: string;
    date: string;
    response_time_avg: number;
    messages_count: number;
    resolved_issues: number;
    sentiment_score: number;
    effectiveness_score: number;
  }
  
  export interface AnalysisReport {
    id: string;
    group_id: string;
    type: string;
    date_from: string;
    date_to: string;
    results: Record<string, any>;
    created_at: string;
  }