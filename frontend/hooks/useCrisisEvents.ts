/**
 * Custom hook for fetching and managing crisis events with auto-refresh
 */

import { useState, useEffect, useCallback } from 'react';
import { fetchCrisisEvents } from '@/lib/api';
import type { CrisisEvent, CrisisEventsState } from '@/types/crisis';

interface UseCrisisEventsOptions {
  minConfidence?: number;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
}

export function useCrisisEvents(options: UseCrisisEventsOptions = {}) {
  const {
    minConfidence,
    autoRefresh = true,
    refreshInterval = 60000, // 60 seconds default
  } = options;

  const [state, setState] = useState<CrisisEventsState>({
    events: [],
    loading: true,
    error: null,
    lastUpdated: null,
  });

  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadEvents = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setState(prev => ({ ...prev, loading: true, error: null }));
      } else {
        setIsRefreshing(true);
      }

      const events = await fetchCrisisEvents(minConfidence);

      setState({
        events,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load crisis events';
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    } finally {
      setIsRefreshing(false);
    }
  }, [minConfidence]);

  // Manual refresh function
  const refresh = useCallback(() => {
    loadEvents(false);
  }, [loadEvents]);

  // Initial load
  useEffect(() => {
    loadEvents(true);
  }, [loadEvents]);

  // Auto-refresh setup
  useEffect(() => {
    if (!autoRefresh) return;

    const intervalId = setInterval(() => {
      loadEvents(false);
    }, refreshInterval);

    return () => clearInterval(intervalId);
  }, [autoRefresh, refreshInterval, loadEvents]);

  return {
    events: state.events,
    loading: state.loading,
    error: state.error,
    lastUpdated: state.lastUpdated,
    isRefreshing,
    refresh,
  };
}
