/**
 * Toggle Renderer
 *
 * DSL adapter for Toggle library component.
 */

import { useState, startTransition } from 'react';
import { Toggle } from '../../library/Toggle';
import type { ToggleComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface ToggleRendererProps {
	component: ToggleComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function ToggleRenderer({ component, pageData, modalData, actionEngine }: ToggleRendererProps) {
	const {
		name,
		label,
		defaultChecked = false,
		disabled = false,
		onChange,
		size = 'md',
		variant = 'default',
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const resolvedLabel = label ? resolveValue(label, context) : undefined;
	const resolvedDefaultChecked = resolveValue(defaultChecked, context);
	const resolvedDisabled = resolveValue(disabled, context);
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const [checked, setChecked] = useState(resolvedDefaultChecked);

	const handleChange = (newValue: boolean) => {
		setChecked(newValue);

		if (onChange && actionEngine) {
			startTransition(() => {
				actionEngine.execute(onChange, {
					...context,
					form: { [name]: newValue }
				});
			});
		}
	};

	const toggleElement = (
		<Toggle
			name={name}
			label={resolvedLabel}
			checked={checked}
			disabled={resolvedDisabled}
			onChange={handleChange}
			size={size}
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
		return toggleElement;
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
			{toggleElement}
		</ComponentWrapper>
	);
}
