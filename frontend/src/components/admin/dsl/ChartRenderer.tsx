/**
 * Chart Renderer
 *
 * DSL adapter for Chart library component.
 */

import { Chart } from '../../library/Chart';
import type { ChartComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveComponentData } from './valueResolver';

interface ChartRendererProps {
	modalData?: any;
	component: ChartComponent;
	pageData?: any;
	actionEngine?: ActionEngine;
}

export default function ChartRenderer({ component, pageData, modalData, actionEngine }: ChartRendererProps) {
	const { chartType, data: rawData, config } = component;

	// Resolve data if it's a ValueRef
	const data = resolveComponentData(rawData, pageData, modalData);

	const { customStyle, className: rawClassName } = component;
	const className = rawClassName ? resolveComponentData(rawClassName, pageData, modalData) : undefined;

	const chartElement = (
		<Chart
			chartType={chartType}
			data={data || []}
			config={config}
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
		return chartElement;
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
			{chartElement}
		</ComponentWrapper>
	);
}
