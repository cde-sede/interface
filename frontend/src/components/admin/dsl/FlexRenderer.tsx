/**
 * Flex Renderer
 *
 * Renders a flexbox layout component
 */

import { Fragment } from 'react';
import type { FlexComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';
import { renderComponent } from '../DSLRenderer';

interface FlexRendererProps {
	component: FlexComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function FlexRenderer({ component, pageData, modalData, actionEngine }: FlexRendererProps) {
	const {
		items,
		direction = 'row',
		justify = 'flex-start',
		align = 'stretch',
		wrap = 'nowrap',
		gap,
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };

	// Resolve dynamic values
	const resolvedItems = resolveValue(items, context);
	const resolvedGap = gap ? resolveValue(gap, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	// Build flex style
	const flexStyle = {
		display: 'flex',
		flexDirection: direction,
		justifyContent: justify,
		alignItems: align,
		flexWrap: wrap,
		gap: resolvedGap,
		...customStyle
	} as React.CSSProperties;

	const flexElement = (
		<div style={flexStyle} className={className}>
			{Array.isArray(resolvedItems) && resolvedItems.map((item, idx) => (
				<Fragment key={idx}>
					{actionEngine && renderComponent(item, pageData, modalData, actionEngine)}
				</Fragment>
			))}
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
		return flexElement;
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
			{flexElement}
		</ComponentWrapper>
	);
}
