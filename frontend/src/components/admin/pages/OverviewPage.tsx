interface Stat {
	label: string;
	value: number | string;
	total?: number;
}

interface Service {
	name: string;
	ready: boolean;
}

interface OverviewPageProps {
	title?: string;
	stats?: Stat[];
	services?: Service[];
}

export default function OverviewPage({ title, stats, services }: OverviewPageProps) {
	return (
		<div className="page-content">
			<h2>{title}</h2>

			{stats && (
				<div className="stats-grid">
					{stats.map((stat: Stat, i: number) => (
						<div key={i} className="stat-card">
							<div className="stat-label">{stat.label}</div>
							<div className="stat-value">
								{stat.value}
								{stat.total && <span className="stat-total">/ {stat.total}</span>}
							</div>
						</div>
					))}
				</div>
			)}

			{services && (
				<div className="content-section">
					<h3>Services</h3>
					<div className="table-container">
						<table className="data-table">
							<thead>
								<tr>
									<th>Service</th>
									<th>Status</th>
								</tr>
							</thead>
							<tbody>
								{services.map((service: Service) => (
									<tr key={service.name}>
										<td className="monospace">{service.name}</td>
										<td>
											<span className={`status-badge ${service.ready ? 'status-ready' : 'status-error'}`}>
												{service.ready ? 'Ready' : 'Not Ready'}
											</span>
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				</div>
			)}
		</div>
	);
}
