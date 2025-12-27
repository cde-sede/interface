/**
 * TextArea Renderer
 *
 * Standalone multiline text input component.
 */

import { useState } from 'react';
import type { TextAreaComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface TextAreaRendererProps {
	component: TextAreaComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function TextAreaRenderer({ component, pageData, modalData, actionEngine }: TextAreaRendererProps) {
	const context = { pageData, data: modalData };

	const {
		name,
		label: rawLabel,
		placeholder: rawPlaceholder,
		defaultValue: rawDefaultValue,
		rows,
		cols,
		maxLength,
		minLength,
		required: rawRequired,
		disabled: rawDisabled,
		readOnly: rawReadOnly,
		resize = 'vertical',
		onChange,
		onBlur,
		helperText: rawHelperText,
		errorText: rawErrorText,
		customStyle,
		className: rawClassName
	} = component;

	// Resolve dynamic values
	const label = rawLabel ? resolveValue(rawLabel, context) : undefined;
	const placeholder = rawPlaceholder ? resolveValue(rawPlaceholder, context) : undefined;
	const defaultValue = rawDefaultValue ? resolveValue(rawDefaultValue, context) : '';
	const required = rawRequired ? resolveValue(rawRequired, context) : false;
	const disabled = rawDisabled ? resolveValue(rawDisabled, context) : false;
	const readOnly = rawReadOnly ? resolveValue(rawReadOnly, context) : false;
	const helperText = rawHelperText ? resolveValue(rawHelperText, context) : undefined;
	const errorText = rawErrorText ? resolveValue(rawErrorText, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const [value, setValue] = useState<string>(String(defaultValue));
	const error = errorText; // Static error from DSL, not dynamic validation

	const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
		const newValue = e.target.value;
		setValue(newValue);

		if (onChange && actionEngine) {
			actionEngine.execute(onChange, {
				...context,
				form: { [name]: newValue },
				value: newValue
			});
		}
	};

	const handleBlur = () => {
		if (onBlur && actionEngine) {
			actionEngine.execute(onBlur, {
				...context,
				form: { [name]: value },
				value
			});
		}
	};

	const textareaElement = (
		<div className="input-wrapper" style={customStyle as React.CSSProperties}>
			{label && <label htmlFor={name} className="input-label">{label}</label>}
			<textarea
				id={name}
				name={name}
				value={value}
				onChange={handleChange}
				onBlur={handleBlur}
				placeholder={placeholder}
				required={required}
				disabled={disabled}
				readOnly={readOnly}
				rows={rows}
				cols={cols}
				maxLength={maxLength}
				minLength={minLength}
				className={className}
				style={{ resize }}
				aria-invalid={!!error}
				aria-describedby={error ? `${name}-error` : helperText ? `${name}-helper` : undefined}
			/>
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
		return textareaElement;
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
			{textareaElement}
		</ComponentWrapper>
	);
}
