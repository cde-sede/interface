/**
 * ChipInput Component
 *
 * Tag/chip input for managing list of values.
 */

import { useState, type KeyboardEvent } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './ChipInput.css';

export type ChipInputVariant = 'default' | 'outlined' | 'filled';

export interface ChipInputProps extends BaseComponentProps {
	name?: string;                       /** Input name */
	label?: string;                      /** Input label */
	placeholder?: string;                /** Placeholder text */
	defaultValue?: string[];             /** Default value (tags) */
	value?: string[];                    /** Controlled value */
	maxTags?: number;                    /** Maximum number of tags */
	allowDuplicates?: boolean;           /** Allow duplicate tags */
	onChange?: (tags: string[]) => void; /** Change handler */
	variant?: ChipInputVariant;          /** Visual variant */
}

export function ChipInput({
	name,
	label,
	placeholder = 'Add tag...',
	defaultValue = [],
	value: controlledValue,
	maxTags,
	allowDuplicates = false,
	onChange,
	variant = 'default',
	className,
	style,
	'data-testid': dataTestId
}: ChipInputProps) {
	const [internalTags, setInternalTags] = useState<string[]>(defaultValue);
	const [inputValue, setInputValue] = useState('');

	const tags = controlledValue !== undefined ? controlledValue : internalTags;

	const addTag = (tag: string) => {
		const trimmedTag = tag.trim();
		if (!trimmedTag) return;

		if (!allowDuplicates && tags.includes(trimmedTag)) return;
		if (maxTags && tags.length >= maxTags) return;

		const newTags = [...tags, trimmedTag];

		if (controlledValue === undefined)
			setInternalTags(newTags);

		setInputValue('');
		onChange?.(newTags);
	};

	const removeTag = (indexToRemove: number) => {
		const newTags = tags.filter((_, index) => index !== indexToRemove);

		if (controlledValue === undefined)
			setInternalTags(newTags);

		onChange?.(newTags);
	};

	const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
		if (e.key === 'Enter' && inputValue) {
			e.preventDefault();
			addTag(inputValue);
		} else if (e.key === 'Backspace' && !inputValue && tags.length > 0)
			removeTag(tags.length - 1);
	};

	const containerClassName = cn(
		'lib-chip-input-container',
		`lib-chip-input-${variant}`,
		className
	);

	return (
		<div
			className={containerClassName}
			style={style}
			data-testid={dataTestId}
		>
			{label && <label className="lib-chip-input-label">{label}</label>}
			<div className="lib-chip-input-wrapper">
				{tags.map((tag, index) => (
					<span key={index} className="lib-chip">
						<span className="lib-chip-text">{tag}</span>
						<button
							className="lib-chip-remove"
							onClick={() => removeTag(index)}
							type="button"
						>
							×
						</button>
					</span>
				))}
				{(!maxTags || tags.length < maxTags) && (
					<input
						type="text"
						name={name}
						className="lib-chip-input"
						value={inputValue}
						onChange={(e) => setInputValue(e.target.value)}
						onKeyDown={handleKeyDown}
						onBlur={() => inputValue && addTag(inputValue)}
						placeholder={tags.length === 0 ? placeholder : ''}
					/>
				)}
			</div>
		</div>
	);
}
