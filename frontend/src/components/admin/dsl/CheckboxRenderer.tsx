/**
 * Checkbox Renderer
 *
 * Standalone checkbox component.
 */

import { useState } from 'react';
import type { CheckboxComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface CheckboxRendererProps {
	component: CheckboxComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function CheckboxRenderer({ component, pageData, modalData, actionEngine }: CheckboxRendererProps) {
	const context = { pageData, data: modalData };

	const {
		name,
		label: rawLabel,
		defaultChecked: rawDefaultChecked,
		required: rawRequired,
		disabled: rawDisabled,
		onChange,
		helperText: rawHelperText,
		errorText: rawErrorText,
		customStyle,
		className: rawClassName
	} = component;

	// Resolve dynamic values
	const label = rawLabel ? resolveValue(rawLabel, context) : undefined;
	const defaultChecked = rawDefaultChecked ? resolveValue(rawDefaultChecked, context) : false;
	const required = rawRequired ? resolveValue(rawRequired, context) : false;
	const disabled = rawDisabled ? resolveValue(rawDisabled, context) : false;
	const helperText = rawHelperText ? resolveValue(rawHelperText, context) : undefined;
	const errorText = rawErrorText ? resolveValue(rawErrorText, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const [checked, setChecked] = useState<boolean>(Boolean(defaultChecked));
	const error = errorText; // Static error from DSL, not dynamic validation

	const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const newChecked = e.target.checked;
		setChecked(newChecked);

		if (onChange && actionEngine) {
			actionEngine.execute(onChange, {
				...context,
				form: { [name]: newChecked },
				value: newChecked
			});
		}
	};

	const checkboxElement = (
		<div className="input-wrapper checkbox-wrapper" style={customStyle as React.CSSProperties}>
			<label className={`checkbox-label ${className || ''}`}>
				<input
					id={name}
					name={name}
					type="checkbox"
					checked={checked}
					onChange={handleChange}
					required={required}
					disabled={disabled}
					aria-invalid={!!error}
					aria-describedby={error ? `${name}-error` : helperText ? `${name}-helper` : undefined}
				/>
				{label && <span className="checkbox-label-text">{label}</span>}
			</label>
			{helperText && !error && <small id={`${name}-helper`} className="input-helper">{helperText}</small>}
			{error && <small id={`${name}-error`} className="input-error">{error}</small>}
		</div>
	);

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
		return checkboxElement;
	}

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
			{checkboxElement}
		</ComponentWrapper>
	);
}
