/**
 * Calendar Renderer
 *
 * DSL adapter for Calendar library component.
 */

import { startTransition } from 'react';
import { Calendar } from '../../library/Calendar';
import type { CalendarEvent as LibCalendarEvent } from '../../library/Calendar';
import type { CalendarComponent, CalendarEvent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface CalendarRendererProps {
	component: CalendarComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function CalendarRenderer({ component, pageData, modalData, actionEngine }: CalendarRendererProps) {
	const {
		calendarEvents,
		view = 'month',
		defaultDate,
		onEventClick,
		onDateClick,
		height
	} = component;

	const resolvedEvents: CalendarEvent[] = resolveValue(calendarEvents, { pageData, data: modalData });
	const resolvedDefaultDate = defaultDate ? new Date(resolveValue(defaultDate, { pageData, data: modalData })) : undefined;
	const resolvedHeight = height ? resolveValue(height, { pageData, data: modalData }) : 'auto';

	// Map DSL events to library events
	const mappedEvents: LibCalendarEvent[] = resolvedEvents.map((event) => ({
		id: event.id,
		title: resolveValue(event.title, { pageData, data: modalData }),
		start: resolveValue(event.start, { pageData, data: modalData }),
		end: event.end ? resolveValue(event.end, { pageData, data: modalData }) : undefined,
		allDay: event.allDay,
		color: event.color ? resolveValue(event.color, { pageData, data: modalData }) : undefined,
		description: event.description ? resolveValue(event.description, { pageData, data: modalData }) : undefined,
		data: event.data
	}));

	// Event click handler
	const handleEventClick = onEventClick && actionEngine ? (event: LibCalendarEvent) => {
		startTransition(() => {
			actionEngine.execute(onEventClick, {
				pageData,
				data: modalData,
				event: event.data || event
			});
		});
	} : undefined;

	// Date click handler
	const handleDateClick = onDateClick && actionEngine ? (date: Date) => {
		startTransition(() => {
			actionEngine.execute(onDateClick, {
				pageData,
				data: modalData,
				date: date.toISOString()
			});
		});
	} : undefined;

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const calendarElement = (
		<Calendar
			events={mappedEvents}
			view={view}
			defaultDate={resolvedDefaultDate}
			onEventClick={handleEventClick}
			onDateClick={handleDateClick}
			height={resolvedHeight}
			style={customStyle as React.CSSProperties}
			className={className}
		/>
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
		return calendarElement;
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
			{calendarElement}
		</ComponentWrapper>
	);
}
