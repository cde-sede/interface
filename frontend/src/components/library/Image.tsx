/**
 * Image Component
 *
 * Responsive image with fit modes and styling options.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Image.css';

export type ImageFit = 'cover' | 'contain' | 'fill' | 'none' | 'scale-down';

export interface ImageProps extends BaseComponentProps {
	src: string;        /** Image source URL */
	alt?: string;       /** Alt text for accessibility */
	width?: string;     /** Image width */
	height?: string;    /** Image height */
	fit?: ImageFit;     /** Object fit mode */
	rounded?: boolean;  /** Rounded corners */
	bordered?: boolean; /** Show border */
}

export function Image({
	src,
	alt = '',
	width,
	height,
	fit = 'cover',
	rounded = false,
	bordered = false,
	className,
	style,
	'data-testid': dataTestId
}: ImageProps) {
	const imageClassName = cn(
		'lib-image',
		`lib-image-fit-${fit}`,
		rounded && 'lib-image-rounded',
		bordered && 'lib-image-bordered',
		className
	);

	const imageStyle: React.CSSProperties = { ...style };
	if (width) imageStyle.width = width;
	if (height) imageStyle.height = height;

	return (
		<div className="lib-image-container" data-testid={dataTestId}>
			<img src={src} alt={alt} className={imageClassName} style={imageStyle} />
		</div>
	);
}
