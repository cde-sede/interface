/**
 * List Component
 *
 * Vertical list of clickable items.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './List.css';

export type ListVariant = 'default' | 'bordered' | 'divided';

export interface ListItem {
	label: string;        /** Item label */
	description?: string; /** Optional description */
	icon?: string;        /** Optional icon */
	trailing?: string;    /** Optional trailing content */
	onClick?: () => void; /** Click handler */
}

export interface ListProps extends BaseComponentProps {
	items: ListItem[];     /** Array of list items */
	variant?: ListVariant; /** Visual variant */
	hoverable?: boolean;   /** Enable hover effect */
}

export function List({
	items,
	variant = 'default',
	hoverable = false,
	className,
	style,
	'data-testid': dataTestId
}: ListProps) {
	if (!items || items.length === 0)
		return null;

	const listClassName = cn(
		'lib-list',
		`lib-list-${variant}`,
		className
	);

	const renderItem = (item: ListItem, index: number) => {
		const hasAction = Boolean(item.onClick);
		const itemClassName = cn(
			'lib-list-item',
			hasAction && 'lib-list-item-clickable',
			hoverable && 'lib-list-item-hoverable'
		);

		return (
			<div
				key={index}
				className={itemClassName}
				onClick={() => item.onClick?.()}
			>
				{item.icon && <span className="lib-list-item-icon">{item.icon}</span>}
				<div className="lib-list-item-content">
					<div className="lib-list-item-label">{item.label}</div>
					{item.description && <div className="lib-list-item-description">{item.description}</div>}
				</div>
				{item.trailing && <span className="lib-list-item-trailing">{item.trailing}</span>}
			</div>
		);
	};

	return (
		<div
			className={listClassName}
			style={style}
			data-testid={dataTestId}
		>
			{items.map((item, index) => renderItem(item, index))}
		</div>
	);
}
