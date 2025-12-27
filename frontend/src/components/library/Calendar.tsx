/**
 * Calendar Component
 *
 * Full-featured calendar with multiple view modes.
 */

import { useState, type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Calendar.css';

export type CalendarView = 'month' | 'week' | 'day' | 'agenda';

export interface CalendarEvent {
	id: string;                     /** Event ID */
	title: string;                  /** Event title */
	start: string;                  /** Start date/time (ISO string) */
	end?: string;                   /** End date/time (ISO string) */
	allDay?: boolean;               /** All day event */
	color?: string;                 /** Event color */
	description?: string;           /** Event description */
	data?: any;                     /** Additional data */
}

export interface CalendarProps extends BaseComponentProps {
	events: CalendarEvent[];        /** Calendar events */
	view?: CalendarView;            /** Default view */
	defaultDate?: Date;             /** Default date to show */
	onEventClick?: (event: CalendarEvent) => void; /** Event click handler */
	onDateClick?: (date: Date) => void; /** Date click handler */
	height?: string;                /** Calendar height */
}

export function Calendar({
	events,
	view = 'month',
	defaultDate,
	onEventClick,
	onDateClick,
	height = 'auto',
	className,
	style,
	'data-testid': dataTestId
}: CalendarProps) {
	const [currentDate, setCurrentDate] = useState(defaultDate || new Date());
	const [currentView, setCurrentView] = useState(view);

	const getMonthDays = (date: Date) => {
		const year = date.getFullYear();
		const month = date.getMonth();
		const firstDay = new Date(year, month, 1);
		const lastDay = new Date(year, month + 1, 0);
		const daysInMonth = lastDay.getDate();
		const startDayOfWeek = firstDay.getDay();

		const days = [];
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

	const getWeekDays = (date: Date) => {
		const days = [];
		const startOfWeek = new Date(date);
		startOfWeek.setDate(date.getDate() - date.getDay());

		for (let i = 0; i < 7; i++) {
			const day = new Date(startOfWeek);
			day.setDate(startOfWeek.getDate() + i);
			days.push(day);
		}
		return days;
	};

	const getEventsForDate = (date: Date | null) => {
		if (!date) return [];
		const dateStr = date.toISOString().split('T')[0];
		return events.filter(event => {
			const eventStartDate = new Date(event.start).toISOString().split('T')[0];
			return eventStartDate === dateStr;
		});
	};

	const handlePrevious = () => {
		const newDate = new Date(currentDate);
		if (currentView === 'month') {
			newDate.setMonth(currentDate.getMonth() - 1);
		} else if (currentView === 'week') {
			newDate.setDate(currentDate.getDate() - 7);
		} else if (currentView === 'day') {
			newDate.setDate(currentDate.getDate() - 1);
		}
		setCurrentDate(newDate);
	};

	const handleNext = () => {
		const newDate = new Date(currentDate);
		if (currentView === 'month') {
			newDate.setMonth(currentDate.getMonth() + 1);
		} else if (currentView === 'week') {
			newDate.setDate(currentDate.getDate() + 7);
		} else if (currentView === 'day') {
			newDate.setDate(currentDate.getDate() + 1);
		}
		setCurrentDate(newDate);
	};

	const handleToday = () => {
		setCurrentDate(new Date());
	};

	const formatMonthYear = (date: Date) => {
		return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
	};

	const formatWeek = (date: Date) => {
		const weekStart = new Date(date);
		weekStart.setDate(date.getDate() - date.getDay());
		const weekEnd = new Date(weekStart);
		weekEnd.setDate(weekStart.getDate() + 6);
		return `${weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
	};

	const renderMonthView = (): ReactNode => {
		const days = getMonthDays(currentDate);
		const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

		return (
			<div className="lib-calendar-grid">
				<div className="lib-calendar-weekdays">
					{weekDays.map(day => (
						<div key={day} className="lib-calendar-weekday">{day}</div>
					))}
				</div>
				<div className="lib-calendar-days">
					{days.map((day, index) => {
						const dayEvents = getEventsForDate(day);
						const isToday = day && day.toDateString() === new Date().toDateString();

						return (
							<div
								key={index}
								className={cn(
									'lib-calendar-day',
									!day && 'lib-calendar-day-empty',
									isToday && 'lib-calendar-day-today'
								)}
								onClick={() => day && onDateClick?.(day)}
							>
								{day && (
									<>
										<div className="lib-calendar-day-number">{day.getDate()}</div>
										<div className="lib-calendar-day-events">
											{dayEvents.slice(0, 3).map((event, eventIndex) => (
												<div
													key={eventIndex}
													className="lib-calendar-event"
													style={{ backgroundColor: event.color || '#3b82f6' }}
													onClick={(e) => {
														e.stopPropagation();
														onEventClick?.(event);
													}}
												>
													{event.title}
												</div>
											))}
											{dayEvents.length > 3 && (
												<div className="lib-calendar-event-more">+{dayEvents.length - 3} more</div>
											)}
										</div>
									</>
								)}
							</div>
						);
					})}
				</div>
			</div>
		);
	};

	const renderWeekView = (): ReactNode => {
		const days = getWeekDays(currentDate);
		const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

		return (
			<div className="lib-calendar-week">
				{days.map((day, index) => {
					const dayEvents = getEventsForDate(day);
					const isToday = day.toDateString() === new Date().toDateString();

					return (
						<div key={index} className={cn('lib-calendar-week-day', isToday && 'lib-calendar-day-today')}>
							<div className="lib-calendar-week-day-header">
								<div className="lib-calendar-week-day-name">{weekDays[index]}</div>
								<div className="lib-calendar-week-day-number">{day.getDate()}</div>
							</div>
							<div className="lib-calendar-week-day-events">
								{dayEvents.map((event, eventIndex) => (
									<div
										key={eventIndex}
										className="lib-calendar-event"
										style={{ backgroundColor: event.color || '#3b82f6' }}
										onClick={() => onEventClick?.(event)}
									>
										{event.title}
									</div>
								))}
							</div>
						</div>
					);
				})}
			</div>
		);
	};

	const renderDayView = (): ReactNode => {
		const dayEvents = getEventsForDate(currentDate);

		return (
			<div className="lib-calendar-day-view">
				<div className="lib-calendar-day-view-header">
					{currentDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
				</div>
				<div className="lib-calendar-day-view-events">
					{dayEvents.length === 0 ? (
						<div className="lib-calendar-empty">No events for this day</div>
					) : (
						dayEvents.map((event, index) => (
							<div
								key={index}
								className="lib-calendar-day-event"
								style={{ borderLeftColor: event.color || '#3b82f6' }}
								onClick={() => onEventClick?.(event)}
							>
								<div className="lib-calendar-day-event-time">
									{new Date(event.start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
								</div>
								<div className="lib-calendar-day-event-content">
									<div className="lib-calendar-day-event-title">{event.title}</div>
									{event.description && <div className="lib-calendar-day-event-description">{event.description}</div>}
								</div>
							</div>
						))
					)}
				</div>
			</div>
		);
	};

	const renderAgendaView = (): ReactNode => {
		const sortedEvents = [...events].sort((a, b) => {
			const aStart = new Date(a.start);
			const bStart = new Date(b.start);
			return aStart.getTime() - bStart.getTime();
		});

		return (
			<div className="lib-calendar-agenda">
				{sortedEvents.length === 0 ? (
					<div className="lib-calendar-empty">No events</div>
				) : (
					sortedEvents.map((event, index) => {
						const start = new Date(event.start);
						return (
							<div
								key={index}
								className="lib-calendar-agenda-event"
								style={{ borderLeftColor: event.color || '#3b82f6' }}
								onClick={() => onEventClick?.(event)}
							>
								<div className="lib-calendar-agenda-event-date">
									{start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
								</div>
								<div className="lib-calendar-agenda-event-content">
									<div className="lib-calendar-agenda-event-title">{event.title}</div>
									{event.description && <div className="lib-calendar-agenda-event-description">{event.description}</div>}
								</div>
							</div>
						);
					})
				)}
			</div>
		);
	};

	return (
		<div
			className={cn('lib-calendar', className)}
			style={{ height, ...style }}
			data-testid={dataTestId}
		>
			<div className="lib-calendar-header">
				<div className="lib-calendar-navigation">
					<button className="lib-calendar-nav-button" onClick={handleToday}>Today</button>
					<button className="lib-calendar-nav-button" onClick={handlePrevious}>‹</button>
					<button className="lib-calendar-nav-button" onClick={handleNext}>›</button>
					<h3 className="lib-calendar-title">
						{currentView === 'month' && formatMonthYear(currentDate)}
						{currentView === 'week' && formatWeek(currentDate)}
						{currentView === 'day' && currentDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
						{currentView === 'agenda' && 'Agenda'}
					</h3>
				</div>
				<div className="lib-calendar-view-switcher">
					<button
						className={cn('lib-calendar-view-button', currentView === 'month' && 'active')}
						onClick={() => setCurrentView('month')}
					>
						Month
					</button>
					<button
						className={cn('lib-calendar-view-button', currentView === 'week' && 'active')}
						onClick={() => setCurrentView('week')}
					>
						Week
					</button>
					<button
						className={cn('lib-calendar-view-button', currentView === 'day' && 'active')}
						onClick={() => setCurrentView('day')}
					>
						Day
					</button>
					<button
						className={cn('lib-calendar-view-button', currentView === 'agenda' && 'active')}
						onClick={() => setCurrentView('agenda')}
					>
						Agenda
					</button>
				</div>
			</div>
			<div className="lib-calendar-content">
				{currentView === 'month' && renderMonthView()}
				{currentView === 'week' && renderWeekView()}
				{currentView === 'day' && renderDayView()}
				{currentView === 'agenda' && renderAgendaView()}
			</div>
		</div>
	);
}
