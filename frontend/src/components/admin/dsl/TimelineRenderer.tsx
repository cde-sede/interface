/**
 * Timeline Renderer
 *
 * DSL adapter for Timeline library component.
 */

import { Timeline } from '../../library/Timeline';
import type { TimelineComponent, TimelineItem as DSLTimelineItem } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface TimelineRendererProps {
	component: TimelineComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function TimelineRenderer({ component, pageData, modalData, actionEngine }: TimelineRendererProps) {
	const {
		items: rawItems,
		position = 'left',
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const items = resolveValue(rawItems, context) as DSLTimelineItem[];
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const timelineItems = items.map((item: DSLTimelineItem) => ({
		title: resolveValue(item.title, context),
		description: item.description ? resolveValue(item.description, context) : undefined,
		timestamp: item.timestamp ? resolveValue(item.timestamp, context) : undefined,
		icon: item.icon ? resolveValue(item.icon, context) : undefined,
		variant: item.variant
	}));

	const timelineElement = (
		<Timeline
			items={timelineItems}
			position={position}
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
		return timelineElement;
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
			{timelineElement}
		</ComponentWrapper>
	);
}
