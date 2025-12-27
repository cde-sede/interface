/**
 * Tabs Component
 *
 * Tabbed interface for organizing content.
 */

import { useState, type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Tabs.css';

export type TabsVariant = 'default' | 'pills' | 'underlined';
export type TabsOrientation = 'horizontal' | 'vertical';

export interface TabItem {
	id: string;         /** Unique tab ID */
	label: string;      /** Tab label */
	content: ReactNode; /** Tab content */
	icon?: string;      /** Optional icon */
	disabled?: boolean; /** Disabled state */
}

export interface TabsProps extends BaseComponentProps {
	items: TabItem[];                   /** Tab items */
	defaultTab?: string;                /** Default active tab */
	variant?: TabsVariant;              /** Visual variant */
	orientation?: TabsOrientation;      /** Tab orientation */
	onChange?: (tabId: string) => void; /** Tab change handler */
}

export function Tabs({
	items,
	defaultTab,
	variant = 'default',
	orientation = 'horizontal',
	onChange,
	className,
	style,
	'data-testid': dataTestId
}: TabsProps) {
	const [activeTab, setActiveTab] = useState(defaultTab || items[0]?.id);

	const handleTabClick = (tabId: string, disabled?: boolean) => {
		if (disabled) return;
		setActiveTab(tabId);
		onChange?.(tabId);
	};

	const activeTabContent = items.find(item => item.id === activeTab)?.content;

	const tabsClassName = cn(
		'lib-tabs',
		`lib-tabs-${variant}`,
		`lib-tabs-${orientation}`,
		className
	);

	return (
		<div
			className={tabsClassName}
			style={style}
			data-testid={dataTestId}
		>
			<div className="lib-tabs-list">
				{items.map((item) => {
					const isActive = activeTab === item.id;
					const tabClassName = cn(
						'lib-tab',
						isActive && 'lib-tab-active',
						item.disabled && 'lib-tab-disabled'
					);

					return (
						<button
							key={item.id}
							className={tabClassName}
							onClick={() => handleTabClick(item.id, item.disabled)}
							type="button"
							disabled={item.disabled}
						>
							{item.icon && <span>{item.icon}</span>}
							<span>{item.label}</span>
						</button>
					);
				})}
			</div>
			<div className="lib-tabs-content">
				{activeTabContent}
			</div>
		</div>
	);
}
