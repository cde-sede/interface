/**
 * Alert Renderer
 *
 * DSL adapter for Alert library component.
 */

import { Alert } from '../../library/Alert';
import type { AlertComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface AlertRendererProps {
	component: AlertComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function AlertRenderer({ component, pageData, modalData, actionEngine }: AlertRendererProps) {
	const {
		message: rawMessage,
		variant,
		dismissible = false,
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const message = resolveValue(rawMessage, context);
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const alertElement = (
		<Alert
			message={message}
			variant={variant}
			dismissible={dismissible}
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
		return alertElement;
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
			{alertElement}
		</ComponentWrapper>
	);
}
