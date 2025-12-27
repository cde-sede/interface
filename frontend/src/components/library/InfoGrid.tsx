/**
 * InfoGrid Component
 *
 * Grid display for key-value information pairs.
 */

import { useState } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './InfoGrid.css';

export type InfoGridItemType = 'text' | 'code' | 'status' | 'date';

export interface InfoGridItem {
	label: string;           /** Item label */
	value: string | number;  /** Item value */
	type?: InfoGridItemType; /** Value display type */
	icon?: string;           /** Optional icon */
	copyable?: boolean;      /** Enable copy to clipboard */
}

export interface InfoGridProps extends BaseComponentProps {
	items: InfoGridItem[]; /** Array of info items */
	columns?: number;      /** Number of columns (auto-fit by default) */
}

export function InfoGrid({
	items,
	columns,
	className,
	style,
	'data-testid': dataTestId
}: InfoGridProps) {
	const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

	if (!items || items.length === 0)
		return null;

	const handleCopy = async (value: string, index: number) => {
		try {
			await navigator.clipboard.writeText(value);
			setCopiedIndex(index);
			setTimeout(() => setCopiedIndex(null), 2000);
		} catch (err) {
			console.error('Failed to copy:', err);
		}
	};

	const renderValue = (item: InfoGridItem, index: number) => {
		const valueElement = (() => {
			switch (item.type) {
				case 'code':
					return <code className="lib-info-value-code">{String(item.value)}</code>;
				case 'status':
					return <span className="lib-status-badge">{String(item.value)}</span>;
				case 'date':
					try {
						let date: Date;

						if (typeof item.value === 'string') {
							date = new Date(item.value);
						} else if (typeof item.value === 'number') {
							// If number is too small, it's likely Unix seconds, convert to ms
							const timestamp = item.value < 10000000000 ? item.value * 1000 : item.value;
							date = new Date(timestamp);
						} else {
							return <span>{String(item.value)}</span>;
						}

						if (isNaN(date.getTime())) {
							return <span>{String(item.value)}</span>;
						}

						return <span>{date.toLocaleString()}</span>;
					} catch {
						return <span>{String(item.value)}</span>;
					}
				default:
					return <span>{String(item.value)}</span>;
			}
		})();

		const displayValue = String(item.value);

		return (
			<div className="lib-info-value">
				{valueElement}
				{item.copyable && (
					<button
						className="lib-copy-button"
						onClick={() => handleCopy(displayValue, index)}
						title="Copy to clipboard"
					>
						{copiedIndex === index ? '✓' : '📋'}
					</button>
				)}
			</div>
		);
	};

	const gridStyle = {
		...style,
		...(columns && { gridTemplateColumns: `repeat(${columns}, 1fr)` })
	};

	return (
		<div
			className={cn('lib-info-grid', className)}
			style={gridStyle}
			data-testid={dataTestId}
		>
			{items.map((item, index) => (
				<div key={index} className="lib-info-item">
					<span className="lib-info-label">{item.label}</span>
					{renderValue(item, index)}
				</div>
			))}
		</div>
	);
}
