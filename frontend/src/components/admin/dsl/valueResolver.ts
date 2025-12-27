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
	// Component-specific context fields
	breadcrumb?: any;
	event?: any;
	date?: any;
	column?: any;
	value?: any;
	selectedRows?: any;
	rowIndex?: any;
	treeNode?: any;
	nodeId?: any;
	polling?: boolean;
	socketEvent?: string;
	// File upload context
	files?: File[];
	file?: { name: string; size: number; type: string };
	index?: number;
	remainingFiles?: File[];
	// Global datastore
	store?: Record<string, any>;
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

	// Check for RichTextComponent before treating as ValueRef
	// RichTextComponent has type='rich-text' but is not a ValueRef
	if (value.type === 'rich-text') {
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

		case 'transform':
			return resolveTransformValue(valueRef, context);

		case 'urlencode':
			return resolveUrlEncodeValue(valueRef, context);

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
		console.log('[ValueResolver] Computed template:', {
			template,
			key,
			val,
			resolvedVal,
			type: typeof resolvedVal
		});
		result = result.replace(`{${key}}`, String(resolvedVal));
	}

	console.log('[ValueResolver] Computed result:', result);
	return result;
}

/**
 * Get a nested value from an object using dot notation
 * Example: getNestedValue({user: {name: "John"}}, "user.name") => "John"
 * Supports array indexing: getNestedValue({items: [{id: 1}, {id: 2}]}, "items.0.id") => 1
 * Supports wildcard mapping: getNestedValue({items: [{name: "a"}, {name: "b"}]}, "items.*.name") => ["a", "b"]
 */
