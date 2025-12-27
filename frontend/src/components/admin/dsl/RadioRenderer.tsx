/**
 * Radio Renderer
 *
 * Standalone radio button group component.
 */

import { useState } from 'react';
import type { RadioComponent, RadioOption } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface RadioRendererProps {
	component: RadioComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function RadioRenderer({ component, pageData, modalData, actionEngine }: RadioRendererProps) {
	const context = { pageData, data: modalData };

	const {
		name,
		label: rawLabel,
		options: rawOptions,
		defaultValue: rawDefaultValue,
		required: rawRequired,
		disabled: rawDisabled,
		orientation = 'vertical',
		onChange,
		helperText: rawHelperText,
		errorText: rawErrorText,
		customStyle,
		className: rawClassName
	} = component;

	// Resolve dynamic values
	const label = rawLabel ? resolveValue(rawLabel, context) : undefined;
	const options: RadioOption[] = resolveValue(rawOptions, context);
	const defaultValue = rawDefaultValue !== undefined ? resolveValue(rawDefaultValue, context) : undefined;
	const required = rawRequired ? resolveValue(rawRequired, context) : false;
	const disabled = rawDisabled ? resolveValue(rawDisabled, context) : false;
	const helperText = rawHelperText ? resolveValue(rawHelperText, context) : undefined;
	const errorText = rawErrorText ? resolveValue(rawErrorText, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const [selectedValue, setSelectedValue] = useState<any>(defaultValue);
	const error = errorText; // Static error from DSL, not dynamic validation

	const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const newValue = e.target.value;
		// Try to parse as JSON to handle complex values
		let parsedValue = newValue;
		try {
			parsedValue = JSON.parse(newValue);
		} catch {
			// Keep as string if not valid JSON
		}

		setSelectedValue(parsedValue);

		if (onChange && actionEngine) {
			actionEngine.execute(onChange, {
				...context,
				form: { [name]: parsedValue },
				value: parsedValue
			});
		}
	};

	const radioElement = (
		<div className={`input-wrapper radio-wrapper ${orientation}`} style={customStyle as React.CSSProperties}>
			{label && <div className="input-label">{label}</div>}
			<div className={`radio-options ${orientation} ${className || ''}`}>
				{options.map((option, index) => {
					const optionLabel = resolveValue(option.label, context);
					const optionValue = JSON.stringify(option.value);
					const isChecked = JSON.stringify(selectedValue) === optionValue;
					const optionId = `${name}-${index}`;

					return (
						<label key={index} className="radio-option">
							<input
								id={optionId}
								name={name}
								type="radio"
								value={optionValue}
								checked={isChecked}
								onChange={handleChange}
								required={required}
								disabled={disabled || option.disabled}
								aria-invalid={!!error}
								aria-describedby={error ? `${name}-error` : helperText ? `${name}-helper` : undefined}
							/>
							<span className="radio-label-text">{optionLabel}</span>
						</label>
					);
				})}
			</div>
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
		return radioElement;
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
			{radioElement}
		</ComponentWrapper>
	);
}
