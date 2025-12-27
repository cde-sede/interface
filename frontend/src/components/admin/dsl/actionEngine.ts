/**
 * Action Engine for DSL
 *
 * Handles execution of actions defined in the DSL (API calls, modals, navigation, etc.)
 */

import type { ActionDefinition, RichTextComponent } from './types';
import { resolveAllValues, type ResolverContext } from './valueResolver';
import { triggerDynamicAction } from './dynamicRegistry';

// Extend Window interface to include datastore
declare global {
	interface Window {
		datastore: Map<string, any>;
	}
}

export interface ActionEngineCallbacks {
	showToast: (message: string | RichTextComponent, type: 'success' | 'error' | 'info' | 'warning') => void;
	showConfirm: (message: string) => Promise<boolean>;
	openModal: (modalId: string, data?: any) => void;
	closeModal: (modalId: string) => void;
	openPanel: (panelId: string, data?: any) => void;
	closePanel: (panelId: string) => void;
	togglePanel: (panelId: string, data?: any) => void;
	navigate: (page: string) => void;
	refresh: () => void;
}

export class ActionEngine {
	private callbacks: ActionEngineCallbacks;
	private authToken: string | null;
	private dataStore: Map<string, any>;

	constructor(callbacks: ActionEngineCallbacks) {
		this.callbacks = callbacks;
		this.authToken = localStorage.getItem('auth_token');
		this.dataStore = new Map();
		window.datastore = this.dataStore;
	}

	/**
   * Execute an action with the given context
   */
	async execute(
		action: ActionDefinition,
		context: ResolverContext = {}
	): Promise<any> {
		// Add dataStore to context so it's always accessible
		const enrichedContext = {
			...context,
			store: Object.fromEntries(this.dataStore)
		};

		// Don't resolve the entire action upfront - resolve parts as needed
		// This prevents trying to resolve response data before the API call completes
		switch (action.type) {
			case 'api-call':
				return this.executeApiCall(action, enrichedContext);

			case 'open-modal':
				// console.log('[ActionEngine] Executing open-modal:', action);
				return this.executeOpenModal(action, enrichedContext);

			case 'close-modal':
				// console.log('[ActionEngine] Executing close-modal:', action);
				return this.executeCloseModal(action, enrichedContext);

			case 'navigate':
				return this.executeNavigate(action);

			case 'refresh':
				return this.executeRefresh();

			case 'show-toast':
				return this.executeShowToast(action, enrichedContext);

			case 'open-panel':
				// console.log('[ActionEngine] Executing open-panel:', action);
				return this.executeOpenPanel(action, enrichedContext);

			case 'close-panel':
				// console.log('[ActionEngine] Executing close-panel:', action);
				return this.executeClosePanel(action, enrichedContext);

			case 'toggle-panel':
				// console.log('[ActionEngine] Executing toggle-panel:', action);
				return this.executeTogglePanel(action, enrichedContext);

			case 'store-data':
				return this.executeStoreData(action, enrichedContext);

			case 'map':
			return this.executeMap(action, enrichedContext);

		case 'copy-to-clipboard':
			return this.executeCopyToClipboard(action, enrichedContext);

		case 'trigger-dynamic':
			return this.executeTriggerDynamic(action, enrichedContext);

			default:
				console.warn('Unknown action type:', action.type);
				return Promise.resolve();
		}
	}

