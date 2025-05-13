// frontend/src/hooks/useTelegramData.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { telegramService } from '../services/telegramService';

export const useTelegramGroups = () => {
  return useQuery({
    queryKey: ['telegram-groups'],
    queryFn: telegramService.getGroups,
  });
};

export const useTelegramGroup = (groupId: string) => {
  return useQuery({
    queryKey: ['telegram-group', groupId],
    queryFn: () => telegramService.getGroupDetails(groupId),
    enabled: !!groupId,
  });
};

export const useGroupMessages = (groupId: string) => {
  return useQuery({
    queryKey: ['telegram-messages', groupId],
    queryFn: () => telegramService.getGroupMessages(groupId),
    enabled: !!groupId,
  });
};

export const useGroupModerators = (groupId: string) => {
  return useQuery({
    queryKey: ['telegram-moderators', groupId],
    queryFn: () => telegramService.getGroupModerators(groupId),
    enabled: !!groupId,
  });
};

export const useAnalyzeGroup = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (groupId: string) => telegramService.analyzeGroup(groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['telegram-groups'] });
      queryClient.invalidateQueries({ queryKey: ['telegram-group'] });
    },
  });
};

export const useModeratorMetrics = (moderatorId: string, groupId: string) => {
  return useQuery({
    queryKey: ['moderator-metrics', moderatorId, groupId],
    queryFn: () => telegramService.getModeratorMetrics(moderatorId, groupId),
    enabled: !!moderatorId && !!groupId,
  });
};