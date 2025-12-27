/**
 * DatePicker Component
 *
 * Date picker based on Calendar with customizable date formatting.
 */

import { useState, useRef, useEffect, useLayoutEffect } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import { Portal } from './Portal';
import './DatePicker.css';

export interface DatePickerProps extends BaseComponentProps {
	id?: string;                      /** Input ID */
	name?: string;                    /** Input name */
	value?: Date | string | null;     /** Controlled value */
	defaultValue?: Date | string | null; /** Default value */
	onChange?: (date: Date | null) => void; /** Change handler */
	format?: string;                  /** Date format string (default: 'YYYY-MM-DD') */
	placeholder?: string;             /** Placeholder text */
	disabled?: boolean;               /** Disabled state */
	readonly?: boolean;               /** Readonly state */
	error?: boolean;                  /** Error state */
	clearable?: boolean;              /** Show clear button */
	minDate?: Date | string;          /** Minimum selectable date */
	maxDate?: Date | string;          /** Maximum selectable date */
}

// Month names for formatting
const MONTH_NAMES = [
	'January', 'February', 'March', 'April', 'May', 'June',
	'July', 'August', 'September', 'October', 'November', 'December'
];

const MONTH_NAMES_SHORT = [
	'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
	'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

/**
 * Format a date using a format string
 * Supported patterns:
 * - YYYY: 4-digit year
 * - YY: 2-digit year
 * - MMMM: Full month name
 * - MMM: Short month name
 * - MM: 2-digit month
 * - M: 1 or 2-digit month
 * - DD: 2-digit day
 * - D: 1 or 2-digit day
 */
export function formatDate(date: Date | null, format: string): string {
	if (!date) return '';

	const year = date.getFullYear();
	const month = date.getMonth();
	const day = date.getDate();

	let formatted = format;

	// Year
	formatted = formatted.replace('YYYY', year.toString());
	formatted = formatted.replace('YY', year.toString().slice(-2));

	// Month
	formatted = formatted.replace('MMMM', MONTH_NAMES[month]);
	formatted = formatted.replace('MMM', MONTH_NAMES_SHORT[month]);
	formatted = formatted.replace('MM', (month + 1).toString().padStart(2, '0'));
	formatted = formatted.replace(/\bM\b/, (month + 1).toString());

	// Day
	formatted = formatted.replace('DD', day.toString().padStart(2, '0'));
	formatted = formatted.replace(/\bD\b/, day.toString());

	return formatted;
}

/**
 * Parse a string value to a Date
 */
function parseDate(value: Date | string | null): Date | null {
	if (!value) return null;
	if (value instanceof Date) return value;
	const parsed = new Date(value);
	return isNaN(parsed.getTime()) ? null : parsed;
}

/**
 * Check if a date is within min/max bounds
 */
function isDateInRange(date: Date, minDate?: Date | string, maxDate?: Date | string): boolean {
	const min = parseDate(minDate || null);
	const max = parseDate(maxDate || null);

	if (min && date < min) return false;
	if (max && date > max) return false;

	return true;
}

export function DatePicker({
	id,
	name,
	value: controlledValue,
	defaultValue,
	onChange,
	format = 'YYYY-MM-DD',
	placeholder = 'Select date',
	disabled = false,
	readonly = false,
	error = false,
	clearable = true,
	minDate,
	maxDate,
	className,
	style,
	'data-testid': dataTestId
}: DatePickerProps) {
	const [selectedDate, setSelectedDate] = useState<Date | null>(() =>
		parseDate(controlledValue !== undefined ? controlledValue : (defaultValue || null))
	);
	const [isOpen, setIsOpen] = useState(false);
	const [currentMonth, setCurrentMonth] = useState<Date>(selectedDate || new Date());
	const [popupPosition, setPopupPosition] = useState<{ top?: number; bottom?: number; left?: number; right?: number }>({});
	const [isPositioned, setIsPositioned] = useState(false);
	const containerRef = useRef<HTMLDivElement>(null);
	const popupRef = useRef<HTMLDivElement>(null);

	// Sync with controlled value
	useEffect(() => {
		if (controlledValue !== undefined) {
			setSelectedDate(parseDate(controlledValue));
		}
	}, [controlledValue]);

	// Close on outside click
	useEffect(() => {
		if (!isOpen) return;

		const handleClickOutside = (e: MouseEvent) => {
			// Don't close if clicking inside the container or the popup
			if (
				(containerRef.current && containerRef.current.contains(e.target as Node)) ||
				(popupRef.current && popupRef.current.contains(e.target as Node))
			) {
				return;
			}
			setIsOpen(false);
		};

		document.addEventListener('mousedown', handleClickOutside);
		return () => document.removeEventListener('mousedown', handleClickOutside);
	}, [isOpen]);

	// Adjust popup position to stay within viewport
	useLayoutEffect(() => {
		if (!isOpen) {
			setIsPositioned(false);
			return;
		}

		if (!popupRef.current || !containerRef.current) return;

		// Use requestAnimationFrame to ensure popup is fully rendered
		const frame = requestAnimationFrame(() => {
			if (!popupRef.current || !containerRef.current) return;

			const popup = popupRef.current;
			const container = containerRef.current;
			const popupRect = popup.getBoundingClientRect();
			const containerRect = container.getBoundingClientRect();

			// Skip if popup hasn't rendered with dimensions yet
			if (popupRect.width === 0 || popupRect.height === 0) {
				return;
			}

			const viewportHeight = window.innerHeight;
			const viewportWidth = window.innerWidth;

			const position: { top?: number; bottom?: number; left?: number; right?: number } = {};
			const gap = 8; // 0.5rem gap between input and popup

		// Check vertical overflow
		const spaceBelow = viewportHeight - containerRect.bottom;
		const spaceAbove = containerRect.top;
		const popupHeight = popupRect.height;

		if (spaceBelow >= popupHeight + gap || spaceAbove < spaceBelow) {
			// Enough space below OR more space below than above - position below
			position.top = containerRect.bottom + gap;
		} else {
			// More space above - position above
			position.bottom = viewportHeight - containerRect.top + gap;
		}

		// Check horizontal overflow
		const spaceRight = viewportWidth - containerRect.left;
		const popupWidth = popupRect.width;

		if (spaceRight >= popupWidth) {
			// Enough space on the right - align to left edge
			position.left = containerRect.left;
		} else {
			// Not enough space on the right - align to right edge
			position.right = viewportWidth - containerRect.right;
		}

			setPopupPosition(position);
			setIsPositioned(true);
		});

		return () => cancelAnimationFrame(frame);
	}, [isOpen]);

	const handleDateSelect = (date: Date) => {
		if (!isDateInRange(date, minDate, maxDate)) return;

		setSelectedDate(date);
		setIsOpen(false);
		onChange?.(date);
	};

	const handleClear = (e: React.MouseEvent) => {
		e.stopPropagation();
		setSelectedDate(null);
		onChange?.(null);
	};

	const handleInputClick = () => {
		if (!disabled && !readonly) {
			setIsOpen(!isOpen);
		}
	};

	// Calendar navigation
	const handlePreviousMonth = () => {
		const newDate = new Date(currentMonth);
		newDate.setMonth(currentMonth.getMonth() - 1);
		setCurrentMonth(newDate);
	};

	const handleNextMonth = () => {
		const newDate = new Date(currentMonth);
		newDate.setMonth(currentMonth.getMonth() + 1);
		setCurrentMonth(newDate);
	};

	const handleToday = () => {
		const today = new Date();
		setCurrentMonth(today);
		if (isDateInRange(today, minDate, maxDate)) {
			handleDateSelect(today);
		}
	};

	// Get days for current month view
	const getMonthDays = () => {
		const year = currentMonth.getFullYear();
		const month = currentMonth.getMonth();
		const firstDay = new Date(year, month, 1);
		const lastDay = new Date(year, month + 1, 0);
		const daysInMonth = lastDay.getDate();
		const startDayOfWeek = firstDay.getDay();

		const days: (Date | null)[] = [];

		// Add empty cells for days before month starts
		for (let i = 0; i < startDayOfWeek; i++) {
			days.push(null);
		}

		// Add all days in month
		for (let i = 1; i <= daysInMonth; i++) {
			days.push(new Date(year, month, i));
		}

		return days;
	};

	const isSameDay = (date1: Date | null, date2: Date | null) => {
		if (!date1 || !date2) return false;
		return date1.toISOString().split('T')[0] === date2.toISOString().split('T')[0];
	};

	const isToday = (date: Date) => {
		const today = new Date();
		return isSameDay(date, today);
	};

	const days = getMonthDays();
	const formattedValue = formatDate(selectedDate, format);

	return (
		<div
			ref={containerRef}
			className={cn('lib-datepicker', className)}
			style={style}
			data-testid={dataTestId}
		>
			<div
				className={cn(
					'lib-datepicker-input-wrapper',
					error && 'lib-datepicker-error',
					disabled && 'lib-datepicker-disabled'
				)}
				onClick={handleInputClick}
			>
				<input
					id={id}
					name={name}
					type="text"
					value={formattedValue}
					placeholder={placeholder}
					disabled={disabled}
					readOnly
					className="lib-datepicker-input"
				/>
				<div className="lib-datepicker-icons">
					{clearable && selectedDate && !disabled && !readonly && (
						<button
							type="button"
							className="lib-datepicker-clear"
							onClick={handleClear}
							aria-label="Clear date"
						>
							✕
						</button>
					)}
					<span className="lib-datepicker-icon">📅</span>
				</div>
			</div>

			{isOpen && (
				<Portal>
					<div
						ref={popupRef}
						className="lib-datepicker-popup"
						style={{
							...(!isPositioned && { top: 0, left: 0 }),
							...popupPosition,
							opacity: isPositioned ? 1 : 0,
							pointerEvents: isPositioned ? 'auto' : 'none',
							transition: 'opacity 0.15s ease'
						}}
					>
						<div className="lib-datepicker-header">
						<button
							type="button"
							className="lib-datepicker-nav-btn"
							onClick={handlePreviousMonth}
							aria-label="Previous month"
						>
							‹
						</button>
						<div className="lib-datepicker-current-month">
							{MONTH_NAMES[currentMonth.getMonth()]} {currentMonth.getFullYear()}
						</div>
						<button
							type="button"
							className="lib-datepicker-nav-btn"
							onClick={handleNextMonth}
							aria-label="Next month"
						>
							›
						</button>
					</div>

					<div className="lib-datepicker-weekdays">
						{['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
							<div key={day} className="lib-datepicker-weekday">
								{day}
							</div>
						))}
					</div>

					<div className="lib-datepicker-days">
						{days.map((date, index) => {
							if (!date) {
								return <div key={`empty-${index}`} className="lib-datepicker-day-empty" />;
							}

							const isSelected = isSameDay(date, selectedDate);
							const isTodayDate = isToday(date);
							const isDisabled = !isDateInRange(date, minDate, maxDate);

							return (
								<button
									key={index}
									type="button"
									className={cn(
										'lib-datepicker-day',
										isSelected && 'lib-datepicker-day-selected',
										isTodayDate && 'lib-datepicker-day-today',
										isDisabled && 'lib-datepicker-day-disabled'
									)}
									onClick={() => !isDisabled && handleDateSelect(date)}
									disabled={isDisabled}
								>
									{date.getDate()}
								</button>
							);
						})}
					</div>

					<div className="lib-datepicker-footer">
						<button
							type="button"
							className="lib-datepicker-today-btn"
							onClick={handleToday}
						>
							Today
						</button>
					</div>
					</div>
				</Portal>
			)}
		</div>
	);
}
