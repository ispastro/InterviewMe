'use client';

import {
    Radar,
    RadarChart as RechartsRadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
} from 'recharts';
import type { ScoreBreakdown } from '@/types';

interface RadarChartProps {
    scores: ScoreBreakdown;
}

export function RadarChart({ scores }: RadarChartProps) {
    const data = [
        { skill: 'Communication', value: scores.communication, fullMark: 5 },
        { skill: 'Confidence', value: scores.confidence, fullMark: 5 },
        { skill: 'Structure', value: scores.structure, fullMark: 5 },
        { skill: 'Technical', value: scores.technicalDepth, fullMark: 5 },
        { skill: 'Relevance', value: scores.relevance, fullMark: 5 },
    ];

    return (
        <ResponsiveContainer width="100%" height={280}>
            <RechartsRadarChart data={data} cx="50%" cy="50%" outerRadius="80%">
                <PolarGrid stroke="#E5E7EB" />
                <PolarAngleAxis
                    dataKey="skill"
                    tick={{ fill: '#475569', fontSize: 12, fontFamily: 'Lexend' }}
                    tickLine={false}
                />
                <PolarRadiusAxis
                    domain={[0, 5]}
                    tick={{ fill: '#94A3B8', fontSize: 10 }}
                    tickLine={false}
                    axisLine={false}
                />
                <Radar
                    name="Skills"
                    dataKey="value"
                    stroke="#0D9488"
                    fill="#0D9488"
                    fillOpacity={0.2}
                    strokeWidth={2}
                />
            </RechartsRadarChart>
        </ResponsiveContainer>
    );
}
