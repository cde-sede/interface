interface Log {
	timestamp: string;
	level: string;
	logger: string;
	message: string;
}

interface LogsPageProps {
	logs?: Log[];
	title?: string;
	description?: string;
}

export default function LogsPage({ logs, title, description }: LogsPageProps) {
	const getLevelClass = (level: string) => {
		switch (level.toUpperCase()) {
			case 'ERROR': return 'log-level-error';
			case 'WARNING': return 'log-level-warning';
			case 'INFO': return 'log-level-info';
			case 'DEBUG': return 'log-level-debug';
			default: return 'log-level-default';
		}
	};

	const formatTimestamp = (timestamp: string) => {
		const date = new Date(timestamp);
		return date.toLocaleTimeString('en-US', { hour12: false }) + '.' + date.getMilliseconds().toString().padStart(3, '0');
	};

	return (
		<div className="page-content">
			<h2>{title}</h2>
			{description && <p className="page-description">{description}</p>}

			<div className="logs-container">
				{logs && logs.length > 0 ? (
					logs.map((log: Log, index: number) => (
						<div key={index} className="log-entry">
							<span className="log-timestamp">{formatTimestamp(log.timestamp)}</span>
							<span className={`log-level ${getLevelClass(log.level)}`}>{log.level.padEnd(7)}</span>
							<span className="log-logger">[{log.logger}]</span>
							<span className="log-message">{log.message}</span>
						</div>
					))
				) : (
					<div className="empty-state">No logs available</div>
				)}
			</div>
		</div>
	);
}
