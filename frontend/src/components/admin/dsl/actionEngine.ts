/**
 * Action Engine for DSL
 *
 * Handles execution of actions defined in the DSL (API calls, modals, navigation, etc.)
 */

import type { ActionDefinition } from './types';
import { resolveAllValues, type ResolverContext } from './valueResolver';

export interface ActionEngineCallbacks {
  showToast: (message: string, type: 'success' | 'error' | 'info' | 'warning') => void;
  showConfirm: (message: string) => Promise<boolean>;
  openModal: (modalId: string, data?: any) => void;
  closeModal: (modalId: string) => void;
  navigate: (page: string) => void;
  refresh: () => void;
}

export class ActionEngine {
  private callbacks: ActionEngineCallbacks;
  private authToken: string | null;

  constructor(callbacks: ActionEngineCallbacks) {
	this.callbacks = callbacks;
	this.authToken = localStorage.getItem('auth_token');
  }

  /**
   * Execute an action with the given context
   */
  async execute(
	action: ActionDefinition,
	context: ResolverContext = {}
  ): Promise<any> {
	// Don't resolve the entire action upfront - resolve parts as needed
	// This prevents trying to resolve response data before the API call completes
	switch (action.type) {
	  case 'api-call':
		return this.executeApiCall(action, context);

	  case 'open-modal':
		console.log('[ActionEngine] Executing open-modal:', action);
		return this.executeOpenModal(action, context);

	  case 'close-modal':
		console.log('[ActionEngine] Executing close-modal:', action);
		return this.executeCloseModal(action, context);

	  case 'navigate':
		return this.executeNavigate(action);

	  case 'refresh':
		return this.executeRefresh();

	  case 'show-toast':
		return this.executeShowToast(action, context);

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
		console.log('[ActionEngine] API call success, onSuccess:', onSuccess);
		if (onSuccess.message) {
		  // Resolve the message if it's a ValueRef
		  const resolvedMessage = resolveAllValues(onSuccess.message, { ...context, response: data });
		  this.callbacks.showToast(resolvedMessage, 'success');
		}
		if (onSuccess.action) {
		  console.log('[ActionEngine] Chaining success action:', onSuccess.action);
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
	  console.log('[ActionEngine] Close modal has onSuccess, chaining:', onSuccess.action);
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

	// Resolve message with context
	const resolvedMessage = resolveAllValues(message, context) as string;

	this.callbacks.showToast(resolvedMessage, toastType);
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
