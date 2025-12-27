/**
 * Defer Renderer - Lazy loading DSL content
 *
 * Loads DSL components on-demand from an endpoint, with support for:
 * - Multiple trigger types (immediate, intersection, action, scroll, conditional)
 * - Loading and error states
 * - Global caching with TTL
 * - Viewport detection via Intersection Observer
 */

import { useState, useEffect, useRef, startTransition, Fragment } from 'react';
import type { DeferComponent, ComponentDefinition } from './types';
import type { ActionEngine } from './actionEngine';
import { resolveValue, resolveAllValues, type ResolverContext } from './valueResolver';
import { renderComponent } from '../DSLRenderer';

interface DeferRendererProps {
	component: DeferComponent;
	pageData?: any;
	modalData?: any;
	actionEngine: ActionEngine;
}

// Global cache for deferred content
interface CacheEntry {
	content: ComponentDefinition[];
	timestamp: number;
}

const deferCache = new Map<string, CacheEntry>();

// Global registry for action-triggered defer components
interface DeferTriggerCallback {
	load: () => void;
}

const deferActionRegistry = new Map<string, Set<DeferTriggerCallback>>();

/**
 * Register a defer component to be triggered by an action
 */
export function registerDeferAction(actionId: string, callback: DeferTriggerCallback) {
	if (!deferActionRegistry.has(actionId)) {
		deferActionRegistry.set(actionId, new Set());
	}
	deferActionRegistry.get(actionId)!.add(callback);
}

/**
 * Unregister a defer component
 */
export function unregisterDeferAction(actionId: string, callback: DeferTriggerCallback) {
	const callbacks = deferActionRegistry.get(actionId);
	if (callbacks) {
		callbacks.delete(callback);
		if (callbacks.size === 0) {
			deferActionRegistry.delete(actionId);
		}
	}
}

/**
 * Trigger all defer components registered for an action
 */
export function triggerDeferAction(actionId: string) {
	const callbacks = deferActionRegistry.get(actionId);
	if (callbacks) {
		callbacks.forEach(callback => callback.load());
	}
}

