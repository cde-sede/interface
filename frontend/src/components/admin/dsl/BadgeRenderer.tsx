/**
 * Badge Renderer
 *
 * DSL adapter for Badge library component.
 */

import { Badge } from '../../library/Badge';
import type { BadgeComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { resolveValue } from './valueResolver';
import { ComponentWrapper } from './ComponentWrapper';

interface BadgeRendererProps {
	component: BadgeComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function BadgeRenderer({ component, pageData, modalData, actionEngine }: BadgeRendererProps) {
	const {
		label,
		variant = 'default',
		size = 'medium',
		icon,
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const resolvedLabel = resolveValue(label, context);
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const badgeElement = (
		<Badge
			label={resolvedLabel}
			variant={variant}
			size={size}
			icon={icon}
			style={customStyle as React.CSSProperties}
			className={className}
		/>
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
		return badgeElement;
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
			{badgeElement}
		</ComponentWrapper>
	);
}
