/**
 * Info Grid Renderer
 *
 * Renders info grid component from DSL (key-value pairs)
 */

import { useState } from 'react';
import type { InfoGridComponent } from './types';
import { resolveValue } from './valueResolver';

interface InfoGridRendererProps {
	component: InfoGridComponent;
	pageData?: any;
	modalData?: any;
}

export default function InfoGridRenderer({ component, pageData, modalData }: InfoGridRendererProps) {
	const { items, columns = 4 } = component;
	const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

	if (!items || items.length === 0) {
		return null;
	}

	const handleCopy = async (value: string, index: number) => {
		try {
			await navigator.clipboard.writeText(value);
			setCopiedIndex(index);
			setTimeout(() => setCopiedIndex(null), 2000);
		} catch (err) {
			console.error('Failed to copy:', err);
		}
	};

	const renderValue = (item: typeof items[0], index: number) => {
		// Resolve value if it's a ValueRef
		const resolvedValue = resolveValue(item.value, { pageData, data: modalData });

		const valueElement = (() => {
			switch (item.type) {
				case 'code':
					return <code className="info-value-code">{String(resolvedValue)}</code>;
				case 'status':
					return <span className="status-badge">{String(resolvedValue)}</span>;
				case 'date':
					try {
						// Handle different date formats: ISO string, Unix ms, or Unix seconds
						let date: Date;

						if (typeof resolvedValue === 'string') {
							// ISO format string
							date = new Date(resolvedValue);
						} else if (typeof resolvedValue === 'number') {
							// If number is too small, it's likely Unix seconds, convert to ms
							const timestamp = resolvedValue < 10000000000 ? resolvedValue * 1000 : resolvedValue;
							date = new Date(timestamp);
						} else {
							return <span>{String(resolvedValue)}</span>;
						}

						if (isNaN(date.getTime())) {
							return <span>{String(resolvedValue)}</span>;
						}

						return <span>{date.toLocaleString()}</span>;
					} catch {
						return <span>{String(resolvedValue)}</span>;
					}
				default:
					return <span>{String(resolvedValue)}</span>;
			}
		})();

		const displayValue = String(resolvedValue);

		return (
			<div className="info-value">
				{valueElement}
				{item.copyable && (
					<button
						className="copy-button"
						onClick={() => handleCopy(displayValue, index)}
						title="Copy to clipboard"
					>
						{copiedIndex === index ? '✓' : '📋'}
					</button>
				)}
			</div>
		);
	};

	return (
		<div className="info-grid" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
			{items.map((item, index) => (
				<div key={index} className="info-item">
					<span className="info-label">{item.label}</span>
					{renderValue(item, index)}
				</div>
			))}
		</div>
	);
}