function getNestedValue(obj: any, path: string): any {
	const parts = path.split('.');
	let current = obj;

	for (let i = 0; i < parts.length; i++) {
		const part = parts[i];

		if (current === null || current === undefined) {
			return undefined;
		}

		// Handle wildcard operator for array mapping
		if (part === '*') {
			if (!Array.isArray(current)) {
				console.warn('Wildcard operator used on non-array value');
				return undefined;
			}

			// Get remaining path after the wildcard
			const remainingPath = parts.slice(i + 1).join('.');

			// If no remaining path, return the array as-is
			if (!remainingPath) {
				return current;
			}

			// Map over array and resolve remaining path for each element
			return current.map(item => getNestedValue(item, remainingPath));
		}

		// Check if part is a numeric index
		const numericIndex = /^\d+$/.test(part) ? parseInt(part, 10) : null;

		// If it's a numeric index and current is an array, use array indexing
		if (numericIndex !== null && Array.isArray(current)) {
			current = current[numericIndex];
		} else {
			// Otherwise use property access
			current = current[part];
		}
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
	for (let i = 0; i < options.length; i++) {
		const option = options[i];
		const resolved = resolveValue(option, context);
		console.log('[ValueResolver] Coalesce option', i, ':', {
			option,
			resolved,
			type: typeof resolved,
			isNullish: resolved === null || resolved === undefined
		});
		if (resolved !== null && resolved !== undefined) {
			console.log('[ValueResolver] Coalesce returning:', resolved);
			return resolved;
		}
	}

	console.log('[ValueResolver] Coalesce: all options were null/undefined, returning undefined');
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
 * Resolve a transform value (map/filter operations)
 */
function resolveTransformValue(
	valueRef: ValueRef,
	context: ResolverContext
): any {
	const { input, transform } = valueRef;

	if (!transform) {
		console.warn('Transform value reference missing transform');
		return undefined;
	}

	// Resolve input
	const resolvedInput = resolveValue(input, context);

	// Apply transformation
	let r = applyTransformOperation(resolvedInput, transform);
	console.log(r);
	return r;
}

/**
 * Apply a transformation to input data
 */
function applyTransformOperation(input: any, transform: string): any {
	// Handle chained transforms with concatenate at the end: #|->.name/.*/->$&\n|->
	// Need to split by |-> but NOT #|-> (which is the flatten map operator)

	// Use negative lookbehind to split on |-> that's not preceded by #
	const parts = transform.split(/(?<!#)\|->/);

	// If we have multiple parts, the last part is either empty (just concat) or a field getter
	if (parts.length > 1) {
		let result = input;

		// Apply all transforms except the last |-> part
		for (let i = 0; i < parts.length - 1; i++) {
			const part = parts[i];
			if (part) {
				result = applyTransformPart(result, part);
			}
		}

		// Now apply the concatenate operation
		const concatGetter = parts[parts.length - 1];
		return applyConcatenateTransform(result, concatGetter);
	}

	// No concatenate - use original logic
	return applyTransformPart(input, transform);
}

/**
 * Apply a single transform part (no concatenate)
 */
function applyTransformPart(input: any, transform: string): any {
	// Handle flatten map: #|->.field - extract field from each element and flatten
	if (transform.startsWith('#|->')) {
		return applyFlattenMapTransform(input, transform);
	}

	// Handle filter transformations on arrays
	if (transform.includes('~>')) {
		return applyFilterTransform(input, transform);
	}

	// Handle array input - apply transformation elementwise for non-filter operations
	if (Array.isArray(input) && !transform.includes('~>')) {
		return input.map(item => applySingleTransformOp(item, transform));
	}

	// Handle single value (string or object)
	return applySingleTransformOp(input, transform);
}

/**
 * Apply flatten map transformation
 * #|->.field - extract field from each element and return flat array
 * Example: [{name: "A"}, {name: "B"}] with #|->.name => ["A", "B"]
 * Supports chaining: #|->.name/.pattern/->replacement => extract name, then apply regex
 */
function applyFlattenMapTransform(input: any, transform: string): any {
	if (!Array.isArray(input)) {
		console.warn('Flatten map transform requires array input');
		return input;
	}

	// Parse: #|->.field1,.field2 followed optionally by more transforms
	const afterPrefix = transform.substring(4); // Remove '#|->'

	// Find where the field part ends (look for next transform operator: /, &, or #)
	// Field can contain dots and commas, but stops at transform operators
	// Use 's' flag to make . match newlines
	const nextTransformMatch = afterPrefix.match(/^([^/&#]+)(.*)$/s);

	if (!nextTransformMatch) {
		console.warn('Invalid flatten map syntax:', transform);
		return input;
	}

	const fieldsStr = nextTransformMatch[1];
	const remainingTransform = nextTransformMatch[2];

	const fields = fieldsStr.split(',').map(f => f.trim().replace(/^\./, ''));

	// Extract fields from each element and flatten
	let result = input.map(item => {
		if (fields.length === 1) {
			// Single field - just return the value
			return getNestedValue(item, fields[0]);
		} else {
			// Multiple fields - return array of values (will be flattened in result)
			return fields.map(field => getNestedValue(item, field));
		}
	}).flat();

	// If there's a remaining transform, apply it to the flattened array
	if (remainingTransform) {
		result = applyTransformPart(result, remainingTransform);
	}

	return result;
}

/**
 * Apply concatenate transformation
 * |->.field - get field from each element and concat
 * |-> - just concat array of strings
 */
function applyConcatenateTransform(input: any, getter: string): any {
	// Input must be an array
	if (!Array.isArray(input)) {
		console.warn('Concatenate transform requires array input, got:', typeof input);
		return input; // Return as-is instead of error
	}

	// If no getter specified, just concatenate the array elements
	if (!getter || getter.trim() === '') {
		return input.map(item => {
			if (typeof item === 'string') return item;
			if (typeof item === 'number') return String(item);
			if (typeof item === 'boolean') return String(item);
			if (item === null) return '';
			if (item === undefined) return '';
			// For objects/arrays, convert to JSON
			return JSON.stringify(item);
		}).join('');
	}

	// Getter specified - extract field/index from each element then concat
	const cleanGetter = getter.trim().replace(/^\./, ''); // Remove leading dot if present

	return input.map(item => {
		// Get nested value using the getter
		const value = getNestedValue(item, cleanGetter);

		// Convert to string
		if (typeof value === 'string') return value;
		if (typeof value === 'number') return String(value);
		if (typeof value === 'boolean') return String(value);
		if (value === null) return '';
		if (value === undefined) return '';
		// For objects/arrays, convert to JSON
		return JSON.stringify(value);
	}).join('');
}

/**
 * Apply transformation to a single element
 */
function applySingleTransformOp(input: any, transform: string): any {
	// Regex transformation: /pattern/->replacement
	if (transform.startsWith('/') && transform.includes('->')) {
		return applyRegexTransform(input, transform);
	}

	// Object field selection: &->.field1,.field2
	if (transform.startsWith('&->')) {
		return applyObjectTransform(input, transform, 'object');
	}

	// Tuple field selection: #->.field1,.field2
	if (transform.startsWith('#->')) {
		return applyObjectTransform(input, transform, 'tuple');
	}

	console.warn('Unknown transform syntax:', transform);
	return input;
}

/**
 * Apply filter transformation to an array
 */
function applyFilterTransform(input: any, transform: string): any {
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
	const comparisonMatch = cleanTransform.match(/^\.([a-zA-Z0-9_.]+)(>=?|<=?|==|!=)(.+)$/);
	if (comparisonMatch) {
		const [, fieldPath, operator, valueStr] = comparisonMatch;
		const compareValue = parseComparisonValue(valueStr);

		return input.filter(item => {
			if (typeof item !== 'object' || item === null) return !isNegated;

			const fieldValue = getNestedValue(item, fieldPath);
			const matches = compareValues(fieldValue, operator, compareValue);
			return isNegated ? !matches : matches;
		});
	}

	console.warn('Unknown filter syntax:', transform);
	return input;
}

/**
 * Apply regex transformation to a string
 */
function applyRegexTransform(input: any, transform: string): any {
	if (typeof input !== 'string') {
		console.warn('Regex transform requires string input');
		return input;
	}

	// Parse: /pattern/->replacement
	const match = transform.match(/^\/(.*)\/->(.*)$/s);
	if (!match) {
		console.warn('Invalid regex transform syntax:', transform);
		return input;
	}

	const [, pattern, replacement] = match;

	try {
		const regex = new RegExp(pattern, 'g');
		console.log(regex, replacement);

		// Apply regex replacement
		const result = input.replace(regex, replacement);

		// If the pattern can match empty strings (like /.*/), the 'g' flag causes
		// an extra match at the end. We need to detect and handle this.
		// Check if pattern matches empty string
		const emptyMatch = new RegExp(pattern).test('');

		if (emptyMatch && result.length > input.length) {
			// The pattern matches empty strings, which causes extra replacements
			// Use a non-global regex for patterns that match empty strings
			// Or add a positive lookahead to ensure at least one character
			const nonGlobalRegex = new RegExp(pattern);
			return input.replace(nonGlobalRegex, replacement);
		}

		return result;
	} catch (error) {
		console.error('Invalid regex pattern:', pattern, error);
		return input;
	}
}

/**
 * Apply object field selection transformation
 */
function applyObjectTransform(
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

	if (mode === 'tuple') {
		// Return array of values
		return fields.map(field => getNestedValue(input, field));
	} else {
		// Return object with selected fields
		const result: Record<string, any> = {};
		fields.forEach(field => {
			const value = getNestedValue(input, field);
			// Use the last part of the field path as the key
			const key = field.includes('.') ? field.split('.').pop()! : field;
			result[key] = value;
		});
		return result;
	}
}

/**
 * Parse comparison value from string
 */
function parseComparisonValue(valueStr: string): any {
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
function compareValues(a: any, operator: string, b: any): boolean {
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
		if ('type' in data && (data.type === 'literal' || data.type === 'field' || data.type === 'computed' || data.type === 'coalesce' || data.type === 'conditional' || data.type === 'transform')) {
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

/**
 * Resolve a URL encode value reference
 * Encodes a value using encodeURIComponent
 */
function resolveUrlEncodeValue(
	valueRef: ValueRef,
	context: ResolverContext
): string {
	const { encode } = valueRef;

	if (encode === undefined || encode === null) {
		console.warn('URL encode value reference missing encode field');
		return '';
	}

	// Resolve the value to encode
	const resolvedValue = resolveValue(encode, context);

	// Convert to string and URL encode
	const stringValue = String(resolvedValue ?? '');
	return encodeURIComponent(stringValue);
}
