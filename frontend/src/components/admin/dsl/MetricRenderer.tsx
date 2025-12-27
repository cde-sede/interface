/**
 * Metric Renderer
 *
 * DSL adapter for Metric library component.
 */

import { Metric } from '../../library/Metric';
import type { MetricComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface MetricRendererProps {
	component: MetricComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function MetricRenderer({ component, pageData, modalData, actionEngine }: MetricRendererProps) {
	const {
		value: rawValue,
		label: rawLabel,
		unit: rawUnit,
		previousValue: rawPreviousValue,
		format = 'number',
		trend,
		icon: rawIcon,
		variant = 'default',
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const value = resolveValue(rawValue, context);
	const label = resolveValue(rawLabel, context);
	const unit = rawUnit ? resolveValue(rawUnit, context) : undefined;
	const previousValue = rawPreviousValue ? resolveValue(rawPreviousValue, context) : undefined;
	const icon = rawIcon ? resolveValue(rawIcon, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const metricElement = (
		<Metric
			value={value}
			label={label}
			unit={unit}
			previousValue={previousValue}
			format={format}
			trend={trend}
			icon={icon}
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
		return metricElement;
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
			{metricElement}
		</ComponentWrapper>
	);
}
