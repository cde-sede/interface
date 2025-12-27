/**
 * Skeleton Component
 *
 * Loading placeholder with animation.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Skeleton.css';

export type SkeletonVariant = 'text' | 'circular' | 'rectangular' | 'rounded';
export type SkeletonAnimation = 'pulse' | 'wave' | 'none';

export interface SkeletonProps extends BaseComponentProps {
	variant?: SkeletonVariant;     /** Shape variant */
	width?: string;                /** Custom width */
	height?: string;               /** Custom height */
	count?: number;                /** Number of skeleton elements to render */
	animation?: SkeletonAnimation; /** Animation type */
}

export function Skeleton({
	variant = 'text',
	width,
	height,
	count = 1,
	animation = 'pulse',
	className,
	style,
	'data-testid': dataTestId
}: SkeletonProps) {
	const skeletonClassName = cn(
		'lib-skeleton',
		`lib-skeleton-${variant}`,
		`lib-skeleton-${animation}`,
		className
	);

	const skeletonStyle: React.CSSProperties = { ...style };
	if (width) skeletonStyle.width = width;
	if (height) skeletonStyle.height = height;

	const skeletons = Array.from({ length: count }, (_, index) => (
		<div
			key={index}
			className={skeletonClassName}
			style={skeletonStyle}
		/>
	));

	return (
		<div className="lib-skeleton-container" data-testid={dataTestId}>
			{skeletons}
		</div>
	);
}
