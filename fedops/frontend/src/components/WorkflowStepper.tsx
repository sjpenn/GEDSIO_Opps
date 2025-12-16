import React from 'react';
import { Check, Circle, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ProposalStage =
    | 'DISCOVERY'
    | 'ANALYSIS'
    | 'DECOMPOSITION'
    | 'STRATEGY'
    | 'DRAFTING'
    | 'REVIEW'
    | 'APPROVAL'
    | 'SUBMISSION';

interface WorkflowStepperProps {
    currentStage: ProposalStage;
    onStageSelect?: (stage: ProposalStage) => void;
}

const STAGES: { id: ProposalStage; label: string }[] = [
    { id: 'DISCOVERY', label: 'Discovery' },
    { id: 'ANALYSIS', label: 'Analysis' },
    { id: 'DECOMPOSITION', label: 'Decomposition' },
    { id: 'STRATEGY', label: 'Strategy' },
    { id: 'DRAFTING', label: 'Drafting' },
    { id: 'REVIEW', label: 'Review' },
    { id: 'APPROVAL', label: 'Approval' },
    { id: 'SUBMISSION', label: 'Submission' },
];

export function WorkflowStepper({ currentStage, onStageSelect }: WorkflowStepperProps) {
    const currentStageIndex = STAGES.findIndex((s) => s.id === currentStage);

    return (
        <div className="w-full bg-white border-b border-gray-200">
            <div className="max-w-screen-2xl mx-auto px-4 py-3">
                <nav aria-label="Progress">
                    <ol role="list" className="flex items-center space-x-4 overflow-x-auto pb-2 scrollbar-hide">
                        {STAGES.map((stage, index) => {
                            const isCompleted = index < currentStageIndex;
                            const isCurrent = index === currentStageIndex;

                            return (
                                <li key={stage.label} className="relative flex-none">
                                    {/* Connector Line */}
                                    {index !== STAGES.length - 1 && (
                                        <div
                                            className={cn(
                                                "absolute top-4 left-1/2 w-full h-0.5 -z-10",
                                                index < currentStageIndex ? "bg-blue-600" : "bg-gray-200"
                                            )}
                                            style={{ left: '50%', width: 'calc(100% + 1rem)' }}
                                        />
                                    )}

                                    <button
                                        onClick={() => onStageSelect?.(stage.id)}
                                        disabled={!onStageSelect}
                                        className="group"
                                    >
                                        <div className="flex flex-col items-center">
                                            <span className="flex items-center justify-center relative">
                                                {isCompleted ? (
                                                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 hover:bg-blue-700 transition-colors">
                                                        <Check className="h-5 w-5 text-white" aria-hidden="true" />
                                                    </span>
                                                ) : isCurrent ? (
                                                    <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-blue-600 bg-white">
                                                        <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />
                                                    </span>
                                                ) : (
                                                    <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-gray-300 bg-white group-hover:border-gray-400">
                                                        <span className="h-2.5 w-2.5 rounded-full bg-transparent group-hover:bg-gray-300" />
                                                    </span>
                                                )}
                                            </span>
                                            <span
                                                className={cn(
                                                    "mt-2 text-xs font-medium uppercase tracking-wide",
                                                    isCurrent ? "text-blue-600" : isCompleted ? "text-gray-900" : "text-gray-500"
                                                )}
                                            >
                                                {stage.label}
                                            </span>
                                        </div>
                                    </button>
                                </li>
                            );
                        })}
                    </ol>
                </nav>
            </div>
        </div>
    );
}
