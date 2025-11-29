import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, Circle, Lock } from 'lucide-react';

interface ShipleyPhaseIndicatorProps {
  currentPhase: string;
  className?: string;
  showLabels?: boolean;
}

const PHASES = [
  { value: 'PHASE_0_MARKET_SEGMENTATION', label: 'Phase 0', shortLabel: 'Market', color: 'bg-gray-500' },
  { value: 'PHASE_1_LONG_TERM_POSITIONING', label: 'Phase 1', shortLabel: 'Positioning', color: 'bg-blue-500' },
  { value: 'PHASE_2_OPPORTUNITY_ASSESSMENT', label: 'Phase 2', shortLabel: 'Assessment', color: 'bg-purple-500' },
  { value: 'PHASE_3_CAPTURE_PLANNING', label: 'Phase 3', shortLabel: 'Capture', color: 'bg-indigo-500' },
  { value: 'PHASE_4_PROPOSAL_PLANNING', label: 'Phase 4', shortLabel: 'Planning', color: 'bg-cyan-500' },
  { value: 'PHASE_5_PROPOSAL_DEVELOPMENT', label: 'Phase 5', shortLabel: 'Development', color: 'bg-green-500' },
  { value: 'PHASE_6_POST_SUBMITTAL', label: 'Phase 6', shortLabel: 'Post-Submit', color: 'bg-emerald-500' },
];

export default function ShipleyPhaseIndicator({ 
  currentPhase, 
  className = '', 
  showLabels = true 
}: ShipleyPhaseIndicatorProps) {
  const currentIndex = PHASES.findIndex(p => p.value === currentPhase);
  const progress = currentIndex >= 0 ? ((currentIndex + 1) / PHASES.length) * 100 : 0;

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-600">
          <span>Shipley Lifecycle Progress</span>
          <span>{currentIndex >= 0 ? PHASES[currentIndex].label : 'Unknown'}</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Phase Badges */}
      {showLabels && (
        <div className="flex flex-wrap gap-2">
          {PHASES.map((phase, index) => {
            const isCompleted = index < currentIndex;
            const isCurrent = index === currentIndex;
            const isLocked = index > currentIndex;

            return (
              <Badge
                key={phase.value}
                variant={isCurrent ? 'default' : 'outline'}
                className={`flex items-center gap-1 ${
                  isCurrent ? phase.color + ' text-white' : ''
                } ${isCompleted ? 'bg-green-50 text-green-700 border-green-300' : ''} ${
                  isLocked ? 'opacity-50' : ''
                }`}
              >
                {isCompleted && <CheckCircle2 className="h-3 w-3" />}
                {isCurrent && <Circle className="h-3 w-3 fill-current" />}
                {isLocked && <Lock className="h-3 w-3" />}
                <span className="text-xs">{phase.shortLabel}</span>
              </Badge>
            );
          })}
        </div>
      )}

      {/* Current Phase Detail */}
      {currentIndex >= 0 && (
        <div className="text-sm text-gray-600">
          <strong>Current Phase:</strong> {PHASES[currentIndex].label} - {PHASES[currentIndex].shortLabel}
          {currentIndex < PHASES.length - 1 && (
            <span className="ml-2 text-gray-500">
              → Next: {PHASES[currentIndex + 1].shortLabel}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// Compact version for tables/cards
export function ShipleyPhaseBadge({ currentPhase }: { currentPhase: string }) {
  const phase = PHASES.find(p => p.value === currentPhase);
  
  if (!phase) {
    return <Badge variant="outline">Unknown</Badge>;
  }

  return (
    <Badge className={`${phase.color} text-white`}>
      {phase.label}
    </Badge>
  );
}
