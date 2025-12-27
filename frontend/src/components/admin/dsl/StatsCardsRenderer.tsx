/**
 * Stats Cards Renderer
 *
 * DSL adapter for StatsCards library component.
 */

import { StatsCards } from '../../library/StatsCards';
import type { StatsCardsComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';

interface StatsCardsRendererProps {
	component: StatsCardsComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function StatsCardsRenderer({ component, pageData, modalData, actionEngine }: StatsCardsRendererProps) {
	const { stats, columns = 4 } = component;

	const { customStyle, className: rawClassName } = component;
	const className = rawClassName ? String(rawClassName) : undefined;

	const statsCardsElement = (
		<StatsCards
			stats={stats || []}
			columns={columns}
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
		return statsCardsElement;
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
			{statsCardsElement}
		</ComponentWrapper>
	);
}
