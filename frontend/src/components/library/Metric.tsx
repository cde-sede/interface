/**
 * Metric Component
 *
 * Displays a key metric value with optional formatting, trends, and comparisons.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Metric.css';

export type MetricFormat = 'number' | 'currency' | 'percentage' | 'duration';
export type MetricTrend = 'up' | 'down' | 'neutral';
export type MetricVariant = 'default' | 'success' | 'error' | 'warning' | 'info';

export interface MetricProps extends BaseComponentProps {
	value: string | number;  /** The metric value to display */
	label: string;           /** Label describing the metric */
	unit?: string;           /** Optional unit to display with the value */
	previousValue?: number;  /** Previous value for calculating change percentage */
	format?: MetricFormat;   /** How to format the value */
	trend?: MetricTrend;     /** Trend direction */
	icon?: string;           /** Optional icon */
	variant?: MetricVariant; /** Visual variant */
}

export function Metric({
	value,
	label,
	unit,
	previousValue,
	format = 'number',
	trend,
	icon,
	variant = 'default',
	className,
	style,
	'data-testid': dataTestId
}: MetricProps) {
	const formatValue = (val: any): string => {
		const numVal = typeof val === 'number' ? val : parseFloat(val);

		if (isNaN(numVal)) return val;

		switch (format) {
			case 'currency':
				return `$${numVal.toLocaleString()}`;
			case 'percentage':
				return `${numVal}%`;
			case 'duration':
				return `${numVal}s`;
			case 'number':
			default:
				return numVal.toLocaleString();
		}
	};

	let changePercent: number | null = null;
	if (previousValue !== undefined && typeof value === 'number' && typeof previousValue === 'number' && previousValue !== 0) {
		changePercent = ((value - previousValue) / previousValue) * 100;
	}

	const metricClassName = cn(
		'lib-metric',
		`lib-metric-${variant}`,
		className
	);

	const determinedTrend = trend || (changePercent !== null
		? (changePercent > 0 ? 'up' : changePercent < 0 ? 'down' : 'neutral')
		: undefined);

	return (
		<div
			className={metricClassName}
			style={style}
			data-testid={dataTestId}
		>
			<div className="lib-metric-header">
				<span className="lib-metric-label">{label}</span>
				{icon && <span className="lib-metric-icon">{icon}</span>}
			</div>
			<div className="lib-metric-value">
				{formatValue(value)}
				{unit && <span className="lib-metric-unit">{unit}</span>}
			</div>
			{(trend || changePercent !== null) && determinedTrend && (
				<div className={`lib-metric-trend lib-metric-trend-${determinedTrend}`}>
					{changePercent !== null && (
						<span className="lib-metric-change">
							{changePercent > 0 ? '↑' : changePercent < 0 ? '↓' : '→'} {Math.abs(changePercent).toFixed(1)}%
						</span>
					)}
				</div>
			)}
		</div>
	);
}
