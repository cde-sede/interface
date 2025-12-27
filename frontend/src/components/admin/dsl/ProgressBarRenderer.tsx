/**
 * Progress Bar Renderer
 *
 * DSL adapter for ProgressBar library component.
 */

import { ProgressBar } from '../../library/ProgressBar';
import type { ProgressBarComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface ProgressBarRendererProps {
	modalData?: any;
	component: ProgressBarComponent;
	pageData?: any;
	actionEngine?: ActionEngine;
}

export default function ProgressBarRenderer({ component, pageData, modalData, actionEngine }: ProgressBarRendererProps) {
	const {
		value: rawValue,
		max = 100,
		label,
		variant = 'default',
		showPercentage = true,
		striped = false,
		animated = false,
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const value = resolveValue(rawValue, context);
	const resolvedLabel = label ? resolveValue(label, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const progressBarElement = (
		<ProgressBar
			value={value}
			max={max}
			label={resolvedLabel}
			variant={variant}
			showPercentage={showPercentage}
			striped={striped}
			animated={animated}
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
		return progressBarElement;
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
			{progressBarElement}
		</ComponentWrapper>
	);
}
