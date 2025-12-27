/**
 * Timeline Component
 *
 * Vertical timeline for displaying chronological events.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Timeline.css';

export type TimelineVariant = 'default' | 'success' | 'error' | 'warning' | 'info';
export type TimelinePosition = 'left' | 'right' | 'alternate';

export interface TimelineItem {
	title: string;             /** Item title */
	description?: string;      /** Optional description */
	timestamp?: string;        /** Optional timestamp */
	icon?: string;             /** Optional icon */
	variant?: TimelineVariant; /** Visual variant */
}

export interface TimelineProps extends BaseComponentProps {
	items: TimelineItem[];       /** Array of timeline items */
	position?: TimelinePosition; /** Position of timeline markers */
}

export function Timeline({
	items,
	position = 'left',
	className,
	style,
	'data-testid': dataTestId
}: TimelineProps) {
	if (!items || items.length === 0)
		return null;

	const timelineClassName = cn(
		'lib-timeline',
		`lib-timeline-${position}`,
		className
	);

	const renderItem = (item: TimelineItem, index: number) => {
		const variant = item.variant || 'default';
		const itemClassName = cn(
			'lib-timeline-item',
			`lib-timeline-item-${variant}`
		);

		return (
			<div key={index} className={itemClassName}>
				<div className="lib-timeline-marker">
					{item.icon ? (
						<span className="lib-timeline-icon">{item.icon}</span>
					) : (
						<span className="lib-timeline-dot" />
					)}
					<div className="lib-timeline-step-line" />
				</div>
				<div className="lib-timeline-content">
					{item.timestamp && <span className="lib-timeline-timestamp">{item.timestamp}</span>}
					<h4 className="lib-timeline-title">{item.title}</h4>
					{item.description && <p className="lib-timeline-description">{item.description}</p>}
				</div>
			</div>
		);
	};

	return (
		<div
			className={timelineClassName}
			style={style}
			data-testid={dataTestId}
		>
			{items.map((item, index) => renderItem(item, index))}
		</div>
	);
}
