/**
 * Progress Bar Renderer
 *
 * Renders a progress bar component
 */

import type { ProgressBarComponent } from './types';
import { resolveValue } from './valueResolver';

interface ProgressBarRendererProps {
	modalData?: any;
	component: ProgressBarComponent;
	pageData?: any;
}

export default function ProgressBarRenderer({ component, pageData, modalData }: ProgressBarRendererProps) {
	const {
		value: rawValue,
		max = 100,
		label,
		variant = 'default',
		showPercentage = true,
		striped = false,
		animated = false
	} = component;

	// Resolve values if they're ValueRefs
	const value = resolveValue(rawValue, { pageData, data: modalData });
	const resolvedLabel = label ? resolveValue(label, { pageData, data: modalData }) : undefined;

	const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

	const className = [
		'dsl-progress-bar',
		`dsl-progress-bar-${variant}`,
		striped && 'dsl-progress-bar-striped',
		animated && 'dsl-progress-bar-animated'
	].filter(Boolean).join(' ');

	return (
		<div className="dsl-progress-container">
			{resolvedLabel && (
				<div className="dsl-progress-header">
					<span className="dsl-progress-label">{resolvedLabel}</span>
					{showPercentage && (
						<span className="dsl-progress-percentage">{percentage.toFixed(0)}%</span>
					)}
				</div>
			)}
			<div className={className}>
				<div
					className="dsl-progress-fill"
					style={{ width: `${percentage}%` }}
				/>
			</div>
		</div>
	);
}
