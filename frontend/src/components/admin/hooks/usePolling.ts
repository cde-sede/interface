/**
 * Hook for setting up polling based on DSL configuration
 *
 * This hook reads the realtime.polling configuration from the DSL and
 * automatically sets up polling intervals that execute DSL actions.
 */

import { useEffect, useRef } from 'react';
import type { PollingConfig } from '../dsl/types';
import type { ActionEngine } from '../dsl/actionEngine';

interface UsePollingOptions {
	pollingConfig?: PollingConfig;
	actionEngine: ActionEngine;
	authToken: string | null;
}

export function usePolling({
	pollingConfig,
	actionEngine,
	authToken
}: UsePollingOptions) {
	const intervalRef = useRef<number | null>(null);

	useEffect(() => {
		if (!pollingConfig) {
			return;
		}

		const { interval, endpoint, method = 'GET', body, action } = pollingConfig;

		if (!endpoint) {
			console.warn('[Polling] No endpoint configured');
			return;
		}

		const poll = async () => {
			try {
				// console.log(`[Polling] Fetching from ${endpoint}`);

				const headers: Record<string, string> = {
					'Content-Type': 'application/json'
				};

				if (authToken) {
					headers['Authorization'] = `Bearer ${authToken}`;
				}

				const fetchOptions: RequestInit = {
					method,
					headers
				};

				if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
					fetchOptions.body = JSON.stringify(body);
				}

				const response = await fetch(endpoint, fetchOptions);

				if (!response.ok) {
					throw new Error(`Polling failed: ${response.statusText}`);
				}

				const data = await response.json();
				// console.log(`[Polling] Received data:`, data);

				// If action is defined, execute it with the poll response as context
				if (action) {
					// console.log(`[Polling] Executing DSL action`, action);
					await actionEngine.execute(action, { response: data, polling: true });
				}
			} catch (error) {
				console.error('[Polling] Error:', error);
			}
		};

		// Initial poll
		poll();

		// Set up interval
		intervalRef.current = setInterval(poll, interval);

		// Cleanup
		return () => {
			if (intervalRef.current) {
				clearInterval(intervalRef.current);
				intervalRef.current = null;
			}
		};
	}, [pollingConfig, actionEngine, authToken]);
}
