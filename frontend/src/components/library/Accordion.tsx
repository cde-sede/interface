/**
 * Accordion Component
 *
 * Collapsible sections for organizing content.
 */

import { useState, type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Accordion.css';

export type AccordionVariant = 'default' | 'bordered' | 'separated';

export interface AccordionItem {
	/** Unique item ID */
	id: string;
	/** Item title */
	title: string;
	/** Item content */
	content: ReactNode;
	/** Default expanded state */
	defaultExpanded?: boolean;
}

export interface AccordionProps extends BaseComponentProps {
	/** Accordion items */
	items: AccordionItem[];
	/** Allow multiple items expanded */
	allowMultiple?: boolean;
	/** Visual variant */
	variant?: AccordionVariant;
}

export function Accordion({
	items,
	allowMultiple = false,
	variant = 'default',
	className,
	style,
	'data-testid': dataTestId
}: AccordionProps) {
	const [expandedItems, setExpandedItems] = useState<Set<string>>(() => {
		const initial = new Set<string>();
		items.forEach((item) => {
			if (item.defaultExpanded) {
				initial.add(item.id);
			}
		});
		return initial;
	});

	const toggleItem = (itemId: string) => {
		setExpandedItems((prev) => {
			const next = new Set(prev);
			if (next.has(itemId)) {
				next.delete(itemId);
			} else {
				if (!allowMultiple) {
					next.clear();
				}
				next.add(itemId);
			}
			return next;
		});
	};

	const accordionClassName = cn(
		'lib-accordion',
		`lib-accordion-${variant}`,
		className
	);

	return (
		<div
			className={accordionClassName}
			style={style}
			data-testid={dataTestId}
		>
			{items.map((item) => {
				const isExpanded = expandedItems.has(item.id);
				const itemClassName = cn(
					'lib-accordion-item',
					isExpanded && 'expanded'
				);

				return (
					<div key={item.id} className={itemClassName}>
						<button
							className="lib-accordion-header"
							onClick={() => toggleItem(item.id)}
							type="button"
						>
							<span className="lib-accordion-title">{item.title}</span>
							<span className="lib-accordion-icon">
								{isExpanded ? '−' : '+'}
							</span>
						</button>
						<div className="lib-accordion-content-wrapper">
							<div className="lib-accordion-content">
								{item.content}
							</div>
						</div>
					</div>
				);
			})}
		</div>
	);
}
