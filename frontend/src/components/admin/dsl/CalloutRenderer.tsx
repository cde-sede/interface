/**
 * Callout Renderer
 *
 * DSL adapter for Callout library component.
 */

import { Callout } from '../../library/Callout';
import type { CalloutComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface CalloutRendererProps {
	component: CalloutComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function CalloutRenderer({ component, pageData, modalData, actionEngine }: CalloutRendererProps) {
	const {
		message: rawMessage,
		title: rawTitle,
		variant = 'info',
		icon: rawIcon,
		dismissible = false,
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const message = resolveValue(rawMessage, context);
	const title = rawTitle ? resolveValue(rawTitle, context) : undefined;
	const icon = rawIcon ? resolveValue(rawIcon, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const calloutElement = (
		<Callout
			message={message}
			title={title}
			variant={variant}
			icon={icon}
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
		return calloutElement;
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
			{calloutElement}
		</ComponentWrapper>
	);
}