	/**
   * Execute an API call action
   */
	private async executeApiCall(
		action: ActionDefinition,
		context: ResolverContext
	): Promise<any> {
		let { endpoint, method = 'POST', body, headers = {}, onSuccess, onError } = action;

		// Resolve endpoint, method, body with current context (before API call)
		const resolvedEndpoint = resolveAllValues(endpoint, context) as string;
		const resolvedMethod = resolveAllValues(method, context) as string;
		const resolvedBody = resolveAllValues(body, context);
		const resolvedHeaders = resolveAllValues(headers, context) as Record<string, string>;

		if (!resolvedEndpoint) {
			console.error('API call action missing endpoint');
			return;
		}

		try {
			const requestHeaders: Record<string, string> = {
				'Content-Type': 'application/json',
				...resolvedHeaders
			};

			if (this.authToken) {
				requestHeaders['Authorization'] = `Bearer ${this.authToken}`;
			}

			const fetchOptions: RequestInit = {
				method: resolvedMethod,
				headers: requestHeaders
			};

			if (resolvedBody && (resolvedMethod === 'POST' || resolvedMethod === 'PUT' || resolvedMethod === 'PATCH')) {
				fetchOptions.body = JSON.stringify(resolvedBody);
			}

			const response = await fetch(resolvedEndpoint, fetchOptions);

			// Handle authentication errors
			if (response.status === 401 || response.status === 403) {
				this.callbacks.showToast('Session expired. Please log in again.', 'error');
				localStorage.removeItem('auth_token');
				window.location.reload();
				return;
			}

			const data = await response.json();

			if (!response.ok) {
				throw new Error(data.error || `API call failed: ${response.statusText}`);
			}

			// Handle success
			if (onSuccess) {
				// console.log('[ActionEngine] API call success, onSuccess:', onSuccess);
				if (onSuccess.message) {
					// Resolve the message if it's a ValueRef
					const resolvedMessage = resolveAllValues(onSuccess.message, { ...context, response: data });
					this.callbacks.showToast(resolvedMessage, 'success');
				}
				if (onSuccess.action) {
					// console.log('[ActionEngine] Chaining success action:', onSuccess.action);
					// Chain the next action, passing response data
					await this.execute(onSuccess.action, { ...context, response: data });
				}
			}

			return data;
		} catch (error) {
			// Handle error
			const errorMessage = error instanceof Error ? error.message : String(error);

			if (onError && onError.message) {
				// Resolve the error message if it's a ValueRef
				const resolvedErrorMessage = resolveAllValues(onError.message, { ...context, error: errorMessage });
				this.callbacks.showToast(resolvedErrorMessage, 'error');
			} else {
				this.callbacks.showToast(`Error: ${errorMessage}`, 'error');
			}

			if (onError && onError.action) {
				await this.execute(onError.action, { ...context, error: errorMessage });
			}

			throw error;
		}
	}

	/**
   * Execute an open modal action
   */
	private executeOpenModal(
		action: ActionDefinition,
		context: ResolverContext
	): void {
		const { modalId, modalData } = action;

		if (!modalId) {
			console.error('Open modal action missing modalId');
			return;
		}

		// Resolve modal data with context
		const resolvedData = modalData ? resolveAllValues(modalData, context) : undefined;

		this.callbacks.openModal(modalId, resolvedData);
	}

	/**
   * Execute a close modal action
   */
	private async executeCloseModal(action: ActionDefinition, context: ResolverContext = {}): Promise<any> {
		const { modalId, message, toastType, onSuccess } = action;

		if (!modalId) {
			console.error('Close modal action missing modalId');
			return;
		}

		this.callbacks.closeModal(modalId);

		// Show toast if message is provided
		if (message) {
			const resolvedMessage = resolveAllValues(message, context) as string;
			this.callbacks.showToast(resolvedMessage, toastType || 'info');
		}

		// Handle onSuccess chaining
		if (onSuccess && onSuccess.action) {
			// console.log('[ActionEngine] Close modal has onSuccess, chaining:', onSuccess.action);
			await this.execute(onSuccess.action, context);
		}
	}

	/**
   * Execute a navigate action
   */
	private executeNavigate(action: ActionDefinition): void {
		const { page, url } = action;

		if (page) {
			this.callbacks.navigate(page);
		} else if (url) {
			window.location.href = url;
		} else {
			console.error('Navigate action missing page or url');
		}
	}

	/**
   * Execute a refresh action
   */
	private executeRefresh(): void {
		this.callbacks.refresh();
	}

