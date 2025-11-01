/**
 * TypeScript types for Crisis Data Aggregator
 */

export interface LocationInfo {
  latitude: number;
  longitude: number;
  display_name: string;
  extracted_name?: string;
  raw?: any;
}

export interface SourceInfo {
  name: string;
  url: string;
}

export interface EventActions {
  alert_triggered: boolean;
  evacuation_planned: boolean;
}

export interface CrisisEvent {
  event_id: string;
  title: string;
  description: string;
  published: string;
  verified_at: string;
  confidence_score: number;
  source_count: number;
  sources: SourceInfo[];
  locations: LocationInfo[];
  location_text: string | null;
  actions: EventActions;
}

export interface AggregatorStatus {
  time_window_hours: number;
  min_confidence_threshold: number;
  sources_count: number;
  enable_human_review: boolean;
  executables: {
    alert_system: boolean;
    evacuation_planner: boolean;
  };
}

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export interface CrisisEventsState {
  events: CrisisEvent[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}
