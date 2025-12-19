/**
 * Form Renderer
 *
 * Renders form component from DSL with validation
 */

import { useState } from 'react';
import type { FormComponent, FormFieldDefinition } from './types';
import { ActionEngine } from './actionEngine';
import { resolveValue, resolveComponentData } from './valueResolver';
import NumberInput from './NumberInput';

interface FormRendererProps {
	component: FormComponent;
	pageData?: any;
	actionEngine: ActionEngine;
	modalData?: any;
}

export default function FormRenderer({ component, pageData, actionEngine, modalData }: FormRendererProps) {
	const { submitAction, cancelAction, layout = 'vertical', readonly = false } = component;

	// Resolve fields (might be a ValueRef)
	const fields: FormFieldDefinition[] = resolveComponentData(component.fields, pageData, modalData) || [];

	const [formData, setFormData] = useState<Record<string, any>>(() => {
		const initial: Record<string, any> = {};
		const context = { pageData, data: modalData };
		fields.forEach((field) => {
			if (field.defaultValue !== undefined) {
				// Resolve ValueRef in defaultValue
				initial[field.name] = resolveValue(field.defaultValue, context);
			}
		});
		return initial;
	});
	const [errors, setErrors] = useState<Record<string, string>>({});
	const [isSubmitting, setIsSubmitting] = useState(false);

	// Validate field
	const validateField = (field: FormFieldDefinition, value: any): string | null => {
		// Required validation
		if (field.required && !value) {
			return `${field.label} is required`;
		}

		// Validation rules
		if (field.validation && value) {
			for (const rule of field.validation) {
				switch (rule.type) {
					case 'required':
						if (!value) return rule.message || `${field.label} is required`;
						break;
					case 'email':
						if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
							return rule.message || 'Invalid email address';
						}
						break;
					case 'min':
						if (typeof value === 'number' && value < rule.value) {
							return rule.message || `Must be at least ${rule.value}`;
						}
						if (typeof value === 'string' && value.length < rule.value) {
							return rule.message || `Must be at least ${rule.value} characters`;
						}
						break;
					case 'max':
						if (typeof value === 'number' && value > rule.value) {
							return rule.message || `Must be at most ${rule.value}`;
						}
						if (typeof value === 'string' && value.length > rule.value) {
							return rule.message || `Must be at most ${rule.value} characters`;
						}
						break;
					case 'pattern':
						if (!new RegExp(rule.value).test(value)) {
							return rule.message || 'Invalid format';
						}
						break;
				}
			}
		}

		return null;
	};

	// Handle field change
	const handleChange = (field: FormFieldDefinition, value: any) => {
		setFormData({ ...formData, [field.name]: value });

		// Clear error on change
		if (errors[field.name]) {
			const newErrors = { ...errors };
			delete newErrors[field.name];
			setErrors(newErrors);
		}
	};

	// Validate all fields
	const validateForm = (): boolean => {
		const newErrors: Record<string, string> = {};

		fields.forEach((field) => {
			const error = validateField(field, formData[field.name]);
			if (error) {
				newErrors[field.name] = error;
			}
		});

		setErrors(newErrors);
		return Object.keys(newErrors).length === 0;
	};

	// Handle submit
	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();

		if (!validateForm()) {
			return;
		}

		setIsSubmitting(true);
		try {
			const context = { form: formData, pageData, data: modalData };
			await actionEngine.execute(submitAction, context);
		} finally {
			setIsSubmitting(false);
		}
	};

	// Handle cancel
	const handleCancel = () => {
		if (cancelAction) {
			const context = { form: formData, pageData, data: modalData };
			actionEngine.execute(cancelAction, context);
		}
	};

	// Render field
	const renderField = (field: FormFieldDefinition) => {
		const value = formData[field.name] || '';
		const error = errors[field.name];
		const context = { pageData, data: modalData, form: formData };

		// Resolve ValueRefs in field properties
		const resolvedPlaceholder = field.placeholder ? resolveValue(field.placeholder, context) : undefined;
		const resolvedHelpText = field.helpText ? resolveValue(field.helpText, context) : undefined;
		const resolvedOptions = field.options ? resolveValue(field.options, context) : undefined;

		switch (field.type) {
			case 'text':
			case 'email':
			case 'password':
				return (
					<div key={field.name} className="form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="required">*</span>}
						</label>
						<input
							id={field.name}
							type={field.type}
							value={value}
							onChange={(e) => handleChange(field, e.target.value)}
							placeholder={resolvedPlaceholder}
							disabled={readonly || field.readonly}
							className={error ? 'error' : ''}
						/>
						{resolvedHelpText && <p className="help-text">{resolvedHelpText}</p>}
						{error && <p className="error-text">{error}</p>}
					</div>
				);

			case 'number':
				return (
					<div key={field.name} className="form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="required">*</span>}
						</label>
						<NumberInput
							id={field.name}
							value={value}
							onChange={(newValue) => handleChange(field, newValue)}
							placeholder={resolvedPlaceholder}
							disabled={readonly || field.readonly}
							readonly={field.readonly}
							min={field.min}
							max={field.max}
							step={field.step}
							className={error ? 'error' : ''}
						/>
						{resolvedHelpText && <p className="help-text">{resolvedHelpText}</p>}
						{error && <p className="error-text">{error}</p>}
					</div>
				);

			case 'textarea':
				return (
					<div key={field.name} className="form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="required">*</span>}
						</label>
						<textarea
							id={field.name}
							value={value}
							onChange={(e) => handleChange(field, e.target.value)}
							placeholder={resolvedPlaceholder}
							disabled={readonly || field.readonly}
							className={error ? 'error' : ''}
							rows={4}
						/>
						{resolvedHelpText && <p className="help-text">{resolvedHelpText}</p>}
						{error && <p className="error-text">{error}</p>}
					</div>
				);

			case 'select':
				return (
					<div key={field.name} className="form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="required">*</span>}
						</label>
						<select
							id={field.name}
							value={value}
							onChange={(e) => handleChange(field, e.target.value)}
							disabled={readonly || field.readonly}
							className={error ? 'error' : ''}
						>
							<option value="">Select...</option>
							{resolvedOptions?.map((option: any) => (
								<option key={option.value} value={option.value}>
									{option.label}
								</option>
							))}
						</select>
						{resolvedHelpText && <p className="help-text">{resolvedHelpText}</p>}
						{error && <p className="error-text">{error}</p>}
					</div>
				);

			case 'checkbox':
				return (
					<div key={field.name} className="form-field checkbox-field">
						<label>
							<input
								type="checkbox"
								checked={!!value}
								onChange={(e) => handleChange(field, e.target.checked)}
								disabled={readonly || field.readonly}
							/>
							<span>
								{field.label}
								{field.required && <span className="required">*</span>}
							</span>
						</label>
						{resolvedHelpText && <p className="help-text">{resolvedHelpText}</p>}
						{error && <p className="error-text">{error}</p>}
					</div>
				);

			case 'date':
			case 'datetime':
				return (
					<div key={field.name} className="form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="required">*</span>}
						</label>
						<input
							id={field.name}
							type={field.type === 'datetime' ? 'datetime-local' : 'date'}
							value={value}
							onChange={(e) => handleChange(field, e.target.value)}
							disabled={readonly || field.readonly}
							className={error ? 'error' : ''}
						/>
						{resolvedHelpText && <p className="help-text">{resolvedHelpText}</p>}
						{error && <p className="error-text">{error}</p>}
					</div>
				);

			default:
				return null;
		}
	};

	return (
		<form
			onSubmit={handleSubmit}
			className={`dsl-form layout-${layout}`}
		>
			<div className="form-fields">
				{fields.map((field) => renderField(field))}
			</div>

			<div className="form-actions">
				<button
					type="submit"
					className="submit-button"
					disabled={readonly || isSubmitting}
				>
					{isSubmitting ? 'Submitting...' : 'Submit'}
				</button>
				{cancelAction && (
					<button
						type="button"
						className="cancel-button"
						onClick={handleCancel}
						disabled={isSubmitting}
					>
						Cancel
					</button>
				)}
			</div>
		</form>
	);
}
