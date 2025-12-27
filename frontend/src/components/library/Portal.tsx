/**
 * Portal Component
 *
 * Renders children into a DOM node outside the parent component hierarchy.
 * Useful for modals, tooltips, and popups to avoid overflow clipping.
 */

import { useMemo, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

export interface PortalProps {
	children: ReactNode;
	containerId?: string;
}

function getOrCreateContainer(containerId: string): HTMLElement {
	let element = document.getElementById(containerId);

	if (!element) {
		element = document.createElement('div');
		element.id = containerId;
		document.body.appendChild(element);
	}

	return element;
}

export function Portal({ children, containerId = 'portal-root' }: PortalProps) {
	// Create or get container synchronously on first render
	const container = useMemo(() => getOrCreateContainer(containerId), [containerId]);

	return createPortal(children, container);
}
