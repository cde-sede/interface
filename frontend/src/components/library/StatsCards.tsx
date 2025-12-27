/**
 * StatsCards Component
 *
 * Grid of statistic cards with values and trends.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './StatsCards.css';

export interface StatCardTrend {
	direction: 'up' | 'down';    /** Trend direction */
	value: string;                /** Trend value/label */
}

export interface StatCard {
	label: string;                /** Stat label */
	value: string | number;       /** Stat value */
	total?: string | number;      /** Optional total (shows as value/total) */
	trend?: StatCardTrend;        /** Optional trend indicator */
	color?: string;               /** Optional border color */
}

export interface StatsCardsProps extends BaseComponentProps {
	stats: StatCard[];            /** Array of stat cards */
	columns?: number;             /** Number of columns */
}

export function StatsCards({
	stats,
	columns = 4,
	className,
	style,
	'data-testid': dataTestId
}: StatsCardsProps) {
	if (!stats || stats.length === 0) {
		return null;
	}

	return (
		<div
			className={cn('lib-stats-grid', className)}
			style={{ gridTemplateColumns: `repeat(${columns}, 1fr)`, ...style }}
			data-testid={dataTestId}
		>
			{stats.map((stat, index) => (
				<div
					key={index}
					className="lib-stat-card"
					style={{ borderColor: stat.color }}
				>
					<div className="lib-stat-label">{stat.label}</div>
					<div className="lib-stat-value">
						{stat.value}
						{stat.total !== undefined && (
							<span className="lib-stat-total"> / {stat.total}</span>
						)}
					</div>
					{stat.trend && (
						<div className={cn('lib-stat-trend', `lib-stat-trend-${stat.trend.direction}`)}>
							{stat.trend.direction === 'up' ? '↑' : '↓'} {stat.trend.value}
						</div>
					)}
				</div>
			))}
		</div>
	);
}
