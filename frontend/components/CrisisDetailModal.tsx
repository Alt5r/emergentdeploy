'use client';

/**
 * Modal component for displaying detailed crisis/disaster event information
 * with associated news sources
 */

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, MapPin, Clock, AlertCircle, CheckCircle2, AlertTriangle, Newspaper } from 'lucide-react';
import type { CrisisEvent, ConfidenceLevel } from '@/types/crisis';

interface CrisisDetailModalProps {
  event: CrisisEvent | null;
  isOpen: boolean;
  onClose: () => void;
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

function formatFullTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function CrisisDetailModal({ event, isOpen, onClose }: CrisisDetailModalProps) {
  if (!event) return null;

  const confidenceLevel = getConfidenceLevel(event.confidence_score);
  const confidencePercent = Math.round(event.confidence_score * 100);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between gap-4 mb-2">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-orange-400" />
                <DialogTitle className="text-xl">{event.title}</DialogTitle>
              </div>
            </div>
            <Badge className={`${getConfidenceBadgeColor(confidenceLevel)} shrink-0 font-medium text-sm px-3 py-1`}>
              {confidencePercent}% confidence
            </Badge>
          </div>

          {/* Location */}
          {event.location_text && (
            <div className="flex items-center gap-2 text-sm text-gray-300 bg-white/5 rounded-lg px-3 py-2">
              <MapPin className="w-4 h-4 text-blue-400 shrink-0" />
              <span>{event.location_text}</span>
            </div>
          )}
        </DialogHeader>

        {/* Description */}
        <div className="mt-4">
          <DialogDescription className="text-base text-gray-200 leading-relaxed">
            {event.description}
          </DialogDescription>
        </div>

        {/* Confidence Score Visualization */}
        <div className="mt-4 p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center justify-between text-sm text-gray-300 mb-2">
            <span className="flex items-center gap-2 font-medium">
              {confidenceLevel === 'high' ? (
                <CheckCircle2 className="w-4 h-4 text-green-400" />
              ) : (
                <AlertCircle className="w-4 h-4 text-yellow-400" />
              )}
              Verification Status
            </span>
            <span className="text-white font-semibold">{confidencePercent}%</span>
          </div>
          <div className="w-full h-3 bg-gray-700/50 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                confidenceLevel === 'high'
                  ? 'bg-gradient-to-r from-green-600 to-green-400'
                  : confidenceLevel === 'medium'
                  ? 'bg-gradient-to-r from-yellow-600 to-yellow-400'
                  : 'bg-gradient-to-r from-red-600 to-red-400'
              }`}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            {confidenceLevel === 'high' && 'High confidence - verified by multiple authoritative sources'}
            {confidenceLevel === 'medium' && 'Medium confidence - reported by credible sources'}
            {confidenceLevel === 'low' && 'Low confidence - limited source verification'}
          </p>
        </div>

        {/* Timestamps */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="p-3 bg-white/5 rounded-lg border border-white/10">
            <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
              <Clock className="w-3.5 h-3.5" />
              <span>Published</span>
            </div>
            <div className="text-sm text-white font-medium">{formatTimestamp(event.published)}</div>
            <div className="text-xs text-gray-400 mt-0.5">{formatFullTimestamp(event.published)}</div>
          </div>
          <div className="p-3 bg-white/5 rounded-lg border border-white/10">
            <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Verified</span>
            </div>
            <div className="text-sm text-white font-medium">{formatTimestamp(event.verified_at)}</div>
            <div className="text-xs text-gray-400 mt-0.5">{formatFullTimestamp(event.verified_at)}</div>
          </div>
        </div>

        {/* News Sources */}
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-3">
            <Newspaper className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">
              News Sources ({event.source_count})
            </h3>
          </div>
          <div className="text-sm text-gray-400 mb-3">
            This event has been reported by {event.source_count} {event.source_count === 1 ? 'source' : 'sources'}
          </div>
          <div className="space-y-2">
            {event.sources.map((source, index) => (
              <a
                key={index}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 hover:border-white/20 transition-all group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-white group-hover:text-blue-400 transition-colors">
                        {source.name}
                      </span>
                      <ExternalLink className="w-3.5 h-3.5 text-gray-400 group-hover:text-blue-400 transition-colors" />
                    </div>
                    <p className="text-xs text-gray-400 line-clamp-1 break-all">
                      {source.url}
                    </p>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>

        {/* Location Details */}
        {event.locations && event.locations.length > 0 && (
          <div className="mt-6 p-4 bg-white/5 rounded-lg border border-white/10">
            <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-400" />
              Affected Locations
            </h3>
            <div className="space-y-2">
              {event.locations.map((location, index) => (
                <div key={index} className="text-sm">
                  <div className="text-gray-300">{location.display_name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {location.latitude.toFixed(4)}°N, {location.longitude.toFixed(4)}°E
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
