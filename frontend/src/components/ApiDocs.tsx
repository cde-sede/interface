import { useState, useEffect } from 'react';
import './ApiDocs.css';

interface ApiModule {
  name: string;
  blueprint: string;
  routes: string[];
}

interface EndpointDoc {
  function: string;
  description: string;
  docstring: string | null;
  route?: string | null;
}

interface ApiDocsData {
  apis: ApiModule[];
}

export default function ApiDocs() {
  const [apis, setApis] = useState<ApiModule[]>([]);
  const [selectedApi, setSelectedApi] = useState<string | null>(null);
  const [endpoints, setEndpoints] = useState<EndpointDoc[]>([]);
  const [selectedEndpoint, setSelectedEndpoint] = useState<string | null>(null);
  const [endpointDetail, setEndpointDetail] = useState<EndpointDoc | null>(null);
  const [testResponse, setTestResponse] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [loadingEndpoints, setLoadingEndpoints] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Fetch all APIs
  useEffect(() => {
    fetch('http://localhost:5000/api/')
      .then(res => res.json())
      .then((data: ApiDocsData) => setApis(data.apis))
      .catch(err => console.error('Failed to fetch APIs:', err));
  }, []);

  // Fetch endpoints for selected API
  useEffect(() => {
    if (!selectedApi) return;

    setLoadingEndpoints(true);
    setEndpoints([]);

    // Construct describe URL (selectedApi already has the base path)
    fetch(`http://localhost:5000${selectedApi}/describe`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        console.log('Fetched endpoints:', data);
        setEndpoints(data.functions || []);
      })
      .catch(err => console.error('Failed to fetch endpoints:', err))
      .finally(() => setLoadingEndpoints(false));
  }, [selectedApi]);

  // Fetch endpoint details
  useEffect(() => {
    if (!selectedApi || !selectedEndpoint) return;

    setLoadingDetail(true);
    setEndpointDetail(null);

    fetch(`http://localhost:5000${selectedApi}/describe?f=${selectedEndpoint}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        console.log('Fetched endpoint detail:', data);
        setEndpointDetail(data);
      })
      .catch(err => console.error('Failed to fetch endpoint details:', err))
      .finally(() => setLoadingDetail(false));
  }, [selectedApi, selectedEndpoint]);

  const testEndpoint = async (route: string) => {
    setLoading(true);
    setTestResponse('');
    try {
      const res = await fetch(`http://localhost:5000${route}`);
      const data = await res.json();
      setTestResponse(JSON.stringify(data, null, 2));
    } catch (err) {
      setTestResponse(`Error: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="api-docs">
      <header className="api-docs-header">
        <h1>API Documentation</h1>
        <p>Interactive API testing and documentation</p>
      </header>

      <div className="api-docs-content">
        <aside className="api-sidebar">
          <h2>API Modules</h2>
          <div className="api-list">
            {apis.map(api => {
              // Find the base route (not /describe, not with query params)
              const baseRoute = api.routes
                .filter(r => !r.includes('describe'))
                .sort((a, b) => a.length - b.length)[0]
                ?.replace(/\/$/, '') || '';

              console.log(`API ${api.name}:`, { routes: api.routes, baseRoute });

              return (
                <div
                  key={api.blueprint}
                  className={`api-item ${selectedApi === baseRoute ? 'active' : ''}`}
                  onClick={() => {
                    console.log(`Clicked API: ${api.name}, baseRoute: ${baseRoute}`);
                    setSelectedApi(baseRoute);
                    setSelectedEndpoint(null);
                    setEndpointDetail(null);
                    setTestResponse('');
                  }}
                >
                  <span className="api-name">{api.name}</span>
                  <span className="api-blueprint">{api.blueprint}</span>
                </div>
              );
            })}
          </div>

          {loadingEndpoints && (
            <div style={{ padding: '1rem', color: '#666' }}>Loading endpoints...</div>
          )}

          {selectedApi && endpoints.length > 0 && (
            <>
              <h3>Endpoints</h3>
              <div className="endpoint-list">
                {endpoints.map(endpoint => (
                  <div
                    key={endpoint.function}
                    className={`endpoint-item ${selectedEndpoint === endpoint.function ? 'active' : ''}`}
                    onClick={() => setSelectedEndpoint(endpoint.function)}
                  >
                    <span className="endpoint-name">{endpoint.function}</span>
                    <span className="endpoint-desc">{endpoint.description}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </aside>

        <main className="api-main">
          {loadingDetail ? (
            <div className="empty-state">
              <p>Loading endpoint details...</p>
            </div>
          ) : selectedApi && selectedEndpoint && endpointDetail ? (
            <div className="endpoint-detail">
              <div className="endpoint-header">
                <h2>{endpointDetail.function}</h2>
                <span className="http-method">GET</span>
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

              <div className="endpoint-test">
                <h3>Try it out</h3>
                <div className="test-section">
                  <button
                    onClick={() => testEndpoint(endpointDetail.route || `${selectedApi}/${selectedEndpoint}`)}
                    disabled={loading}
                    className="test-button"
                  >
                    {loading ? 'Testing...' : 'Execute'}
                  </button>

                  {testResponse && (
                    <div className="test-response">
                      <h4>Response</h4>
                      <pre>{testResponse}</pre>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <p>Select an API module and endpoint to view documentation</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
