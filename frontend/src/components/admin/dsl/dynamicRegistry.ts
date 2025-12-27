/**
 * Dynamic Component Registry
 *
 * Global registry for triggering dynamic components via actions.
 * Separated from DynamicRenderer to avoid circular dependencies.
 */

export interface DynamicTriggerCallback {
	load: () => void;
}

const dynamicActionRegistry = new Map<string, Set<DynamicTriggerCallback>>();

/**
 * Register a dynamic component to be triggered by an action
 */
export function registerDynamicAction(actionId: string, callback: DynamicTriggerCallback) {
	if (!dynamicActionRegistry.has(actionId)) {
		dynamicActionRegistry.set(actionId, new Set());
	}
	dynamicActionRegistry.get(actionId)!.add(callback);
}

/**
 * Unregister a dynamic component
 */
export function unregisterDynamicAction(actionId: string, callback: DynamicTriggerCallback) {
	const callbacks = dynamicActionRegistry.get(actionId);
	if (callbacks) {
		callbacks.delete(callback);
		if (callbacks.size === 0) {
			dynamicActionRegistry.delete(actionId);
		}
	}
}

/**
 * Trigger all dynamic components registered for an action
 */
export function triggerDynamicAction(actionId: string) {
	const callbacks = dynamicActionRegistry.get(actionId);
	if (callbacks) {
		callbacks.forEach(callback => callback.load());
	}
}
