/**
 * Grid Component
 *
 * CSS Grid layout container for responsive layouts.
 */

import { type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Grid.css';

export interface GridProps extends BaseComponentProps {
	children: ReactNode;           /** Grid items */
	columns?: number | string;     /** Number of columns or template string */
	gap?: string;                  /** Gap between items */
	autoRows?: string;             /** Auto row sizing */
}

export function Grid({
	children,
	columns = 3,
	gap = '1rem',
	autoRows,
	className,
	style,
	'data-testid': dataTestId
}: GridProps) {
	// Convert columns to grid template
	const gridTemplateColumns = typeof columns === 'number'
		? `repeat(${columns}, 1fr)`
		: columns;

	const gridStyle: React.CSSProperties = {
		gridTemplateColumns,
		gap,
		...(autoRows && { gridAutoRows: autoRows }),
		...style
	};

	return (
		<div
			className={cn('lib-grid', className)}
			style={gridStyle}
			data-testid={dataTestId}
		>
			{children}
		</div>
	);
}
