/**
 * Grid Renderer
 *
 * DSL adapter for Grid library component.
 */

import { Grid } from '../../library/Grid';
import type { GridComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { renderComponent } from '../DSLRenderer';
import { resolveValue } from './valueResolver';

interface GridRendererProps {
	component: GridComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function GridRenderer({ component, pageData, modalData, actionEngine }: GridRendererProps) {
	const { items, columns = 3, gap = '1rem', autoRows } = component;

	// Resolve gap
	const resolvedGap = typeof gap === 'string'
		? resolveValue(gap, { pageData, data: modalData })
		: gap;

	// Resolve autoRows if provided
	const resolvedAutoRows = autoRows
		? resolveValue(autoRows, { pageData, data: modalData })
		: undefined;

	// Check if items is an array (not a ValueRef)
	if (!Array.isArray(items)) {
		console.warn('Grid items is not an array, cannot render');
		return null;
	}

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const gridElement = (
		<Grid
			columns={columns}
			gap={resolvedGap}
			autoRows={resolvedAutoRows}
			style={customStyle as React.CSSProperties}
			className={className}
		>
			{items.map((item: any, index: number) => (
				<div key={index}>
					{actionEngine && renderComponent(item, pageData, modalData, actionEngine)}
				</div>
			))}
		</Grid>
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
		return gridElement;
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
			{gridElement}
		</ComponentWrapper>
	);
}
