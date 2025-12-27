/**
 * Breadcrumbs Renderer
 *
 * DSL adapter for Breadcrumbs library component.
 */

import { startTransition } from 'react';
import { Breadcrumbs } from '../../library/Breadcrumbs';
import type { BreadcrumbsComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface BreadcrumbsRendererProps {
	component: BreadcrumbsComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function BreadcrumbsRenderer({ component, pageData, modalData, actionEngine }: BreadcrumbsRendererProps) {
	const { items, separator = '/', customStyle, className: rawClassName } = component;

	const context = { pageData, data: modalData };
	const resolvedItems = resolveValue(items, context);
	const resolvedSeparator = resolveValue(separator, context);
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const breadcrumbItems = resolvedItems.map((item: any) => {
		const resolvedLabel = resolveValue(item.label, context);
		const resolvedHref = item.href ? resolveValue(item.href, context) : undefined;

		return {
			label: resolvedLabel,
			href: resolvedHref,
			onClick: () => {
				if (item.action && actionEngine) {
					startTransition(() => {
						actionEngine.execute(item.action, { ...context, breadcrumb: item });
					});
				} else if (resolvedHref) {
					window.location.href = resolvedHref;
				}
			}
		};
	});

	const breadcrumbsElement = (
		<Breadcrumbs
			items={breadcrumbItems}
			separator={resolvedSeparator}
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
		return breadcrumbsElement;
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
			{breadcrumbsElement}
		</ComponentWrapper>
	);
}
