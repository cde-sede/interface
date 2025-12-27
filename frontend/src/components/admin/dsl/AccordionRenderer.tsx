/**
 * Accordion Renderer
 *
 * Renders an accordion component for collapsible sections
 */

import { useState } from 'react';
import type { AccordionComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';
import { renderComponent } from '../DSLRenderer';

interface AccordionRendererProps {
	modalData?: any;
	component: AccordionComponent;
	pageData?: any;
	actionEngine?: ActionEngine;
}

export default function AccordionRenderer({ component, pageData, modalData, actionEngine }: AccordionRendererProps) {
	const { items, allowMultiple = false, variant = 'default' } = component;

	// Track which items are expanded
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

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const customClassName = rawClassName ? resolveValue(rawClassName, context) : undefined;
	const accordionClassName = customClassName
		? `dsl-accordion dsl-accordion-${variant} ${customClassName}`
		: `dsl-accordion dsl-accordion-${variant}`;

	const accordionElement = (
		<div className={accordionClassName} style={customStyle as React.CSSProperties}>
			{items.map((item) => {
				const isExpanded = expandedItems.has(item.id);
				const resolvedTitle = resolveValue(item.title, context);

				return (
					<div key={item.id} className={`dsl-accordion-item ${isExpanded ? 'expanded' : ''}`}>
						<button
							className="dsl-accordion-header"
							onClick={() => toggleItem(item.id)}
							aria-expanded={isExpanded}
						>
							<span className="dsl-accordion-title">{resolvedTitle}</span>
							<span className="dsl-accordion-icon">{isExpanded ? '−' : '+'}</span>
						</button>
						<div className="dsl-accordion-content-wrapper">
							<div className="dsl-accordion-content">
								{item.content.map((comp, index) => (
									<div key={index}>
										{actionEngine && renderComponent(comp, pageData, modalData, actionEngine)}
									</div>
								))}
							</div>
						</div>
					</div>
				);
			})}
		</div>
	);

	// Only use ComponentWrapper if we have wrapper-level properties
	const needsWrapper = Boolean(
		actionEngine && (
			component.events?.click ||
			component.events?.hover ||
			component.id ||
			component.ariaLabel ||
			component.ariaDescribedBy
		)
	);

	if (!needsWrapper) {
		return accordionElement;
	}

	// Create a component object without customStyle/className to avoid duplication
	const wrapperComponent = {
		...component,
		customStyle: undefined,
		className: undefined
	};

	return (
		<ComponentWrapper
			component={wrapperComponent}
			pageData={pageData}
			modalData={modalData}
			actionEngine={actionEngine}
		>
			{accordionElement}
		</ComponentWrapper>
	);
}
