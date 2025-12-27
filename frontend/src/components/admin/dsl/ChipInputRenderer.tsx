/**
 * Chip Input Renderer
 *
 * DSL adapter for ChipInput library component.
 */

import { useState, startTransition } from 'react';
import { ChipInput } from '../../library/ChipInput';
import type { ChipInputComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface ChipInputRendererProps {
	component: ChipInputComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function ChipInputRenderer({ component, pageData, modalData, actionEngine }: ChipInputRendererProps) {
	const {
		name,
		label,
		value,
		placeholder,
		defaultValue = [],
		maxTags,
		allowDuplicates = false,
		onChange,
		variant = 'default'
	} = component;

	const resolvedLabel = label ? resolveValue(label, { pageData, data: modalData }) : undefined;
	const resolvedPlaceholder = placeholder ? resolveValue(placeholder, { pageData, data: modalData }) : 'Add tag...';
	const resolvedValue = value !== undefined ? resolveValue(value, { pageData, data: modalData }) : resolveValue(defaultValue, { pageData, data: modalData });

	const [tags, setTags] = useState<string[]>(resolvedValue);

	const handleChange = (newTags: string[]) => {
		setTags(newTags);

		if (onChange && actionEngine) {
			startTransition(() => {
				actionEngine.execute(onChange, {
					pageData,
					data: modalData,
					form: { [name]: newTags }
				});
			});
		}
	};

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const chipInputElement = (
		<ChipInput
			name={name}
			label={resolvedLabel}
			placeholder={resolvedPlaceholder}
			value={tags}
			maxTags={maxTags}
			allowDuplicates={allowDuplicates}
			onChange={handleChange}
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
		return chipInputElement;
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
			{chipInputElement}
		</ComponentWrapper>
	);
}
