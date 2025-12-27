/**
 * Avatar Component
 *
 * Displays user avatar with image or initials, plus optional status indicator.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Avatar.css';

export type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type AvatarVariant = 'circle' | 'square' | 'rounded';
export type AvatarStatus = 'online' | 'offline' | 'away' | 'busy';

export interface AvatarProps extends BaseComponentProps {
	name: string;            /** User name for generating initials */
	src?: string;            /** Optional image source URL */
	size?: AvatarSize;       /** Size variant */
	variant?: AvatarVariant; /** Shape variant */
	status?: AvatarStatus;   /** Optional status indicator */
}

export function Avatar({
	name,
	src,
	size = 'md',
	variant = 'circle',
	status,
	className,
	style,
	'data-testid': dataTestId
}: AvatarProps) {
	const getInitials = (name: string): string => {
		return name
			.split(' ')
			.map(part => part[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	};

	const avatarClassName = cn(
		'lib-avatar',
		`lib-avatar-${size}`,
		`lib-avatar-${variant}`,
		status && `lib-avatar-status-${status}`,
		className
	);

	return (
		<div className="lib-avatar-container" data-testid={dataTestId}>
			<div className={avatarClassName} style={style}>
				{src ? (
					<img src={src} alt={name} className="lib-avatar-img" />
				) : (
					<span className="lib-avatar-initials">{getInitials(name)}</span>
				)}
				{status && <span className={`lib-avatar-status-indicator lib-avatar-status-indicator-${status}`} />}
			</div>
		</div>
	);
}
