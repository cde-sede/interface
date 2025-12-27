/**
 * Form Component
 *
 * Form with validation and multiple field types.
 */

import { useState } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import { NumberInput } from './NumberInput';
import { DatePicker, formatDate } from './DatePicker';
import './Form.css';

export type FormLayout = 'vertical' | 'horizontal' | 'grid';
export type FormFieldType = 'text' | 'number' | 'email' | 'password' | 'textarea' | 'select' | 'checkbox' | 'date' | 'datetime';
export type ValidationRuleType = 'required' | 'email' | 'min' | 'max' | 'pattern';

export interface ValidationRule {
	type: ValidationRuleType;    /** Rule type */
	value?: any;                 /** Rule value (for min, max, pattern) */
	message?: string;            /** Custom error message */
}

export interface FormFieldOption {
	value: any;                  /** Option value */
	label: string;               /** Option label */
}

export interface FormField {
	name: string;                /** Field name */
	label: string;               /** Field label */
	type: FormFieldType;         /** Field type */
	required?: boolean;          /** Required field */
	defaultValue?: any;          /** Default value */
	placeholder?: string;        /** Placeholder text */
	helpText?: string;           /** Help text */
	validation?: ValidationRule[]; /** Validation rules */
	options?: FormFieldOption[]; /** Options for select */
	readonly?: boolean;          /** Readonly state */
	min?: number;                /** Min value (number) */
	max?: number;                /** Max value (number) */
	step?: number;               /** Step (number) */
}

export interface FormProps extends BaseComponentProps {
	fields: FormField[];         /** Form fields */
	onSubmit: (data: Record<string, any>) => void | Promise<void>; /** Submit handler */
	onCancel?: () => void;       /** Cancel handler */
	layout?: FormLayout;         /** Form layout */
	readonly?: boolean;          /** Readonly state */
	submitLabel?: string;        /** Submit button label */
	cancelLabel?: string;        /** Cancel button label */
}

