/**
 * ProgressBar Component
 *
 * Visual progress indicator with percentage display.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './ProgressBar.css';

export type ProgressBarVariant = 'default' | 'success' | 'error' | 'warning' | 'info';

export interface ProgressBarProps extends BaseComponentProps {
	value: number;                /** Current progress value */
	max?: number;                 /** Maximum value (default 100) */
	label?: string;               /** Optional label */
	variant?: ProgressBarVariant; /** Visual variant */
	showPercentage?: boolean;     /** Show percentage text */
	striped?: boolean;            /** Striped pattern */
	animated?: boolean;           /** Animated stripes */
}

export function ProgressBar({
	value,
	max = 100,
	label,
	variant = 'default',
	showPercentage = true,
	striped = false,
	animated = false,
	className,
	style,
	'data-testid': dataTestId
}: ProgressBarProps) {
	const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

	const progressBarClassName = cn(
		'lib-progress-bar',
		`lib-progress-bar-${variant}`,
		striped && 'lib-progress-bar-striped',
		animated && 'lib-progress-bar-animated',
		className
	);

	return (
		<div className="lib-progress-container" data-testid={dataTestId} style={style}>
			{label && (
				<div className="lib-progress-header">
					<span className="lib-progress-label">{label}</span>
					{showPercentage && (
						<span className="lib-progress-percentage">{percentage.toFixed(0)}%</span>
					)}
				</div>
			)}
			<div className={progressBarClassName}>
				<div
					className="lib-progress-fill"
					style={{ width: `${percentage}%` }}
				/>
			</div>
		</div>
	);
}
