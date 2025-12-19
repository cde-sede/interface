/**
 * Number Input Component
 *
 * Custom number input with theme-styled increment/decrement buttons
 */

import { useState, useEffect } from 'react';
import './NumberInput.css';

interface NumberInputProps {
	id?: string;
	value: number | string;
	onChange: (value: number | string) => void;
	placeholder?: string;
	disabled?: boolean;
	readonly?: boolean;
	min?: number;
	max?: number;
	step?: number;
	className?: string;
}

export default function NumberInput({
	id,
	value,
	onChange,
	placeholder,
	disabled = false,
	readonly = false,
	min,
	max,
	step = 1,
	className = ''
}: NumberInputProps) {
	const [inputValue, setInputValue] = useState(String(value || ''));

	// Sync with external value changes
	useEffect(() => {
		setInputValue(String(value || ''));
	}, [value]);

	const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const newValue = e.target.value;
		setInputValue(newValue);

		// Parse and validate
		if (newValue === '' || newValue === '-') {
			onChange(newValue);
			return;
		}

		const parsed = parseFloat(newValue);
		if (!isNaN(parsed)) {
			onChange(parsed);
		}
	};

	const increment = () => {
		const current = parseFloat(inputValue) || 0;
		let newValue = current + step;

		if (max !== undefined && newValue > max) {
			newValue = max;
		}

		setInputValue(String(newValue));
		onChange(newValue);
	};

	const decrement = () => {
		const current = parseFloat(inputValue) || 0;
		let newValue = current - step;

		if (min !== undefined && newValue < min) {
			newValue = min;
		}

		setInputValue(String(newValue));
		onChange(newValue);
	};

	const handleBlur = () => {
		// Validate on blur
		const parsed = parseFloat(inputValue);

		if (isNaN(parsed)) {
			setInputValue('');
			onChange('');
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
		onChange(validated);
	};

	const canIncrement = !disabled && !readonly && (max === undefined || (parseFloat(inputValue) || 0) < max);
	const canDecrement = !disabled && !readonly && (min === undefined || (parseFloat(inputValue) || 0) > min);

	return (
		<div className={`number-input-wrapper ${className}`}>
			<input
				id={id}
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
				className="number-input-field"
			/>
			<div className="number-input-controls">
				<button
					type="button"
					className="number-input-btn number-input-increment"
					onClick={increment}
					disabled={!canIncrement}
					tabIndex={-1}
					aria-label="Increment"
				>
					▲
				</button>
				<button
					type="button"
					className="number-input-btn number-input-decrement"
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
