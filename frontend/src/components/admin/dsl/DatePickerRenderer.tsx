/**
 * DatePicker Renderer
 *
 * DSL adapter for DatePicker library component.
 */

import { useState, startTransition } from 'react';
import { DatePicker, formatDate } from '../../library/DatePicker';
import type { DatePickerComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface DatePickerRendererProps {
	component: DatePickerComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function DatePickerRenderer({ component, pageData, modalData, actionEngine }: DatePickerRendererProps) {
	const {
		name,
		label,
		defaultValue,
		format = 'YYYY-MM-DD',
		placeholder,
		disabled = false,
		readonly = false,
		clearable = true,
		minDate,
		maxDate,
		onChange
	} = component;

	const context = { pageData, data: modalData };

	const resolvedLabel = label ? resolveValue(label, context) : undefined;
	const resolvedDefaultValue = defaultValue ? resolveValue(defaultValue, context) : null;
	const resolvedPlaceholder = placeholder ? resolveValue(placeholder, context) : undefined;
	const resolvedDisabled = resolveValue(disabled, context);
	const resolvedReadonly = resolveValue(readonly, context);
	const resolvedMinDate = minDate ? resolveValue(minDate, context) : undefined;
	const resolvedMaxDate = maxDate ? resolveValue(maxDate, context) : undefined;

	const [selectedDate, setSelectedDate] = useState<Date | null>(
		resolvedDefaultValue ? new Date(resolvedDefaultValue) : null
	);

	const handleChange = (date: Date | null) => {
		setSelectedDate(date);

		if (onChange && actionEngine) {
			startTransition(() => {
				actionEngine.execute(onChange, {
					pageData,
					data: modalData,
					form: { [name]: date ? formatDate(date, format) : null }
				});
			});
		}
	};

	const { customStyle, className: rawClassName } = component;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const datePickerElement = (
		<div className="dsl-date-picker-field" style={customStyle as React.CSSProperties}>
			{resolvedLabel && (
				<label htmlFor={name} className="dsl-date-picker-label">
					{resolvedLabel}
				</label>
			)}
			<DatePicker
				id={name}
				name={name}
				value={selectedDate}
				onChange={handleChange}
				format={format}
				placeholder={resolvedPlaceholder}
				disabled={resolvedDisabled}
				readonly={resolvedReadonly}
				clearable={clearable}
				minDate={resolvedMinDate}
				maxDate={resolvedMaxDate}
				className={className}
			/>
		</div>
	);

	// Only use ComponentWrapper if we have wrapper-level properties
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
		return datePickerElement;
	}

	// Create a component object without customStyle/className to avoid duplication
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
			{datePickerElement}
		</ComponentWrapper>
	);
}
