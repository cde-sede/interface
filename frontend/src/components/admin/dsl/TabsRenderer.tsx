/**
 * Tabs Renderer
 *
 * Renders tabbed interface from DSL definition
 */

import { useState } from 'react';
import type { TabsComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';
import { renderComponent } from '../DSLRenderer';

interface TabsRendererProps {
	component: TabsComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function TabsRenderer({ component, pageData, modalData, actionEngine }: TabsRendererProps) {
	const {
		items,
		defaultTab,
		variant = 'default',
		orientation = 'horizontal'
	} = component;

	const [activeTab, setActiveTab] = useState(defaultTab || items[0]?.id);

	const activeTabData = items.find(tab => tab.id === activeTab);

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const customClassName = rawClassName ? resolveValue(rawClassName, context) : undefined;
	const tabsClassName = customClassName
		? `dsl-tabs dsl-tabs-${variant} dsl-tabs-${orientation} ${customClassName}`
		: `dsl-tabs dsl-tabs-${variant} dsl-tabs-${orientation}`;

	const tabsElement = (
		<div className={tabsClassName} style={customStyle as React.CSSProperties}>
			<div className="dsl-tabs-list">
				{items.map(tab => {
					const resolvedLabel = resolveValue(tab.label, { pageData, data: modalData });
					const resolvedIcon = tab.icon ? resolveValue(tab.icon, { pageData, data: modalData }) : null;
					const isActive = tab.id === activeTab;

					return (
						<button
							key={tab.id}
							className={`dsl-tab ${isActive ? 'dsl-tab-active' : ''} ${tab.disabled ? 'dsl-tab-disabled' : ''}`}
							onClick={() => !tab.disabled && setActiveTab(tab.id)}
							disabled={tab.disabled}
						>
							{resolvedIcon && <span className="dsl-tab-icon">{resolvedIcon}</span>}
							<span className="dsl-tab-label">{resolvedLabel}</span>
						</button>
					);
				})}
			</div>

			<div className="dsl-tabs-content">
				{activeTabData?.content.map((comp, index) => (
					<div key={index} className="dsl-tab-component">
						{actionEngine && renderComponent(comp, pageData, modalData, actionEngine)}
					</div>
				))}
			</div>
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
		return tabsElement;
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
			{tabsElement}
		</ComponentWrapper>
	);
}