export function Form({
	fields,
	onSubmit,
	onCancel,
	layout = 'vertical',
	readonly = false,
	submitLabel = 'Submit',
	cancelLabel = 'Cancel',
	className,
	style,
	'data-testid': dataTestId
}: FormProps) {
	const [formData, setFormData] = useState<Record<string, any>>(() => {
		const initial: Record<string, any> = {};
		fields.forEach((field) => {
			if (field.defaultValue !== undefined) {
				initial[field.name] = field.defaultValue;
			}
		});
		return initial;
	});

	const [errors, setErrors] = useState<Record<string, string>>({});
	const [isSubmitting, setIsSubmitting] = useState(false);

	// Validate field
	const validateField = (field: FormField, value: any): string | null => {
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
	const handleChange = (field: FormField, value: any) => {
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
			await onSubmit(formData);
		} finally {
			setIsSubmitting(false);
		}
	};

	// Render field
	const renderField = (field: FormField) => {
		const value = formData[field.name] || '';
		const error = errors[field.name];

		switch (field.type) {
			case 'text':
			case 'email':
			case 'password':
				return (
					<div key={field.name} className="lib-form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="lib-form-required">*</span>}
						</label>
						<input
							id={field.name}
							name={field.name}
							type={field.type}
							value={value}
							onChange={(e) => handleChange(field, e.target.value)}
							placeholder={field.placeholder}
							disabled={readonly || field.readonly}
							className={error ? 'lib-form-error' : ''}
						/>
						{field.helpText && <p className="lib-form-help-text">{field.helpText}</p>}
						{error && <p className="lib-form-error-text">{error}</p>}
					</div>
				);

			case 'number':
				return (
					<div key={field.name} className="lib-form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="lib-form-required">*</span>}
						</label>
						<NumberInput
							id={field.name}
							name={field.name}
							value={value}
							onChange={(newValue) => handleChange(field, newValue)}
							placeholder={field.placeholder}
							disabled={readonly || field.readonly}
							readonly={field.readonly}
							min={field.min}
							max={field.max}
							step={field.step}
							error={!!error}
						/>
						{field.helpText && <p className="lib-form-help-text">{field.helpText}</p>}
						{error && <p className="lib-form-error-text">{error}</p>}
					</div>
				);

			case 'textarea':
				return (
					<div key={field.name} className="lib-form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="lib-form-required">*</span>}
						</label>
						<textarea
							id={field.name}
							name={field.name}
							value={value}
							onChange={(e) => handleChange(field, e.target.value)}
							placeholder={field.placeholder}
							disabled={readonly || field.readonly}
							className={error ? 'lib-form-error' : ''}
							rows={4}
						/>
						{field.helpText && <p className="lib-form-help-text">{field.helpText}</p>}
						{error && <p className="lib-form-error-text">{error}</p>}
					</div>
				);

			case 'select':
				return (
					<div key={field.name} className="lib-form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="lib-form-required">*</span>}
						</label>
						<select
							id={field.name}
							name={field.name}
							value={value}
							onChange={(e) => handleChange(field, e.target.value)}
							disabled={readonly || field.readonly}
							className={error ? 'lib-form-error' : ''}
						>
							<option value="">Select...</option>
							{field.options?.map((option) => (
								<option key={option.value} value={option.value}>
									{option.label}
								</option>
							))}
						</select>
						{field.helpText && <p className="lib-form-help-text">{field.helpText}</p>}
						{error && <p className="lib-form-error-text">{error}</p>}
					</div>
				);

			case 'checkbox':
				return (
					<div key={field.name} className="lib-form-field lib-form-checkbox-field">
						<label>
							<input
								type="checkbox"
								name={field.name}
								checked={!!value}
								onChange={(e) => handleChange(field, e.target.checked)}
								disabled={readonly || field.readonly}
							/>
							<span>
								{field.label}
								{field.required && <span className="lib-form-required">*</span>}
							</span>
						</label>
						{field.helpText && <p className="lib-form-help-text">{field.helpText}</p>}
						{error && <p className="lib-form-error-text">{error}</p>}
					</div>
				);

			case 'date':
				return (
					<div key={field.name} className="lib-form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="lib-form-required">*</span>}
						</label>
						<DatePicker
							id={field.name}
							name={field.name}
							value={value ? new Date(value) : null}
							onChange={(date) => handleChange(field, date ? formatDate(date, 'YYYY-MM-DD') : '')}
							format="YYYY-MM-DD"
							placeholder={field.placeholder}
							disabled={readonly || field.readonly}
							error={!!error}
						/>
						{field.helpText && <p className="lib-form-help-text">{field.helpText}</p>}
						{error && <p className="lib-form-error-text">{error}</p>}
					</div>
				);

			case 'datetime':
				return (
					<div key={field.name} className="lib-form-field">
						<label htmlFor={field.name}>
							{field.label}
							{field.required && <span className="lib-form-required">*</span>}
						</label>
						<input
							id={field.name}
							name={field.name}
							type="datetime-local"
							value={value}
							onChange={(e) => handleChange(field, e.target.value)}
							disabled={readonly || field.readonly}
							className={error ? 'lib-form-error' : ''}
						/>
						{field.helpText && <p className="lib-form-help-text">{field.helpText}</p>}
						{error && <p className="lib-form-error-text">{error}</p>}
					</div>
				);

			default:
				return null;
		}
	};

	const formClassName = cn(
		'lib-form',
		layout !== 'vertical' && `lib-form-${layout}`,
		className
	);

	return (
		<form
			onSubmit={handleSubmit}
			className={formClassName}
			style={style}
			data-testid={dataTestId}
		>
			<div className="lib-form-fields">
				{fields.map((field) => renderField(field))}
			</div>

			<div className="lib-form-actions">
				<button
					type="submit"
					className="lib-form-submit-button"
					disabled={readonly || isSubmitting}
				>
					{isSubmitting ? 'Submitting...' : submitLabel}
				</button>
				{onCancel && (
					<button
						type="button"
						className="lib-form-cancel-button"
						onClick={onCancel}
						disabled={isSubmitting}
					>
						{cancelLabel}
					</button>
				)}
			</div>
		</form>
	);
}
