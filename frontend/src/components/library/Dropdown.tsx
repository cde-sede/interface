/**
 * Dropdown Component
 *
 * Select dropdown with search, multi-select, and clearable options.
 */

import { useState, useRef, useEffect } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Dropdown.css';

export interface DropdownOption {
	value: any;           /** Option value */
	label: string;        /** Option label */
	description?: string; /** Optional description */
	icon?: string;        /** Optional icon */
	disabled?: boolean;   /** Disabled state */
}

export interface DropdownProps extends BaseComponentProps {
	name?: string;                   /** Input name */
	label?: string;                  /** Dropdown label */
	placeholder?: string;            /** Placeholder text */
	options: DropdownOption[];       /** Available options */
	defaultValue?: any;              /** Default value */
	value?: any;                     /** Controlled value */
	searchable?: boolean;            /** Enable search */
	clearable?: boolean;             /** Enable clear button */
	multiple?: boolean;              /** Enable multi-select */
	onChange?: (value: any) => void; /** Change handler */
	disabled?: boolean;              /** Disabled state */
}

export function Dropdown({
	name: _name,
	label,
	placeholder = 'Select...',
	options,
	defaultValue,
	value: controlledValue,
	searchable = false,
	clearable = false,
	multiple = false,
	onChange,
	disabled = false,
	className,
	style,
	'data-testid': dataTestId
}: DropdownProps) {
	const [internalValue, setInternalValue] = useState<any>(
		defaultValue ?? (multiple ? [] : null)
	);
	const [searchTerm, setSearchTerm] = useState('');
	const [isOpen, setIsOpen] = useState(false);
	const dropdownRef = useRef<HTMLDivElement>(null);

	// Use controlled value if provided
	const selectedValue = controlledValue !== undefined ? controlledValue : internalValue;

	useEffect(() => {
		const handleClickOutside = (event: MouseEvent) => {
			if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node))
				setIsOpen(false);
		};

		document.addEventListener('mousedown', handleClickOutside);
		return () => document.removeEventListener('mousedown', handleClickOutside);
	}, []);

	const filteredOptions = searchable && searchTerm
		? options.filter(opt => opt.label.toLowerCase().includes(searchTerm.toLowerCase()))
		: options;

	const handleSelect = (option: DropdownOption) => {
		let newValue;
		if (multiple) {
			const currentValues = selectedValue || [];
			if (currentValues.includes(option.value))
				newValue = currentValues.filter((v: any) => v !== option.value);
			else
				newValue = [...currentValues, option.value];
		} else {
			newValue = option.value;
			setIsOpen(false);
		}

		if (controlledValue === undefined)
			setInternalValue(newValue);

		setSearchTerm('');
		onChange?.(newValue);
	};

	const handleClear = () => {
		const newValue = multiple ? [] : null;

		if (controlledValue === undefined)
			setInternalValue(newValue);

		onChange?.(newValue);
	};

	const getDisplayValue = () => {
		if (multiple && selectedValue?.length > 0)
			return `${selectedValue.length} selected`;
		if (!multiple && selectedValue !== null && selectedValue !== undefined) {
			const option = options.find(opt => opt.value === selectedValue);
			return option?.label || '';
		}
		return placeholder;
	};

	const containerClassName = cn(
		'lib-dropdown-container',
		disabled && 'lib-dropdown-disabled',
		className
	);

	const triggerClassName = cn(
		'lib-dropdown-trigger',
		isOpen && 'lib-dropdown-open'
	);

	return (
		<div
			className={containerClassName}
			style={style}
			data-testid={dataTestId}
		>
			{label && <label className="lib-dropdown-label">{label}</label>}
			<div ref={dropdownRef} className="lib-dropdown">
				<div
					className={triggerClassName}
					onClick={() => !disabled && setIsOpen(!isOpen)}
				>
					<span className="lib-dropdown-value">{getDisplayValue()}</span>
					<div className="lib-dropdown-icons">
						{clearable && selectedValue && (
							<button
								className="lib-dropdown-clear"
								onClick={(e) => {
									e.stopPropagation();
									handleClear();
								}}
								type="button"
							>
								×
							</button>
						)}
						<span className="lib-dropdown-arrow">▼</span>
					</div>
				</div>

				{isOpen && (
					<div className="lib-dropdown-menu">
						{searchable && (
							<div className="lib-dropdown-search">
								<input
									type="text"
									className="lib-dropdown-search-input"
									placeholder="Search..."
									value={searchTerm}
									onChange={(e) => setSearchTerm(e.target.value)}
									onClick={(e) => e.stopPropagation()}
								/>
							</div>
						)}
						<div className="lib-dropdown-options">
							{filteredOptions.map((option, index) => {
								const isSelected = multiple
									? selectedValue?.includes(option.value)
									: selectedValue === option.value;

								const optionClassName = cn(
									'lib-dropdown-option',
									isSelected && 'lib-dropdown-option-selected',
									option.disabled && 'lib-dropdown-option-disabled'
								);

								return (
									<div
										key={index}
										className={optionClassName}
										onClick={() => !option.disabled && handleSelect(option)}
									>
										{option.icon && <span className="lib-dropdown-option-icon">{option.icon}</span>}
										<div className="lib-dropdown-option-content">
											<div className="lib-dropdown-option-label">{option.label}</div>
											{option.description && (
												<div className="lib-dropdown-option-description">{option.description}</div>
											)}
										</div>
										{multiple && isSelected && <span className="lib-dropdown-option-check">✓</span>}
									</div>
								);
							})}
							{filteredOptions.length === 0 && (
								<div className="lib-dropdown-empty">No options found</div>
							)}
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
