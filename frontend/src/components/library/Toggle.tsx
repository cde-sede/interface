/**
 * Toggle Component
 *
 * Switch/checkbox toggle for boolean values.
 */

import { useState } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Toggle.css';

export type ToggleSize = 'sm' | 'md' | 'lg';
export type ToggleVariant = 'default' | 'success' | 'error';

export interface ToggleProps extends BaseComponentProps {
	name?: string;                         /** Input name */
	label?: string;                        /** Toggle label */
	defaultChecked?: boolean;              /** Default checked state */
	checked?: boolean;                     /** Controlled checked state */
	disabled?: boolean;                    /** Disabled state */
	onChange?: (checked: boolean) => void; /** Change handler */
	size?: ToggleSize;                     /** Size variant */
	variant?: ToggleVariant;               /** Visual variant */
}

export function Toggle({
	name,
	label,
	defaultChecked = false,
	checked: controlledChecked,
	disabled = false,
	onChange,
	size = 'md',
	variant = 'default',
	className,
	style,
	'data-testid': dataTestId
}: ToggleProps) {
	const [internalChecked, setInternalChecked] = useState(defaultChecked);

	// Use controlled value if provided, otherwise use internal state
	const isChecked = controlledChecked !== undefined ? controlledChecked : internalChecked;

	const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const newValue = e.target.checked;

		if (controlledChecked === undefined)
			setInternalChecked(newValue);

		onChange?.(newValue);
	};

	const containerClassName = cn(
		'lib-toggle-container',
		`lib-toggle-${size}`,
		className
	);

	const toggleClassName = cn(
		'lib-toggle',
		disabled && 'lib-toggle-disabled'
	);

	const sliderClassName = cn(
		'lib-toggle-slider',
		`lib-toggle-${variant}`,
		isChecked && 'lib-toggle-checked'
	);

	return (
		<div
			className={containerClassName}
			style={style}
			data-testid={dataTestId}
		>
			<label className={toggleClassName}>
				<input
					type="checkbox"
					name={name}
					checked={isChecked}
					onChange={handleChange}
					disabled={disabled}
					className="lib-toggle-input"
				/>
				<span className={sliderClassName}></span>
			</label>
			{label && <span className="lib-toggle-label">{label}</span>}
		</div>
	);
}
