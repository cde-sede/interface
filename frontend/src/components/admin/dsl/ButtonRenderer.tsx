/**
 * Button Renderer
 *
 * DSL adapter for Button library component.
 * Handles action execution and confirmation dialogs.
 */

import { startTransition } from 'react';
import { Button } from '../../library/Button';
import type { ButtonComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface ButtonRendererProps {
	modalData?: any;
	component: ButtonComponent;
	pageData?: any;
	actionEngine?: ActionEngine;
	context?: any;
}

export default function ButtonRenderer({
	component,
	pageData,
	modalData,
	actionEngine,
	context = {}
}: ButtonRendererProps) {
	const {
		label,
		action,
		variant = 'primary',
		icon,
		size = 'medium',
		disabled = false,
		confirmMessage,
		customStyle,
		className: rawClassName
	} = component;

	const resolverContext = { pageData, data: modalData };
	const className = rawClassName ? resolveValue(rawClassName, resolverContext) : undefined;

	const handleClick = () => {
		if (!actionEngine) return;

		const actionContext = { pageData, data: modalData, ...context };

		startTransition(() => {
			if (confirmMessage) {
				const message = resolveValue(confirmMessage, actionContext);
				actionEngine.executeWithConfirmation(action, message, actionContext);
			} else {
				actionEngine.execute(action, actionContext);
			}
		});
	};

	const buttonElement = (
		<Button
			label={label}
			variant={variant}
			size={size}
			icon={icon}
			disabled={disabled}
			onClick={handleClick}
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
		return buttonElement;
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
			{buttonElement}
		</ComponentWrapper>
	);
}
