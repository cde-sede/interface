import { useState, useEffect, useRef } from 'react';
import './ApiDocs.css';
import { ThemePicker } from './ThemePicker';

interface RouteInfo {
	name: string;
	url: string;
}

interface ApiModule {
	name: string;
	blueprint: string;
	parent: string | null;
	url_prefix: string;
	routes: RouteInfo[];
}

interface ParamDef {
	type: string;
	required: boolean;
	description: string;
	in: 'path' | 'query' | 'body' | 'header';
}

interface EndpointDoc {
	function: string;
	description: string;
	docstring: string | null;
	route?: string | null;
	params?: Record<string, ParamDef>;
	method?: string;
	type?: 'route' | 'specs';
	documentation?: string;
	_index?: number;
}

interface ApiDocsData {
	apis: ApiModule[];
}

export default function ApiDocs() {
	const [apis, setApis] = useState<ApiModule[]>([]);
	const [selectedApiName, setSelectedApiName] = useState<string | null>(null);
	const [endpoints, setEndpoints] = useState<EndpointDoc[]>([]);
	const [endpointDetails, setEndpointDetails] = useState<EndpointDoc[]>([]);
	const [activeEndpoint, setActiveEndpoint] = useState<string | null>(null);
	const [testResponse, setTestResponse] = useState<Record<string, string>>({});
	const [loading, setLoading] = useState<Record<string, boolean>>({});
	const [loadingEndpoints, setLoadingEndpoints] = useState(false);
	const [paramValues, setParamValues] = useState<Record<string, Record<string, string>>>({});

	// Refs for scroll-spy
	const endpointRefs = useRef<Record<string, HTMLDivElement | null>>({});
	const mainRef = useRef<HTMLDivElement | null>(null);
	const responseRefs = useRef<Record<string, HTMLDivElement | null>>({});

	// Cache for endpoint details by API name
	const endpointCache = useRef<Record<string, { endpoints: EndpointDoc[], details: EndpointDoc[] }>>({});

	// Build base path recursively
	const buildBasePath = (apiName: string, apisMap: Map<string, ApiModule>): string => {
		const api = apisMap.get(apiName);
		if (!api) return '';

		const parentBase = api.parent ? buildBasePath(api.parent, apisMap) : '';
		return parentBase + api.url_prefix;
	};

	// Fetch all APIs
	useEffect(() => {
		fetch('http://localhost:5000/api/')
			.then(async res => {
				if (!res.ok) {
					const text = await res.text();
					throw new Error(`HTTP ${res.status}: ${text}`);
				}
				try {
					return await res.json();
				} catch (e) {
					throw new Error(`Invalid JSON response: ${e}`);
				}
			})
			.then((data: ApiDocsData) => setApis(data.apis))
			.catch(err => console.error('Failed to fetch APIs:', err));
	}, []);

	// Clear cache function
	const clearCache = () => {
		endpointCache.current = {};
		// Reload current API if one is selected
		if (selectedApiName) {
			const currentApi = selectedApiName;
			setSelectedApiName(null);
			setTimeout(() => setSelectedApiName(currentApi), 0);
		}
	};

	// Fetch endpoints for selected API and load all details
	useEffect(() => {
		if (!selectedApiName) return;

		// Check cache first
		const cached = endpointCache.current[selectedApiName];
		if (cached) {
			// Instant swap with cached data
			setEndpoints(cached.endpoints);
			setEndpointDetails(cached.details);
			setLoadingEndpoints(false);
			if (cached.details.length > 0) {
				setActiveEndpoint(cached.details[0].function);
			}
			return;
		}

		// No cache - grey out current and load new
		setLoadingEndpoints(true);
		// Keep old endpoints visible but greyed out
		// Only clear if there are no endpoints (first load)
		if (endpoints.length === 0) {
			setEndpoints([]);
			setEndpointDetails([]);
		}
		setActiveEndpoint(null);

		// Build base path for the selected API
		const apisMap = new Map(apis.map(api => [api.name, api]));
		const basePath = buildBasePath(selectedApiName, apisMap);

		// Fetch list of endpoints
		fetch(`http://localhost:5000${basePath}/describe`)
			.then(async res => {
				if (!res.ok) {
					const text = await res.text();
					throw new Error(`HTTP ${res.status}: ${text}`);
				}
				try {
					return await res.json();
				} catch (e) {
					throw new Error(`Invalid JSON response: ${e}`);
				}
			})
			.then(data => {
				console.log('Fetched endpoints:', data);
				const endpointList = data.functions || [];

				// Fetch details for all endpoints
				return Promise.all(
					endpointList.map((endpoint: EndpointDoc) =>
						fetch(`http://localhost:5000${basePath}/describe?f=${encodeURIComponent(endpoint.function)}`)
							.then(async res => {
								if (!res.ok) {
									console.error(`HTTP ${res.status} for ${endpoint.function}`);
									return null;
								}
								try {
									return await res.json();
								} catch (e) {
									console.error(`Invalid JSON for ${endpoint.function}:`, e);
									return null;
								}
							})
							.catch(err => {
								console.error(`Failed to fetch details for ${endpoint.function}:`, err);
								return null;
							})
					)
				).then(details => ({ endpointList, details }));
			})
			.then(({ endpointList, details }) => {
				const validDetails = details.filter(d => d !== null);
				console.log('Fetched all endpoint details:', validDetails);

				// Store in cache
				endpointCache.current[selectedApiName] = {
					endpoints: endpointList,
					details: validDetails
				};

				// Update state
				setEndpoints(endpointList);
				setEndpointDetails(validDetails);
				// Set first endpoint as active
				if (validDetails.length > 0) {
					setActiveEndpoint(validDetails[0].function);
				}
			})
			.catch(err => {
				console.error('Failed to fetch endpoints:', err);
				setEndpoints([]);
				setEndpointDetails([]);
			})
			.finally(() => setLoadingEndpoints(false));
	}, [selectedApiName, apis]);

	// Scroll-spy: Intersection Observer to track visible endpoints
	useEffect(() => {
		if (!mainRef.current || endpointDetails.length === 0) return;

		const observer = new IntersectionObserver(
			(entries) => {
				// Find the entry with the highest intersection ratio
				const visibleEntry = entries
					.filter(entry => entry.isIntersecting)
					.sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

				if (visibleEntry) {
					const endpointName = visibleEntry.target.getAttribute('data-endpoint');
					if (endpointName) {
						setActiveEndpoint(endpointName);
					}
				}
			},
			{
				root: mainRef.current,
				rootMargin: '-20% 0px -70% 0px',
				threshold: [0, 0.25, 0.5, 0.75, 1]
			}
		);

		// Observe all endpoint sections
		Object.values(endpointRefs.current).forEach(ref => {
			if (ref) observer.observe(ref);
		});

		return () => observer.disconnect();
	}, [endpointDetails]);

	// Scroll to endpoint when sidebar item is clicked
	const scrollToEndpoint = (endpointName: string) => {
		const element = endpointRefs.current[endpointName];
		if (element && mainRef.current) {
			element.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	};

	// Smart scroll for response after execute
	const scrollToResponse = (endpointName: string) => {
		// Use setTimeout to ensure the DOM has updated with the response
		setTimeout(() => {
			const responseElement = responseRefs.current[endpointName];
			const mainElement = mainRef.current;

			if (!responseElement || !mainElement) return;

			const MARGIN_TOP = 0; // pixels of space above response
			const MARGIN_BOTTOM = 0; // pixels of space below response

			const responseRect = responseElement.getBoundingClientRect();
			const mainRect = mainElement.getBoundingClientRect();
			const viewportHeight = mainRect.height;
			const responseHeight = responseRect.height;

			// Available height considering margins
			const availableHeight = viewportHeight - MARGIN_TOP - MARGIN_BOTTOM;

			// If response is bigger than available viewport (with margins), scroll to top with margin
			if (responseHeight > availableHeight) {
				const elementTop = responseElement.offsetTop;
				const targetScroll = elementTop - MARGIN_TOP;

				mainElement.scrollTo({ top: targetScroll, behavior: 'smooth' });
			} else {
				// If response is smaller, check if bottom is visible with margin
				const responseBottom = responseRect.bottom;
				const mainBottom = mainRect.bottom;

				// If bottom is not visible (accounting for bottom margin), scroll to show it
				if (responseBottom > mainBottom - MARGIN_BOTTOM) {
					const elementTop = responseElement.offsetTop;
					const elementBottom = elementTop + responseHeight;
					const targetScroll = elementBottom - viewportHeight + MARGIN_BOTTOM;

					mainElement.scrollTo({ top: targetScroll, behavior: 'smooth' });
				}
			}
		}, 100);
	};

	const testEndpoint = async (endpointName: string, route: string, method: string, params?: Record<string, ParamDef>) => {
		setLoading(prev => ({ ...prev, [endpointName]: true }));
		// Don't clear the response immediately to avoid flicker - keep old response while loading

		try {
			let url = `http://localhost:5000${route}`;
			let body: any = undefined;
			const queryParams: Record<string, string> = {};
			const headers: Record<string, string> = {};

			// Get param values for this specific endpoint
			const endpointParams = paramValues[endpointName] || {};

			// Process parameters
			if (params) {
				for (const [key, def] of Object.entries(params)) {
					const value = endpointParams[key];

					if (def.required && !value) {
						setTestResponse(prev => ({ ...prev, [endpointName]: `Error: Required parameter "${key}" is missing` }));
						setLoading(prev => ({ ...prev, [endpointName]: false }));
						scrollToResponse(endpointName);
						return;
					}

					if (value) {
						if (def.in === 'path') {
							// Replace path parameter
							url = url.replace(`{${key}}`, encodeURIComponent(value));
						} else if (def.in === 'query') {
							queryParams[key] = value;
						} else if (def.in === 'body') {
							if (!body) body = {};
							body[key] = value;
						} else if (def.in === 'header') {
							headers[key] = value;
						}
					}
				}
			}

			// Add query params to URL
			if (Object.keys(queryParams).length > 0) {
				const queryString = new URLSearchParams(queryParams).toString();
				url += `?${queryString}`;
			}

			// Make request
			const options: RequestInit = {
				method,
				headers: { ...headers },
			};

			if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
				options.headers = { ...options.headers, 'Content-Type': 'application/json' };
				options.body = JSON.stringify(body);
			}

			const res = await fetch(url, options);
			const responseText = await res.text();

			if (!res.ok) {
				setTestResponse(prev => ({ ...prev, [endpointName]: `HTTP ${res.status} Error:\n${responseText}` }));
				scrollToResponse(endpointName);
				return;
			}

			let data;
			try {
				data = JSON.parse(responseText);
			} catch (e) {
				setTestResponse(prev => ({ ...prev, [endpointName]: `Invalid JSON response:\n${responseText}` }));
				scrollToResponse(endpointName);
				return;
			}

			setTestResponse(prev => ({ ...prev, [endpointName]: JSON.stringify(data, null, 2) }));
			scrollToResponse(endpointName);
		} catch (err) {
			setTestResponse(prev => ({ ...prev, [endpointName]: `Error: ${err}` }));
			scrollToResponse(endpointName);
		} finally {
			setLoading(prev => ({ ...prev, [endpointName]: false }));
		}
	};

	return (
		<div className="api-docs">
			<header className="api-docs-header">
				<div className="header-content">
					<div className="header-text">
						<h1>API Documentation</h1>
						<p>Interactive API testing and documentation</p>
					</div>
					<ThemePicker />
				</div>
			</header>

			<div className="api-docs-content">
				<aside className="api-sidebar">
					<div className="sidebar-section">
						<h2>API Modules</h2>
						<div className="sidebar-scroll">
							<div className="api-list">
								{apis.filter(api => api.name !== 'api').map(api => (
									<div
										key={api.blueprint}
										className={`api-item ${selectedApiName === api.name ? 'active' : ''}`}
										onClick={() => {
											console.log(`Clicked API: ${api.name}`);
											setSelectedApiName(api.name);
											setActiveEndpoint(null);
											setTestResponse({});
										}}
									>
										<span className="api-name">{api.name}</span>
										<span className="api-blueprint">{api.blueprint}</span>
									</div>
								))}
							</div>
						</div>
					</div>

					<div className="sidebar-section">
						<div className="sidebar-section-header">
							<h3>Sections</h3>
							<button
								className="cache-clear-button"
								onClick={clearCache}
								title="Clear cache and reload"
								aria-label="Clear cache"
							>
								<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
									<path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
								</svg>
							</button>
						</div>
						<div className="sidebar-scroll">
							{selectedApiName && endpoints.length > 0 && (
								<div className={`endpoint-list ${loadingEndpoints ? 'loading' : ''}`}>
									{endpoints.map(endpoint => (
										<div
											key={endpoint.function}
											className={`endpoint-item ${activeEndpoint === endpoint.function ? 'active' : ''}`}
											onClick={() => scrollToEndpoint(endpoint.function)}
										>
											<span className="endpoint-name">{endpoint.function}</span>
											<span className="endpoint-desc">{endpoint.description}</span>
										</div>
									))}
								</div>
							)}
						</div>
					</div>
				</aside>

				<main className="api-main" ref={mainRef}>
					{loadingEndpoints && endpointDetails.length === 0 ? (
						<div className="empty-state">
							<p>Loading endpoint details...</p>
						</div>
					) : selectedApiName && endpointDetails.length > 0 ? (
						<div className="endpoints-container">
							{endpointDetails.map((endpointDetail) => (
								<div
									key={endpointDetail.function}
									className="endpoint-detail"
									ref={(el) => {
										endpointRefs.current[endpointDetail.function] = el;
									}}
									data-endpoint={endpointDetail.function}
								>
									<div className="endpoint-header">
										<h2>{endpointDetail.function}</h2>
										<span className={`http-method method-${endpointDetail.method?.toLowerCase() || 'get'}`}>
											{endpointDetail.method || 'GET'}
										</span>
									</div>

									<div className="endpoint-description">
										<h3>Description</h3>
										<p>{endpointDetail.description}</p>
									</div>

									{endpointDetail.docstring && (
										<div className="endpoint-docstring">
											<h3>Details</h3>
											<pre>{endpointDetail.docstring}</pre>
										</div>
									)}

									{endpointDetail.documentation && (
										<div className="endpoint-documentation">
											<h3>Documentation</h3>
											<div>{endpointDetail.documentation}</div>
										</div>
									)}

									{endpointDetail.params && Object.keys(endpointDetail.params).length > 0 && (
										<div className="endpoint-params">
											<h3>Parameters</h3>
											<div className="params-list">
												{Object.entries(endpointDetail.params).map(([key, param]) => (
													<div key={key} className="param-item">
														<div className="param-header">
															<span className="param-name">{key}</span>
															<span className={`param-badge badge-${param.in}`}>{param.in}</span>
															{param.required && <span className="param-required">required</span>}
															<span className="param-type">{param.type}</span>
														</div>
														<p className="param-description">{param.description}</p>
														<input
															type={param.type === 'number' ? 'number' : param.type === 'boolean' ? 'checkbox' : 'text'}
															{...(param.type === 'boolean'
																? { checked: (paramValues[endpointDetail.function]?.[key] === 'true') }
																: { value: paramValues[endpointDetail.function]?.[key] || '' }
															)}
															onChange={(e) => setParamValues(prev => ({
																...prev,
																[endpointDetail.function]: {
																	...(prev[endpointDetail.function] || {}),
																	[key]: param.type === 'boolean' ? String(e.target.checked) : e.target.value
																}
															}))}
															placeholder={param.type !== 'boolean' ? `Enter ${key}` : undefined}
															className="param-input"
														/>
													</div>
												))}
											</div>
										</div>
									)}

									{(!endpointDetail.type || endpointDetail.type === 'route') && (
										<div className="endpoint-test">
											<h3>Try it out</h3>
											<div className="test-section">
												<button
													onClick={() => {
														const apisMap = new Map(apis.map(api => [api.name, api]));
														const basePath = buildBasePath(selectedApiName!, apisMap);
														testEndpoint(
															endpointDetail.function,
															endpointDetail.route || `${basePath}/${endpointDetail.function}`,
															endpointDetail.method || 'GET',
															endpointDetail.params
														);
													}}
													disabled={loading[endpointDetail.function]}
													className="test-button"
												>
													{loading[endpointDetail.function] ? 'Testing...' : 'Execute'}
												</button>

												{testResponse[endpointDetail.function] && (
													<div
														className={`test-response ${loading[endpointDetail.function] ? 'loading' : ''}`}
														ref={(el) => {
															responseRefs.current[endpointDetail.function] = el;
														}}
													>
														<h4>Response</h4>
														<pre>{testResponse[endpointDetail.function]}</pre>
														{loading[endpointDetail.function] && (
															<div className="response-loading-overlay">
																<span>Loading...</span>
															</div>
														)}
													</div>
												)}
											</div>
										</div>
									)}
								</div>
							))}
						</div>
					) : (
						<div className="empty-state">
							<p>Select an API module to view documentation</p>
						</div>
					)}
				</main>
			</div>
		</div>
	);
}