	/**
   * Execute a show toast action
   */
	private executeShowToast(
		action: ActionDefinition,
		context: ResolverContext
	): void {
		const { message, toastType = 'info' } = action;

		if (!message) {
			console.error('Show toast action missing message');
			return;
		}

		// Check if message is a RichTextComponent
		if (typeof message === 'object' && 'type' in message && message.type === 'rich-text') {
			// Resolve the content field and pass the entire component
			const resolvedComponent = {
				...message,
				content: resolveAllValues(message.content, context)
			};
			this.callbacks.showToast(resolvedComponent as any, toastType);
		} else {
			// Resolve message with context for string/ValueRef
			const resolvedMessage = resolveAllValues(message, context) as string;
			this.callbacks.showToast(resolvedMessage, toastType);
		}
	}

	/**
   * Execute an open panel action
   */
	private executeOpenPanel(
		action: ActionDefinition,
		context: ResolverContext
	): void {
		const { panelId, panelData } = action;

		if (!panelId) {
			console.error('Open panel action missing panelId');
			return;
		}

		// Resolve panel data with context
		const resolvedData = panelData ? resolveAllValues(panelData, context) : undefined;

		this.callbacks.openPanel(panelId, resolvedData);
	}

	/**
   * Execute a close panel action
   */
	private executeClosePanel(
		action: ActionDefinition,
		_context: ResolverContext
	): void {
		const { panelId } = action;

		if (!panelId) {
			console.error('Close panel action missing panelId');
			return;
		}

		this.callbacks.closePanel(panelId);
	}

	/**
   * Execute a toggle panel action
   */
	private executeTogglePanel(
		action: ActionDefinition,
		context: ResolverContext
	): void {
		const { panelId, panelData } = action;

		if (!panelId) {
			console.error('Toggle panel action missing panelId');
			return;
		}

		// Resolve panel data with context
		const resolvedData = panelData ? resolveAllValues(panelData, context) : undefined;

		this.callbacks.togglePanel(panelId, resolvedData);
	}

	/**
   * Execute a store data action
   */
	private executeStoreData(
		action: ActionDefinition,
		context: ResolverContext
	): void {
		const { key, value } = action;

		if (!key) {
			console.error('Store data action missing key');
			return;
		}

		// Resolve key and value with context
		const resolvedKey = resolveAllValues(key, context) as string;
		const resolvedValue = resolveAllValues(value, context);

		// Store the data
		this.dataStore.set(resolvedKey, resolvedValue);
		// console.log(`[ActionEngine] Stored data: ${resolvedKey} =`, resolvedValue);
	}

	/**
   * Execute a map transformation action
   */
	private async executeMap(
		action: ActionDefinition,
		context: ResolverContext
	): Promise<any> {
		const { input, transform, output } = action;

		if (!transform) {
			console.error('Map action missing transform');
			return;
		}

		// Resolve input
		const resolvedInput = resolveAllValues(input, context);
		// console.log("resolved input:", resolvedInput);

		// Apply transformation
		const result = this.applyTransform(resolvedInput, transform);
		// console.log("result", result);

		// Store result if output key is provided
		if (output) {
			const resolvedOutput = resolveAllValues(output, context) as string;
			this.dataStore.set(resolvedOutput, result);
			// console.log(`[ActionEngine] Map result stored in: ${resolvedOutput}`);
		}

		return result;
	}

	/**
   * Apply a transformation to input data
   */
	private applyTransform(input: any, transform: string): any {
		// Handle array input - apply transformation elementwise
		if (Array.isArray(input)) {
			return input.map(item => this.applySingleTransform(item, transform));
		}

		// Handle single value (string or object)
		return this.applySingleTransform(input, transform);
	}

	/**
   * Apply transformation to a single element
   */
	private applySingleTransform(input: any, transform: string): any {
		// Filter transformation: /pattern/~> or .field>value~>
		if (transform.includes('~>')) {
			return this.applyFilterTransform(input, transform);
		}

		// Regex transformation: /pattern/->replacement
		if (transform.startsWith('/')) {
			return this.applyRegexTransform(input, transform);
		}

		// Object field selection: &->.field1,.field2
		if (transform.startsWith('&->')) {
			return this.applyObjectTransform(input, transform, 'object');
		}

		// Tuple field selection: #->.field1,.field2
		if (transform.startsWith('#->')) {
			return this.applyObjectTransform(input, transform, 'tuple');
		}

		console.warn('Unknown transform syntax:', transform);
		return input;
	}

