'use client';

import { cn } from '@/lib/utils';

interface SelectOption {
    value: string;
    label: string;
}

interface SelectProps {
    options: SelectOption[];
    value: string;
    onChange: (value: string) => void;
    label?: string;
    className?: string;
}

export function Select({ options, value, onChange, label, className }: SelectProps) {
    return (
        <div className="w-full">
            {label && (
                <label className="block text-sm font-medium text-[#0F172A] mb-2 font-[Lexend]">
                    {label}
                </label>
            )}
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className={cn(
                    'w-full h-10 px-3 py-2 rounded-[12px] appearance-none cursor-pointer font-[Lexend] text-sm',
                    'bg-white border border-[#E5E7EB]',
                    'text-[#0F172A]',
                    'focus:outline-none focus:ring-2 focus:ring-[#0D9488] focus:border-transparent',
                    'transition-all duration-200',
                    'bg-[url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%23475569\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3e%3cpolyline points=\'6 9 12 15 18 9\'%3e%3c/polyline%3e%3c/svg%3e")]',
                    'bg-[length:1.25rem] bg-[right_0.75rem_center] bg-no-repeat',
                    className
                )}
            >
                {options.map((option) => (
                    <option
                        key={option.value}
                        value={option.value}
                        className="bg-white text-[#0F172A]"
                    >
                        {option.label}
                    </option>
                ))}
            </select>
        </div>
    );
}
