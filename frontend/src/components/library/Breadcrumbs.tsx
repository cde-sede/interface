/**
 * Breadcrumbs Component
 *
 * Navigation breadcrumb trail showing current location in hierarchy.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Breadcrumbs.css';

export interface BreadcrumbItem {
	label: string;        /** Display label */
	href?: string;        /** Optional link href */
	onClick?: () => void; /** Click handler */
}

export interface BreadcrumbsProps extends BaseComponentProps {
	items: BreadcrumbItem[]; /** Array of breadcrumb items */
	separator?: string;      /** Separator character/string */
}

export function Breadcrumbs({
	items,
	separator = '/',
	className,
	style,
	'data-testid': dataTestId
}: BreadcrumbsProps) {
	const breadcrumbsClassName = cn('lib-breadcrumbs', className);

	return (
		<nav
			className={breadcrumbsClassName}
			style={style}
			data-testid={dataTestId}
			aria-label="Breadcrumb"
		>
			<ol className="lib-breadcrumbs-list">
				{items.map((item, index) => {
					const isLast = index === items.length - 1;

					return (
						<li key={index} className="lib-breadcrumbs-item">
							{!isLast && (item.onClick || item.href) ? (
								<button
									className="lib-breadcrumbs-link"
									onClick={item.onClick}
									type="button"
								>
									{item.label}
								</button>
							) : (
								<span className={cn(
									'lib-breadcrumbs-label',
									isLast && 'lib-breadcrumbs-current'
								)}>
									{item.label}
								</span>
							)}
							{!isLast && (
								<span className="lib-breadcrumbs-separator">{separator}</span>
							)}
						</li>
					);
				})}
			</ol>
		</nav>
	);
}
