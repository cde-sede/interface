/**
 * Container Renderer
 *
 * Renders a simple container/wrapper component for layout
 */

import { Fragment } from 'react';
import type { ContainerComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';
import { renderComponent } from '../DSLRenderer';

interface ContainerRendererProps {
	component: ContainerComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function ContainerRenderer({ component, pageData, modalData, actionEngine }: ContainerRendererProps) {
	const {
		children,
		maxWidth,
		padding,
		centered = false,
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };

	// Resolve dynamic values
	const resolvedChildren = resolveValue(children, context);
	const resolvedMaxWidth = maxWidth ? resolveValue(maxWidth, context) : undefined;
	const resolvedPadding = padding ? resolveValue(padding, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	// Build container style
	const containerStyle = {
		maxWidth: resolvedMaxWidth,
		padding: resolvedPadding,
		margin: centered ? '0 auto' : undefined,
		...customStyle
	} as React.CSSProperties;

	const containerElement = (
		<div style={containerStyle} className={className}>
			{Array.isArray(resolvedChildren) && resolvedChildren.map((child, idx) => (
				<Fragment key={idx}>
					{actionEngine && renderComponent(child, pageData, modalData, actionEngine)}
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
		return containerElement;
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
			{containerElement}
		</ComponentWrapper>
	);
}
