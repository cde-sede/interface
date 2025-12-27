/**
 * Spacer Component
 *
 * Layout component for adding white space between elements.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Spacer.css';

export type SpacerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type SpacerOrientation = 'horizontal' | 'vertical';

export interface SpacerProps extends BaseComponentProps {
	size?: SpacerSize;               /** Size of the space */
	orientation?: SpacerOrientation; /** Direction of the space */
}

export function Spacer({
	size = 'md',
	orientation = 'vertical',
	className,
	style,
	'data-testid': dataTestId
}: SpacerProps) {
	const spacerClassName = cn(
		'lib-spacer',
		`lib-spacer-${size}`,
		`lib-spacer-${orientation}`,
		className
	);

	return (
		<div
			className={spacerClassName}
			style={style}
			data-testid={dataTestId}
		/>
	);
}
