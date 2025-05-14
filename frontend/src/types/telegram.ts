// frontend/src/types/telegram.ts
export interface TelegramGroup {
  id: string;
  group_id: string;
  name: string;
  created_at: string;
  settings: {
    members_count?: number;
    is_public?: boolean;
    description?: string;
    [key: string]: any;
  };
  metrics?: {
    response_time_avg?: number;
    messages_count?: number;
    active_users?: number;
    [key: string]: any;
  };
}

export interface TelegramMessage {
  id: number;
  text: string;
  date: string;
  sender_id: number;
  reply_to_msg_id?: number;
}

export interface TelegramModerator {
  id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
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
  id?: string;
  group_id: string;
  type?: string;
  date_from?: string;
  date_to?: string;
  sentiment_score?: number;
  response_time?: string;
  resolved_issues?: number;
  satisfaction_score?: number;
  engagement_rate?: number;
  key_topics?: string[];
  created_at?: string;
}

// frontend/src/types/telegram.ts - добавить новые типы

export interface AnalysisResultSummary {
  sentiment_score: number;
  response_time_avg: number;
  resolved_issues: number;
  satisfaction_score: number;
  engagement_rate: number;
}

export interface ModeratorMetrics {
  response_time: {
    avg: number;
    min: number;
    max: number;
  };
  sentiment: {
    positive: number;
    neutral: number;
    negative: number;
  };
  performance: {
    effectiveness: number;
    helpfulness: number;
    clarity: number;
  };
}

export interface AnalysisResultData {
  timestamp: string;
  summary: AnalysisResultSummary;
  key_topics: string[];
  moderator_metrics: ModeratorMetrics;
  recommendations: string[];
}

export interface AnalysisResponse {
  status: string;
  result: AnalysisResultData;
  message?: string;
}