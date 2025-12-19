/**
 * Stats Cards Renderer
 *
 * Renders stat cards component from DSL
 */

import type { StatsCardsComponent } from './types';

interface StatsCardsRendererProps {
	component: StatsCardsComponent;
}

export default function StatsCardsRenderer({ component }: StatsCardsRendererProps) {
	const { stats, columns = 4 } = component;

	if (!stats || stats.length === 0) {
		return null;
	}

	return (
		<div className="stats-grid" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
			{stats.map((stat, index) => (
				<div key={index} className="stat-card" style={{ borderColor: stat.color }}>
					<div className="stat-label">{stat.label}</div>
					<div className="stat-value">
						{stat.value}
						{stat.total !== undefined && (
							<span className="stat-total"> / {stat.total}</span>
						)}
					</div>
					{stat.trend && (
						<div className={`stat-trend stat-trend-${stat.trend.direction}`}>
							{stat.trend.direction === 'up' ? '↑' : '↓'} {stat.trend.value}
						</div>
					)}
				</div>
			))}
		</div>
	);
}
