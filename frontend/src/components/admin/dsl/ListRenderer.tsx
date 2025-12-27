/**
 * List Renderer
 *
 * DSL adapter for List library component.
 */

import { startTransition } from 'react';
import { List } from '../../library/List';
import type { ListComponent, ListItem as DSLListItem } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface ListRendererProps {
	component: ListComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function ListRenderer({ component, pageData, modalData, actionEngine }: ListRendererProps) {
	const {
		items: rawItems,
		variant = 'default',
		hoverable = false,
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const items = resolveValue(rawItems, context) as DSLListItem[];
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const listItems = items.map((item: DSLListItem) => ({
		label: resolveValue(item.label, context),
		description: item.description ? resolveValue(item.description, context) : undefined,
		icon: item.icon ? resolveValue(item.icon, context) : undefined,
		trailing: item.trailing ? resolveValue(item.trailing, context) : undefined,
		onClick: item.action && actionEngine ? () => {
			startTransition(() => {
				actionEngine.execute(item.action!, context);
			});
		} : undefined
	}));

	const listElement = (
		<List
			items={listItems}
			variant={variant}
			hoverable={hoverable}
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
		return listElement;
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
			{listElement}
		</ComponentWrapper>
	);
}
