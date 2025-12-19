/**
 * Value Resolver for DSL
 *
 * Resolves ValueRef objects to actual values based on context.
 */

import type { ValueRef } from './types';

export interface ResolverContext {
	row?: any;
	form?: any;
	response?: any;
	pageData?: any;
	data?: any;
	error?: any;
	pagination?: any;
}

/**
 * Resolve a value reference to its actual value
 */
export function resolveValue(
	value: any,
	context: ResolverContext
): any {
	// If it's not an object or doesn't have a type field, return as-is
	if (typeof value !== 'object' || value === null || !('type' in value)) {
		return value;
	}

	const valueRef = value as ValueRef;

	switch (valueRef.type) {
		case 'literal':
			return valueRef.value;

		case 'field':
			return resolveFieldReference(valueRef, context);

		case 'computed':
			return resolveComputedValue(valueRef, context);

		case 'coalesce':
			return resolveCoalesceValue(valueRef, context);

		case 'conditional':
			return resolveConditionalValue(valueRef, context);

		default:
			console.warn('Unknown value reference type:', valueRef.type);
			return value;
	}
}

/**
 * Resolve a field reference like {type: "field", source: "row", path: "name"}
 */
function resolveFieldReference(
	valueRef: ValueRef,
	context: ResolverContext
): any {
	const { source, path } = valueRef;

	if (!source || !path) {
		console.warn('Field reference missing source or path:', valueRef);
		return undefined;
	}

	// Get the source object
	const sourceObj = context[source];

	if (!sourceObj) {
		console.warn(`Source "${source}" not found in context`);
		return undefined;
	}
	if (path == "self")
		return sourceObj;

	// Navigate the path (supports dot notation like "user.name")
	return getNestedValue(sourceObj, path);
}

/**
 * Resolve a computed value with template interpolation
 */
function resolveComputedValue(
	valueRef: ValueRef,
	context: ResolverContext
): string {
	const { template, values } = valueRef;

	if (!template) {
		console.warn('Computed value missing template:', valueRef);
		return '';
	}

	if (!values) {
		return template;
	}

	// Replace placeholders in template with resolved values
	let result = template;
	for (const [key, val] of Object.entries(values)) {
		const resolvedVal = resolveValue(val, context);
		result = result.replace(`{${key}}`, String(resolvedVal));
	}

	return result;
}

/**
 * Get a nested value from an object using dot notation
 * Example: getNestedValue({user: {name: "John"}}, "user.name") => "John"
 */
function getNestedValue(obj: any, path: string): any {
	const parts = path.split('.');
	let current = obj;

	for (const part of parts) {
		if (current === null || current === undefined) {
			return undefined;
		}
		current = current[part];
	}

	return current;
}

/**
 * Resolve a coalesce value (returns first non-null/undefined value)
 */
function resolveCoalesceValue(
	valueRef: ValueRef,
	context: ResolverContext
): any {
	const { options } = valueRef;

	if (!options || !Array.isArray(options)) {
		console.warn('Coalesce value missing options:', valueRef);
		return undefined;
	}

	// Try each option in order, return the first that's not null/undefined
	for (const option of options) {
		const resolved = resolveValue(option, context);
		if (resolved !== null && resolved !== undefined && resolved !== '') {
			return resolved;
		}
	}

	return undefined;
}

/**
 * Resolve a conditional value (ternary operator)
 */
function resolveConditionalValue(
	valueRef: ValueRef,
	context: ResolverContext
): any {
	const { condition, trueValue, falseValue } = valueRef;

	if (!condition || !trueValue || !falseValue) {
		console.warn('Conditional value missing required fields:', valueRef);
		return undefined;
	}

	const conditionResult = resolveValue(condition, context);

	// JavaScript truthy/falsy evaluation
	return conditionResult ? resolveValue(trueValue, context) : resolveValue(falseValue, context);
}

/**
 * Resolve all ValueRef objects in a nested structure
 */
export function resolveAllValues(
	data: any,
	context: ResolverContext
): any {
	if (Array.isArray(data)) {
		return data.map(item => resolveAllValues(item, context));
	}

	if (typeof data === 'object' && data !== null) {
		// Check if this is a ValueRef
		if ('type' in data && (data.type === 'literal' || data.type === 'field' || data.type === 'computed' || data.type === 'coalesce' || data.type === 'conditional')) {
			return resolveValue(data, context);
		}

		// Recursively resolve nested objects
		const resolved: any = {};
		for (const [key, value] of Object.entries(data)) {
			resolved[key] = resolveAllValues(value, context);
		}
		return resolved;
	}

	return data;
}

/**
 * Resolve data for a component
 * If data is a ValueRef, resolve it, otherwise return as-is
 */
export function resolveComponentData(
	data: any,
	pageData: any,
	modalData?: any
): any {
	if (!data) {
		return data;
	}

	// If data is a ValueRef, resolve it
	if (typeof data === 'object' && 'type' in data) {
		return resolveValue(data, { pageData, data: modalData });
	}

	return data;
}
