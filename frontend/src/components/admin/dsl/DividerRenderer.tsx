/**
 * Divider Renderer
 *
 * DSL adapter for Divider library component.
 */

import { Divider } from '../../library/Divider';
import type { DividerComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface DividerRendererProps {
	component: DividerComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function DividerRenderer({ component, pageData, modalData, actionEngine }: DividerRendererProps) {
	const {
		label: rawLabel,
		orientation = 'horizontal',
		variant = 'solid',
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const label = rawLabel ? resolveValue(rawLabel, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const dividerElement = (
		<Divider
			label={label}
			orientation={orientation}
			variant={variant}
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
		return dividerElement;
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
			{dividerElement}
		</ComponentWrapper>
	);
}
