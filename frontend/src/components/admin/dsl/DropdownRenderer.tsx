/**
 * Dropdown Renderer
 *
 * DSL adapter for Dropdown library component.
 */

import { useState, startTransition } from 'react';
import { Dropdown } from '../../library/Dropdown';
import type { DropdownComponent, DropdownOption as DSLDropdownOption } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface DropdownRendererProps {
	component: DropdownComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function DropdownRenderer({ component, pageData, modalData, actionEngine }: DropdownRendererProps) {
	const {
		name,
		label,
		placeholder,
		options,
		defaultValue,
		searchable = false,
		clearable = false,
		multiple = false,
		onChange,
		disabled = false
	} = component;

	const resolvedLabel = label ? resolveValue(label, { pageData, data: modalData }) : undefined;
	const resolvedPlaceholder = placeholder ? resolveValue(placeholder, { pageData, data: modalData }) : 'Select...';
	const resolvedOptions: DSLDropdownOption[] = resolveValue(options, { pageData, data: modalData });
	const resolvedDefaultValue = defaultValue ? resolveValue(defaultValue, { pageData, data: modalData }) : (multiple ? [] : null);
	const resolvedDisabled = resolveValue(disabled, { pageData, data: modalData });

	const [selectedValue, setSelectedValue] = useState<any>(resolvedDefaultValue);

	const handleChange = (newValue: any) => {
		setSelectedValue(newValue);

		if (onChange && actionEngine) {
			startTransition(() => {
				actionEngine.execute(onChange, {
					pageData,
					data: modalData,
					form: { [name]: newValue }
				});
			});
		}
	};

	// Resolve option labels, descriptions, and icons
	const dropdownOptions = resolvedOptions.map((opt: DSLDropdownOption) => ({
		value: opt.value,
		label: resolveValue(opt.label, { pageData, data: modalData }),
		description: opt.description ? resolveValue(opt.description, { pageData, data: modalData }) : undefined,
		icon: opt.icon ? resolveValue(opt.icon, { pageData, data: modalData }) : undefined,
		disabled: opt.disabled
	}));

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const dropdownElement = (
		<Dropdown
			name={name}
			label={resolvedLabel}
			placeholder={resolvedPlaceholder}
			options={dropdownOptions}
			value={selectedValue}
			searchable={searchable}
			clearable={clearable}
			multiple={multiple}
			onChange={handleChange}
			disabled={resolvedDisabled}
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
		return dropdownElement;
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
			{dropdownElement}
		</ComponentWrapper>
	);
}
