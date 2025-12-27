/**
 * Dynamic Renderer - Action-triggered reloadable content
 *
 * Loads DSL components from an endpoint when triggered by actions.
 * Key features:
 * - Can be triggered multiple times
 * - Each trigger replaces the content (not appends)
 * - No caching - always fetches fresh content
 * - Simpler than Defer - only action-based triggering
 */

import { useState, useEffect, Fragment, startTransition } from 'react';
import type { DynamicComponent, ComponentDefinition } from './types';
import type { ActionEngine } from './actionEngine';
import { resolveValue, resolveAllValues, type ResolverContext } from './valueResolver';
import { renderComponent } from '../DSLRenderer';
import {
	registerDynamicAction,
	unregisterDynamicAction,
	type DynamicTriggerCallback
} from './dynamicRegistry';

interface DynamicRendererProps {
	component: DynamicComponent;
	pageData?: any;
	modalData?: any;
	actionEngine: ActionEngine;
}

export default function DynamicRenderer({
	component,
	pageData,
	modalData,
	actionEngine
}: DynamicRendererProps) {
	const triggerId = component.triggerId;

	// State
	const [content, setContent] = useState<ComponentDefinition[] | null>(component.initialContent || null);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [contentKey, setContentKey] = useState(0); // Unique key to force remount on content change

	// Debug: Log content changes
	useEffect(() => {
		// console.log('[DynamicRenderer] Content state changed:', {
		// 	triggerId,
		// 	contentLength: content?.length,
		// 	isLoading,
		// 	error,
		// 	contentKey,
		// 	content
		// });
	}, [content, isLoading, error, contentKey]);

	/**
	 * Load dynamic content from endpoint
	 * Can be called multiple times - always replaces content
	 */
	const loadContent = async () => {
		// Create context at trigger time with current data
		const context: ResolverContext = {
			pageData,
			data: modalData,
			store: window.datastore ? Object.fromEntries(window.datastore) : {}
		};

		// Resolve endpoint at trigger time (not mount time)
		let endpoint = resolveValue(component.endpoint, context) as string;
		const method = component.method || 'GET';

		// Build query parameters if provided
		if (component.params) {
			const resolvedParams = resolveAllValues(component.params, context);
			const queryString = new URLSearchParams(
				Object.entries(resolvedParams).map(([key, value]) => [
					key,
					String(value ?? '')
				])
			).toString();

			if (queryString) {
				endpoint += (endpoint.includes('?') ? '&' : '?') + queryString;
			}
		}

		// Execute onTrigger action if defined
		if (component.onTrigger && actionEngine) {
			startTransition(() => {
				actionEngine.execute(component.onTrigger!, context);
			});
		}

		// Fetch from endpoint
		setIsLoading(true);
		setError(null);

		try {
			const token = localStorage.getItem('auth_token');
			const headers: Record<string, string> = {
				'Content-Type': 'application/json',
				...component.headers
			};

			if (token) {
				headers['Authorization'] = `Bearer ${token}`;
			}

			const options: RequestInit = {
				method,
				headers
			};

			if (method !== 'GET' && component.body) {
				const resolvedBody = resolveAllValues(component.body, context);
				options.body = JSON.stringify(resolvedBody);
			}

			const response = await fetch(endpoint, options);

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const data = await response.json();

			// Expect response to be an array of ComponentDefinitions
			const components = Array.isArray(data) ? data : data.components || [];

			// console.log('[DynamicRenderer] Loaded content:', {
			// 	endpoint,
			// 	dataType: Array.isArray(data) ? 'array' : 'object',
			// 	dataLength: Array.isArray(data) ? data.length : 'N/A',
			// 	componentsLength: components.length,
			// 	components
			// });

			// Replace content (not append) and increment key to force remount
			setContent(components);
			setContentKey(prev => prev + 1);

			// Execute onLoad action if defined
			if (component.onLoad && actionEngine) {
				startTransition(() => {
					actionEngine.execute(component.onLoad!, { ...context, response: components });
				});
			}
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : String(err);
			setError(errorMessage);
			console.error('[DynamicRenderer] Failed to load content:', err);

			// Execute onError action if defined
			if (component.onError && actionEngine) {
				startTransition(() => {
					actionEngine.execute(component.onError!, { ...context, error: errorMessage });
				});
			}
		} finally {
			setIsLoading(false);
		}
	};

	/**
	 * Setup action trigger registration
	 */
	useEffect(() => {
		if (triggerId) {
			const callback: DynamicTriggerCallback = {
				load: () => loadContent()
			};

			registerDynamicAction(triggerId, callback);

			return () => {
				unregisterDynamicAction(triggerId, callback);
			};
		}
	}, [triggerId]);

	// Render loading state
	if (isLoading && component.loadingState) {
		return (
			<div>
				{renderComponent(component.loadingState, pageData, modalData, actionEngine)}
			</div>
		);
	}

	// Render error state
	if (error && component.errorState) {
		return (
			<div>
				{renderComponent(component.errorState, pageData, modalData, actionEngine)}
			</div>
		);
	}

	// Render error state (default)
	if (error) {
		return (
			<div style={{ padding: '1rem', color: 'var(--theme-error-text)' }}>
				<strong>Error loading content:</strong> {error}
			</div>
		);
	}

	// Render content when loaded
	if (content) {
		// console.log('[DynamicRenderer] Rendering content:', content.length, 'components with key:', contentKey);
		return (
			<div key={contentKey}>
				{content.map((comp, idx) => {
					// console.log('[DynamicRenderer] Rendering component', idx, ':', comp.type);
					return (
						<Fragment key={idx}>
							{renderComponent(comp, pageData, modalData, actionEngine)}
						</Fragment>
					);
				})}
			</div>
		);
	}

	// No content yet (waiting for first trigger)
	// console.log('[DynamicRenderer] No content, returning null');
	return null;
}
