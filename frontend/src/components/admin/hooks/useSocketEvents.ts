/**
 * Hook for dynamically setting up Socket.IO event listeners based on DSL configuration
 *
 * This hook reads the realtime.socketEvents configuration from the DSL and
 * automatically registers the appropriate Socket.IO listeners.
 */

import { useEffect, useRef } from 'react';
import type { Socket } from 'socket.io-client';
import type { RealtimeConfig, SocketEventHandler } from '../dsl/types';
import type { ActionEngine } from '../dsl/actionEngine';

interface UseSocketEventsOptions {
	socket: Socket | null;
	realtimeConfig?: RealtimeConfig;
	currentPage: string;
	actionEngine: ActionEngine;
	onRefresh: () => void;
	onShowToast: (message: string, type: 'success' | 'error' | 'info' | 'warning') => void;
}

export function useSocketEvents({
	socket,
	realtimeConfig,
	currentPage,
	actionEngine,
	onRefresh,
	onShowToast
}: UseSocketEventsOptions) {
	const currentPageRef = useRef(currentPage);

	// Keep currentPage ref in sync
	useEffect(() => {
		currentPageRef.current = currentPage;
	}, [currentPage]);

	useEffect(() => {
		if (!socket || !realtimeConfig?.enabled || !realtimeConfig.socketEvents) {
			return;
		}

		const handlers: Array<{ event: string; handler: (data: any) => void }> = [];

		// Register each socket event handler from the DSL
		realtimeConfig.socketEvents.forEach((eventConfig: SocketEventHandler) => {
			const handler = async (data: any) => {
				// console.log(`[Socket.IO] Received event: "${eventConfig.event}"`, data);

				// If action is defined, execute it with the socket data as context
				if (eventConfig.action) {
					// console.log(`[Socket.IO] Executing DSL action for event "${eventConfig.event}"`, eventConfig.action);
					try {
						await actionEngine.execute(eventConfig.action, { data, socketEvent: eventConfig.event });
					} catch (error) {
						console.error(`[Socket.IO] Error executing action for event "${eventConfig.event}":`, error);
					}
					return;
				}

				// Fall back to legacy handler types if no action is defined
				if (!eventConfig.handler) {
					console.warn(`[Socket.IO] Event "${eventConfig.event}" has no action or handler defined`);
					return;
				}

				// Handle different handler types (legacy)
				switch (eventConfig.handler) {
					case 'refresh-page':
						// Refresh the current page if the event is for this page
						if (!data.page || data.page === currentPageRef.current) {
							// console.log(`[Socket.IO] Executing action: refresh-page (page: ${currentPageRef.current})`);
							onRefresh();
						} else {
							// console.log(`[Socket.IO] Ignoring refresh-page event (current page: ${currentPageRef.current}, event page: ${data.page})`);
						}
						break;

					case 'show-toast':
						// Show a toast notification
						const message = eventConfig.message || data.message || 'Notification';
						const type = data.type || 'info';
						// console.log(`[Socket.IO] Executing action: show-toast (type: ${type}, message: "${message}")`);
						onShowToast(message, type);
						break;

					case 'update-component':
						// Update a specific component (future enhancement)
						// console.log(`[Socket.IO] Executing action: update-component (componentId: ${eventConfig.componentId})`, data);
						console.warn('[Socket.IO] update-component handler not yet implemented');
						break;

					default:
						console.warn(`[Socket.IO] Unknown handler type: "${eventConfig.handler}" for event "${eventConfig.event}"`);
				}
			};

			// Register the handler with Socket.IO
			socket.on(eventConfig.event, handler);
			handlers.push({ event: eventConfig.event, handler });
		});

		// Cleanup: remove all registered handlers
		return () => {
			handlers.forEach(({ event, handler }) => {
				socket.off(event, handler);
			});
		};
	}, [socket, realtimeConfig, actionEngine, onRefresh, onShowToast]);
}
