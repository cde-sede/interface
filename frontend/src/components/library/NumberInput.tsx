/**
 * NumberInput Component
 *
 * Number input with increment/decrement buttons.
 */

import { useState, useEffect } from 'react';
import { cn } from './utils';
import './NumberInput.css';

export interface NumberInputProps {
	id?: string;                   /** Input ID */
	name?: string;                 /** Input name */
	value?: number | string;       /** Input value */
	defaultValue?: number | string; /** Default value */
	onChange?: (value: number | string) => void; /** Change handler */
	placeholder?: string;          /** Placeholder text */
	disabled?: boolean;            /** Disabled state */
	readonly?: boolean;            /** Readonly state */
	min?: number;                  /** Minimum value */
	max?: number;                  /** Maximum value */
	step?: number;                 /** Step increment */
	className?: string;            /** Additional CSS class */
	error?: boolean;               /** Error state */
}

export function NumberInput({
	id,
	name,
	value: controlledValue,
	defaultValue,
	onChange,
	placeholder,
	disabled = false,
	readonly = false,
	min,
	max,
	step = 1,
	className = '',
	error = false
}: NumberInputProps) {
	const [inputValue, setInputValue] = useState(String(controlledValue ?? defaultValue ?? ''));

	// Sync with external value changes
	useEffect(() => {
		if (controlledValue !== undefined) {
			setInputValue(String(controlledValue));
		}
	}, [controlledValue]);

	const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const newValue = e.target.value;
		setInputValue(newValue);

		// Parse and validate
		if (newValue === '' || newValue === '-') {
			onChange?.(newValue);
			return;
		}

		const parsed = parseFloat(newValue);
		if (!isNaN(parsed)) {
			onChange?.(parsed);
		}
	};

	const increment = () => {
		const current = parseFloat(inputValue) || 0;
		let newValue = current + step;

		if (max !== undefined && newValue > max) {
			newValue = max;
		}

		setInputValue(String(newValue));
		onChange?.(newValue);
	};

	const decrement = () => {
		const current = parseFloat(inputValue) || 0;
		let newValue = current - step;

		if (min !== undefined && newValue < min) {
			newValue = min;
		}

		setInputValue(String(newValue));
		onChange?.(newValue);
	};

	const handleBlur = () => {
		// Validate on blur
		const parsed = parseFloat(inputValue);

		if (isNaN(parsed)) {
			setInputValue('');
			onChange?.('');
			return;
		}

		let validated = parsed;

		if (min !== undefined && validated < min) {
			validated = min;
		}
		if (max !== undefined && validated > max) {
			validated = max;
		}

		setInputValue(String(validated));
		onChange?.(validated);
	};

	const canIncrement = !disabled && !readonly && (max === undefined || (parseFloat(inputValue) || 0) < max);
	const canDecrement = !disabled && !readonly && (min === undefined || (parseFloat(inputValue) || 0) > min);

	return (
		<div className={cn('lib-number-input-wrapper', error && 'lib-number-input-error', className)}>
			<input
				id={id}
				name={name}
				type="number"
				value={inputValue}
				onChange={handleInputChange}
				onBlur={handleBlur}
				placeholder={placeholder}
				disabled={disabled}
				readOnly={readonly}
				min={min}
				max={max}
				step={step}
				className="lib-number-input-field"
			/>
			<div className="lib-number-input-controls">
				<button
					type="button"
					className="lib-number-input-btn lib-number-input-increment"
					onClick={increment}
					disabled={!canIncrement}
					tabIndex={-1}
					aria-label="Increment"
				>
					▲
				</button>
				<button
					type="button"
					className="lib-number-input-btn lib-number-input-decrement"
					onClick={decrement}
					disabled={!canDecrement}
					tabIndex={-1}
					aria-label="Decrement"
				>
					▼
				</button>
			</div>
		</div>
	);
}
