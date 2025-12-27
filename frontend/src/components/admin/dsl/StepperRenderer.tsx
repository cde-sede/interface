/**
 * Stepper Renderer
 *
 * DSL adapter for Stepper library component.
 */

import { Stepper } from '../../library/Stepper';
import type { StepperComponent, StepperStep } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface StepperRendererProps {
	component: StepperComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function StepperRenderer({ component, pageData, modalData, actionEngine }: StepperRendererProps) {
	const {
		steps: rawSteps,
		currentStep: rawCurrentStep = 0,
		orientation = 'horizontal',
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const steps = resolveValue(rawSteps, context) as StepperStep[];
	const currentStep = resolveValue(rawCurrentStep, context) as number;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const stepItems = steps.map((step) => ({
		label: resolveValue(step.label, context),
		description: step.description ? resolveValue(step.description, context) : undefined,
		status: step.status
	}));

	const stepperElement = (
		<Stepper
			steps={stepItems}
			currentStep={currentStep}
			orientation={orientation}
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
		return stepperElement;
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
			{stepperElement}
		</ComponentWrapper>
	);
}