	/**
   * Apply filter transformation to an array
   */
	private applyFilterTransform(input: any, transform: string): any {
		if (!Array.isArray(input)) {
			console.warn('Filter transform requires array input');
			return input;
		}

		// Check if it's a negated filter (~>!)
		const isNegated = transform.endsWith('~>!');
		const cleanTransform = isNegated ? transform.slice(0, -3) : transform.slice(0, -2);

		// Regex filter for strings: /pattern/~> or /pattern/~>!
		if (cleanTransform.startsWith('/') && cleanTransform.endsWith('/')) {
			const pattern = cleanTransform.slice(1, -1);
			try {
				const regex = new RegExp(pattern);
				return input.filter(item => {
					if (typeof item !== 'string') return !isNegated;
					const matches = regex.test(item);
					return isNegated ? !matches : matches;
				});
			} catch (error) {
				console.error('Invalid regex pattern:', pattern, error);
				return input;
			}
		}

		// Object comparison filter: .field>value~> or .field>value~>!
		// Supports: >, <, >=, <=, ==, !=
		const comparisonMatch = cleanTransform.match(/^\.([a-zA-Z0-9_.]+)(>=?|<=?|==|!=)(.+)$/);
		if (comparisonMatch) {
			const [, fieldPath, operator, valueStr] = comparisonMatch;
			const compareValue = this.parseComparisonValue(valueStr);

			return input.filter(item => {
				if (typeof item !== 'object' || item === null) return !isNegated;

				const fieldValue = this.getNestedValueFromObject(item, fieldPath);
				const matches = this.compareValues(fieldValue, operator, compareValue);
				return isNegated ? !matches : matches;
			});
		}

		console.warn('Unknown filter syntax:', transform);
		return input;
	}

	/**
   * Parse comparison value from string
   */
	private parseComparisonValue(valueStr: string): any {
		const trimmed = valueStr.trim();

		// Try parsing as number
		if (/^-?\d+\.?\d*$/.test(trimmed)) {
			return parseFloat(trimmed);
		}

		// Try parsing as boolean
		if (trimmed === 'true') return true;
		if (trimmed === 'false') return false;

		// Try parsing as null
		if (trimmed === 'null') return null;

		// Remove quotes if present
		if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
			(trimmed.startsWith("'") && trimmed.endsWith("'"))) {
			return trimmed.slice(1, -1);
		}

