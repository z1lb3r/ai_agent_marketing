// frontend/src/services/telegramService.ts
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

  async analyzeGroup(groupId: string): Promise<AnalysisReport> {
    const response = await api.post(`/telegram/groups/${groupId}/analyze`);
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