export default function DeferRenderer({
	component,
	pageData,
	modalData,
	actionEngine
}: DeferRendererProps) {
	// Resolve non-dynamic values
	const trigger = component.trigger || { type: 'immediate' };
	const cacheConfig = component.cache;

	// State
	const [content, setContent] = useState<ComponentDefinition[] | null>(null);
	const [isLoading, setIsLoading] = useState(trigger.type === 'immediate');  // Start loading for immediate triggers
	const [error, setError] = useState<string | null>(null);
	const [shouldLoad, setShouldLoad] = useState(trigger.type === 'immediate');

	// Refs
	const containerRef = useRef<HTMLDivElement>(null);
	const observerRef = useRef<IntersectionObserver | null>(null);
	const hasLoadedRef = useRef(false);

	/**
	 * Load deferred content from endpoint
	 */
	const loadContent = async () => {
		if (hasLoadedRef.current && !error) return; // Already loaded successfully

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

		// Special case: "#" endpoint means trigger hooks without fetching
		if (endpoint === '#') {
			setContent([]);
			hasLoadedRef.current = true;

			// Execute onLoad action without fetching
			if (component.onLoad && actionEngine) {
				startTransition(() => {
					actionEngine.execute(component.onLoad!, context);
				});
			}
			return;
		}

		// Check cache first
		if (cacheConfig?.enabled) {
			const cacheKey = cacheConfig.key
				? resolveValue(cacheConfig.key, context) as string
				: endpoint;

			const cached = deferCache.get(cacheKey);
			if (cached) {
				const age = Date.now() - cached.timestamp;
				const ttl = cacheConfig.ttl || Infinity;

				if (age < ttl) {
					// Cache hit
					setContent(cached.content);
					hasLoadedRef.current = true;

					// Execute onLoad action for cached content
					if (component.onLoad && actionEngine) {
						startTransition(() => {
							actionEngine.execute(component.onLoad!, context);
						});
					}
					return;
				} else {
					// Cache expired
					deferCache.delete(cacheKey);
				}
			}
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

			setContent(components);
			hasLoadedRef.current = true;

			// Update cache
			if (cacheConfig?.enabled) {
				const cacheKey = cacheConfig.key
					? resolveValue(cacheConfig.key, context) as string
					: endpoint;

				deferCache.set(cacheKey, {
					content: components,
					timestamp: Date.now()
				});
			}

			// Execute onLoad action if defined
			if (component.onLoad && actionEngine) {
				startTransition(() => {
					actionEngine.execute(component.onLoad!, { ...context, response: components });
				});
			}
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : String(err);
			setError(errorMessage);
			console.error('[DeferRenderer] Failed to load content:', err);

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
	 * Handle trigger based on type
	 */
	useEffect(() => {
		if (shouldLoad) {
			startTransition(() => {
				loadContent();
			});
		}
	}, [shouldLoad]);

	/**
	 * Setup intersection observer for viewport trigger
	 */
	useEffect(() => {
		if (trigger.type === 'intersection' && containerRef.current) {
			const options: IntersectionObserverInit = {
				rootMargin: trigger.rootMargin || '200px',
				threshold: trigger.threshold !== undefined ? trigger.threshold : 0.1
			};

			observerRef.current = new IntersectionObserver((entries) => {
				entries.forEach(entry => {
					if (entry.isIntersecting && !hasLoadedRef.current) {
						setShouldLoad(true);
					}
				});
			}, options);

			observerRef.current.observe(containerRef.current);

			return () => {
				if (observerRef.current) {
					observerRef.current.disconnect();
				}
			};
		}
	}, [trigger.type, trigger.rootMargin, trigger.threshold]);

	/**
	 * Setup scroll listener for scroll trigger
	 */
	useEffect(() => {
		if (trigger.type === 'scroll') {
			const handleScroll = () => {
				const scrollY = window.scrollY;
				const threshold = trigger.scrollThreshold || 500;

				if (scrollY >= threshold && !hasLoadedRef.current) {
					setShouldLoad(true);
				}
			};

			window.addEventListener('scroll', handleScroll, { passive: true });
			handleScroll(); // Check immediately

			return () => {
				window.removeEventListener('scroll', handleScroll);
			};
		}
	}, [trigger.type, trigger.scrollThreshold]);

	/**
	 * Setup conditional trigger
	 */
	useEffect(() => {
		if (trigger.type === 'conditional' && trigger.condition) {
			// Create fresh context for condition evaluation
			const context: ResolverContext = {
				pageData,
				data: modalData,
				store: window.datastore ? Object.fromEntries(window.datastore) : {}
			};
			const conditionResult = resolveValue(trigger.condition, context);

			if (conditionResult && !hasLoadedRef.current) {
				setShouldLoad(true);
			}
		}
	}, [trigger.type, trigger.condition, pageData, modalData]);

	/**
	 * Setup action trigger registration
	 */
	useEffect(() => {
		if (trigger.type === 'action' && trigger.actionId) {
			const callback: DeferTriggerCallback = {
				load: () => setShouldLoad(true)
			};

			registerDeferAction(trigger.actionId, callback);

			return () => {
				unregisterDeferAction(trigger.actionId!, callback);
			};
		}
	}, [trigger.type, trigger.actionId]);

	// Render loading state
	if (isLoading && component.loadingState) {
		return (
			<div ref={containerRef}>
				{renderComponent(component.loadingState, pageData, modalData, actionEngine)}
			</div>
		);
	}

	// Render error state
	if (error) {
		if (component.errorState) {
			return (
				<div ref={containerRef}>
					{renderComponent(component.errorState, pageData, modalData, actionEngine)}
				</div>
			);
		}

		if (component.fallback) {
			return (
				<div ref={containerRef}>
					{component.fallback.map((comp, idx) => (
						<div key={idx}>
							{renderComponent(comp, pageData, modalData, actionEngine)}
						</div>
					))}
				</div>
			);
		}

		// Default error display
		return (
			<div ref={containerRef} style={{ padding: '1rem', color: 'var(--theme-error-text)' }}>
				<strong>Error loading content:</strong> {error}
			</div>
		);
	}

	// Render content when loaded
	if (content) {
		// No wrapper div - just render components directly to avoid nesting
		return (
			<>
				{content.map((comp, idx) => (
					<Fragment key={idx}>
						{renderComponent(comp, pageData, modalData, actionEngine)}
					</Fragment>
				))}
			</>
		);
	}

	// Render placeholder for intersection/scroll/action/conditional triggers
	if (!shouldLoad) {
		if (component.loadingState) {
			return (
				<div ref={containerRef}>
					{renderComponent(component.loadingState, pageData, modalData, actionEngine)}
				</div>
			);
		}

		// Empty placeholder for intersection observer to detect
		return <div ref={containerRef} style={{ minHeight: '1px' }} />;
	}

	// Waiting for content - show loading state or nothing
	if (component.loadingState) {
		return (
			<div ref={containerRef}>
				{renderComponent(component.loadingState, pageData, modalData, actionEngine)}
			</div>
		);
	}

	// Don't show anything if no loading state is defined
	return <div ref={containerRef} style={{ minHeight: '1px' }} />;
}