		return trimmed;
	}

	/**
   * Compare two values using an operator
   */
	private compareValues(a: any, operator: string, b: any): boolean {
		switch (operator) {
			case '>': return a > b;
			case '<': return a < b;
			case '>=': return a >= b;
			case '<=': return a <= b;
			case '==': return a == b;
			case '!=': return a != b;
			default: return false;
		}
	}

	/**
   * Apply regex transformation to a string
   */
	private applyRegexTransform(input: any, transform: string): any {
		if (typeof input !== 'string') {
			console.warn('Regex transform requires string input');
			return input;
		}

		// Parse: /pattern/->replacement
		const match = transform.match(/^\/(.*)\/->(.*)$/);
		if (!match) {
			console.warn('Invalid regex transform syntax:', transform);
			return input;
		}

		const [, pattern, replacement] = match;

		try {
			const regex = new RegExp(pattern, 'g');
			return input.replace(regex, replacement);
		} catch (error) {
			console.error('Invalid regex pattern:', pattern, error);
			return input;
		}
	}

	/**
   * Apply object field selection transformation
   */
	private applyObjectTransform(
		input: any,
		transform: string,
		mode: 'object' | 'tuple'
	): any {
		if (typeof input !== 'object' || input === null) {
			console.warn('Object transform requires object input');
			return input;
		}

		// Parse: &->.field1,.field2 or #->.field1,.field2
		const prefix = mode === 'object' ? '&->' : '#->';
		const fieldsStr = transform.substring(prefix.length);
		const fields = fieldsStr.split(',').map(f => f.trim().replace(/^\./, ''));
		// console.log(fields);

		if (mode === 'tuple') {
			// Return array of values
			return fields.map(field => this.getNestedValueFromObject(input, field));
		} else {
			// Return object with selected fields
			const result: Record<string, any> = {};
			fields.forEach(field => {
				const value = this.getNestedValueFromObject(input, field);
				// console.log("value:", value);
				// Use the last part of the field path as the key
				const key = field.includes('.') ? field.split('.').pop()! : field;
				result[key] = value;
			});
			return result;
		}
	}

	/**
   * Get nested value from object (similar to valueResolver's getNestedValue)
   */
	private getNestedValueFromObject(obj: any, path: string): any {
		const parts = path.split('.');
		let current = obj;

		for (const part of parts) {
			if (current === null || current === undefined) {
				return undefined;
			}

			const numericIndex = /^\d+$/.test(part) ? parseInt(part, 10) : null;

			if (numericIndex !== null && Array.isArray(current)) {
				current = current[numericIndex];
			} else {
				current = current[part];
			}
		}

		return current;
	}

	/**
   * Execute a copy to clipboard action
   */
	private async executeCopyToClipboard(
		action: ActionDefinition,
		context: ResolverContext
	): Promise<void> {
		const { copyValue, onSuccess, onError } = action;

		if (!copyValue) {
			console.error('Copy to clipboard action missing copyValue');
			return;
		}

		// Resolve the value to copy
		const resolvedValue = resolveAllValues(copyValue, context);
		const textToCopy = typeof resolvedValue === 'string'
			? resolvedValue
			: JSON.stringify(resolvedValue, null, 2);

		try {
			// Try modern Clipboard API first
			if (navigator.clipboard && navigator.clipboard.writeText) {
				await navigator.clipboard.writeText(textToCopy);
			} else {
				// Fallback for older browsers
				const textArea = document.createElement('textarea');
				textArea.value = textToCopy;
				textArea.style.cssText = 'position:fixed;left:-9999px;top:-9999px';
				document.body.appendChild(textArea);
				textArea.select();

				const successful = document.execCommand('copy');
				document.body.removeChild(textArea);

				if (!successful) {
					throw new Error('Fallback copy failed');
				}
			}

			// Handle success
			if (onSuccess) {
				const defaultMessage = 'Copied to clipboard!';
				if (onSuccess.message) {
					const resolvedMessage = resolveAllValues(onSuccess.message, context);
					this.callbacks.showToast(resolvedMessage as string, 'success');
				} else {
					this.callbacks.showToast(defaultMessage, 'success');
				}

				if (onSuccess.action) {
					await this.execute(onSuccess.action, context);
				}
			} else {
				// Default success message if no onSuccess handler
				this.callbacks.showToast('Copied to clipboard!', 'success');
			}
		} catch (error) {
			// Handle error

			if (onError && onError.message) {
				const resolvedErrorMessage = resolveAllValues(onError.message, context);
				this.callbacks.showToast(resolvedErrorMessage as string, 'error');
			} else {
				this.callbacks.showToast('Failed to copy to clipboard', 'error');
			}

			if (onError && onError.action) {
				await this.execute(onError.action, context);
			}

			console.error('Copy to clipboard failed:', error);
		}
	}

	/**
	 * Execute trigger dynamic action
	 */
	private async executeTriggerDynamic(
		action: ActionDefinition,
		_context: ResolverContext
	): Promise<void> {
		const { triggerId } = action;

		if (!triggerId) {
			console.error('Trigger dynamic action missing triggerId');
			return;
		}

		// Trigger all dynamic components with this ID
		triggerDynamicAction(triggerId);
	}

	/**
   * Execute an action with confirmation
   */
	async executeWithConfirmation(
		action: ActionDefinition,
		confirmMessage: string,
		context: ResolverContext = {}
	): Promise<any> {
		const confirmed = await this.callbacks.showConfirm(confirmMessage);
		if (!confirmed) {
			return Promise.resolve();
		}

		return this.execute(action, context);
	}
}
