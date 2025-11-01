'use client';

/**
 * Card component for displaying individual crisis event details
 */

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, MapPin, Clock, AlertCircle, CheckCircle2 } from 'lucide-react';
import type { CrisisEvent, ConfidenceLevel } from '@/types/crisis';

interface CrisisEventCardProps {
  event: CrisisEvent;
}

function getConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.8) return 'high';
  if (score >= 0.6) return 'medium';
  return 'low';
}

function getConfidenceBadgeColor(level: ConfidenceLevel): string {
  switch (level) {
    case 'high':
      return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'medium':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'low':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
  }
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

export function CrisisEventCard({ event }: CrisisEventCardProps) {
  const confidenceLevel = getConfidenceLevel(event.confidence_score);
  const confidencePercent = Math.round(event.confidence_score * 100);

  return (
    <Card className="p-4 bg-gradient-to-br from-gray-900/90 to-gray-800/90 border-white/10 backdrop-blur-sm hover:border-white/20 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1 line-clamp-2">
            {event.title}
          </h3>
        </div>

        <Badge
          className={`${getConfidenceBadgeColor(confidenceLevel)} shrink-0 font-medium`}
        >
          {confidencePercent}%
        </Badge>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-300 mb-4 line-clamp-3">
        {event.description}
      </p>

      {/* Confidence Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-xs text-gray-400 mb-1.5">
          <span className="flex items-center gap-1">
            {confidenceLevel === 'high' ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
            ) : (
              <AlertCircle className="w-3.5 h-3.5 text-yellow-400" />
            )}
            Confidence Score
          </span>
          <span className="font-medium">{confidencePercent}%</span>
        </div>
        <div className="w-full h-2 bg-gray-700/50 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              confidenceLevel === 'high'
                ? 'bg-green-500'
                : confidenceLevel === 'medium'
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* Location */}
      {event.location_text && (
        <div className="flex items-start gap-2 text-sm text-gray-300 mb-3">
          <MapPin className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <span>{event.location_text}</span>
        </div>
      )}

      {/* Timestamp */}
      <div className="flex items-center gap-2 text-xs text-gray-400 mb-4">
        <Clock className="w-3.5 h-3.5" />
        <span>Published {formatTimestamp(event.published)}</span>
        <span className="text-gray-600">•</span>
        <span>Verified {formatTimestamp(event.verified_at)}</span>
      </div>

      {/* Sources */}
      <div className="border-t border-white/5 pt-3">
        <div className="text-xs text-gray-400 mb-2">
          Reported by {event.source_count} {event.source_count === 1 ? 'source' : 'sources'}
        </div>
        <div className="flex flex-wrap gap-2">
          {event.sources.slice(0, 3).map((source, index) => (
            <a
              key={index}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-2 py-1 bg-white/5 hover:bg-white/10 rounded text-xs text-gray-300 hover:text-white transition-colors border border-white/5"
            >
              <span className="truncate max-w-[120px]">{source.name}</span>
              <ExternalLink className="w-3 h-3 shrink-0" />
            </a>
          ))}
          {event.sources.length > 3 && (
            <span className="px-2 py-1 text-xs text-gray-400">
              +{event.sources.length - 3} more
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}
