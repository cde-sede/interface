/**
 * Tooltip Renderer
 *
 * DSL adapter for Tooltip library component.
 */

import { Tooltip } from '../../library/Tooltip';
import type { TooltipComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';
import { renderComponent } from '../DSLRenderer';

interface TooltipRendererProps {
	component: TooltipComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function TooltipRenderer({ component, pageData, modalData, actionEngine }: TooltipRendererProps) {
	const { content, trigger, placement = 'top', variant = 'dark', customStyle, className: rawClassName } = component;

	const context = { pageData, data: modalData };
	const resolvedContent = resolveValue(content, context);
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const tooltipElement = (
		<Tooltip
			content={resolvedContent}
			placement={placement}
			variant={variant}
			style={customStyle as React.CSSProperties}
			className={className}
		>
			{actionEngine && renderComponent(trigger, pageData, modalData, actionEngine)}
		</Tooltip>
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
		return tooltipElement;
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
			{tooltipElement}
		</ComponentWrapper>
	);
}
