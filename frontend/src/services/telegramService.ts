// frontend/src/services/telegramService.ts - ОБНОВЛЕННАЯ ВЕРСИЯ

import { api } from './api';
import { TelegramGroup, ModeratorMetrics, AnalysisReport } from '../types/telegram';

export const telegramService = {
  // Группы
  async getGroups(): Promise<TelegramGroup[]> {
    const response = await api.get('/telegram/groups');
    return response.data;
  },

  async getGroupDetails(groupId: string): Promise<TelegramGroup> {
    const response = await api.get(`/telegram/groups/${groupId}`);
    return response.data;
  },

  async getGroupMessages(groupId: string): Promise<any[]> {
    const response = await api.get(`/telegram/groups/${groupId}/messages`);
    return response.data;
  },

  async getGroupModerators(groupId: string): Promise<any[]> {
    const response = await api.get(`/telegram/groups/${groupId}/moderators`);
    return response.data;
  },

  // Анализ модераторов
  async analyzeGroup(groupId: string): Promise<AnalysisReport> {
    const response = await api.post(`/telegram/groups/${groupId}/analyze`);
    return response.data;
  },

  // Анализ настроений сообщества
  async analyzeCommunity(groupId: string, params: {
    prompt: string;
    days_back: number;
  }): Promise<any> {
    const response = await api.post(`/telegram/groups/${groupId}/analyze-community`, params);
    return response.data;
  },

  // НОВЫЙ МЕТОД: Анализ комментариев к постам
  async analyzePostsComments(groupId: string, params: {
    prompt: string;
    post_links: string[];
  }): Promise<any> {
    const response = await api.post(`/telegram/groups/${groupId}/analyze-posts`, params);
    return response.data;
  },

  // Модераторы
  async getModeratorMetrics(moderatorId: string, groupId: string): Promise<ModeratorMetrics[]> {
    const response = await api.get(`/telegram/moderators/${moderatorId}/metrics`, {
      params: { group_id: groupId }
    });
    return response.data;
  },

  // Аналитика
  async getGroupAnalytics(groupId: string): Promise<any> {
    const response = await api.get(`/telegram/groups/${groupId}/analytics`);
    return response.data;
  }
};