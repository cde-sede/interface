/**
 * Info Grid Renderer
 *
 * DSL adapter for InfoGrid library component.
 */

import { InfoGrid } from '../../library/InfoGrid';
import type { InfoGridComponent, InfoGridItem as DSLInfoGridItem } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface InfoGridRendererProps {
	component: InfoGridComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function InfoGridRenderer({ component, pageData, modalData, actionEngine }: InfoGridRendererProps) {
	const { items, columns } = component;

	const infoGridItems = items.map((item: DSLInfoGridItem) => ({
		label: item.label,
		value: resolveValue(item.value, { pageData, data: modalData }),
		type: item.type,
		icon: item.icon,
		copyable: item.copyable
	}));

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const infoGridElement = (
		<InfoGrid
			items={infoGridItems}
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
		return infoGridElement;
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
			{infoGridElement}
		</ComponentWrapper>
	);
}
