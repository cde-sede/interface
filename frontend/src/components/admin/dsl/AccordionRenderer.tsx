/**
 * Accordion Renderer
 *
 * Renders an accordion component for collapsible sections
 */

import { useState } from 'react';
import type { AccordionComponent, ComponentDefinition } from './types';
import { resolveValue } from './valueResolver';
import { ActionEngine } from './actionEngine';
import StatsCardsRenderer from './StatsCardsRenderer';
import InfoGridRenderer from './InfoGridRenderer';
import CodeBlockRenderer from './CodeBlockRenderer';
import TableRenderer from './TableRenderer';
import ButtonRenderer from './ButtonRenderer';
import FormRenderer from './FormRenderer';
import BadgeRenderer from './BadgeRenderer';
import ProgressBarRenderer from './ProgressBarRenderer';
import DividerRenderer from './DividerRenderer';

interface AccordionRendererProps {
	modalData?: any;
	component: AccordionComponent;
	pageData?: any;
	actionEngine: ActionEngine;
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

	const renderComponent = (comp: ComponentDefinition, index: number) => {
		switch (comp.type) {
			case 'stats-cards':
				return <StatsCardsRenderer key={index} component={comp} />;
			case 'info-grid':
				return <InfoGridRenderer key={index} component={comp} pageData={pageData} modalData={modalData} />;
			case 'code-block':
				return <CodeBlockRenderer key={index} component={comp} pageData={pageData} modalData={modalData} />;
			case 'table':
				return <TableRenderer key={index} component={comp} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'button':
				return <ButtonRenderer key={index} component={comp} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'form':
				return <FormRenderer key={index} component={comp} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'badge':
				return <BadgeRenderer key={index} component={comp} pageData={pageData} modalData={modalData} />;
			case 'progress-bar':
				return <ProgressBarRenderer key={index} component={comp} pageData={pageData} modalData={modalData} />;
			case 'divider':
				return <DividerRenderer key={index} component={comp} />;
			case 'alert':
				return (
					<div key={index} className={`alert alert-${comp.variant}`}>
						{comp.message}
					</div>
				);
			default:
				return <div key={index}>Unknown component type</div>;
		}
	};

	const className = `dsl-accordion dsl-accordion-${variant}`;

	return (
		<div className={className}>
			{items.map((item) => {
				const isExpanded = expandedItems.has(item.id);
				const resolvedTitle = resolveValue(item.title, { pageData, data: modalData });

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
						{isExpanded && (
							<div className="dsl-accordion-content">
								{item.content.map((comp, index) => renderComponent(comp, index))}
							</div>
						)}
					</div>
				);
			})}
		</div>
	);
}
