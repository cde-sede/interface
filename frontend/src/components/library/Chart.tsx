/**
 * Chart Component
 *
 * Data visualization using Recharts library.
 */

import {
	BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area,
	ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
	Legend, ResponsiveContainer, Cell
} from 'recharts';
import type { BaseComponentProps } from './types';
import './Chart.css';

export type ChartType = 'bar' | 'line' | 'pie' | 'area' | 'scatter';

export interface ChartSeries {
	dataKey: string;                /** Data field key */
	name: string;                   /** Series name */
	color?: string;                 /** Series color */
}

export interface ChartAxis {
	dataKey?: string;               /** Axis data field */
	label?: string;                 /** Axis label */
}

export interface ChartConfig {
	xAxis?: ChartAxis;              /** X-axis configuration */
	yAxis?: ChartAxis;              /** Y-axis configuration */
	series: ChartSeries[];          /** Chart series */
	legend?: boolean;               /** Show legend */
	height?: number;                /** Chart height */
}

export interface ChartProps extends BaseComponentProps {
	chartType: ChartType;           /** Chart type */
	data: any[];                    /** Chart data */
	config: ChartConfig;            /** Chart configuration */
}

// Default colors for chart series
const DEFAULT_COLORS = [
	'#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1',
	'#a4de6c', '#d0ed57', '#ffc0cb', '#ffd700', '#ff6347'
];

export function Chart({
	chartType,
	data,
	config,
	className,
	style,
	'data-testid': dataTestId
}: ChartProps) {
	const {
		xAxis,
		yAxis,
		series = [],
		legend = true,
		height = 400
	} = config;

	if (!data || !Array.isArray(data)) {
		return (
			<div className="lib-chart-error" data-testid={dataTestId}>
				<p>No data available for chart</p>
			</div>
		);
	}

	// Common chart props
	const commonProps = {
		data,
		margin: { top: 5, right: 30, left: 20, bottom: 5 }
	};

	const renderChart = () => {
		switch (chartType) {
			case 'bar':
				return (
					<BarChart {...commonProps}>
						<CartesianGrid strokeDasharray="3 3" />
						{xAxis && <XAxis dataKey={xAxis.dataKey} label={xAxis.label ? { value: xAxis.label, position: 'insideBottom', offset: -5 } : undefined} />}
						{yAxis && <YAxis label={yAxis.label ? { value: yAxis.label, angle: -90, position: 'insideLeft' } : undefined} />}
						<Tooltip />
						{legend && <Legend />}
						{series.map((s, index) => (
							<Bar
								key={s.dataKey}
								dataKey={s.dataKey}
								name={s.name}
								fill={s.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
							/>
						))}
					</BarChart>
				);

			case 'line':
				return (
					<LineChart {...commonProps}>
						<CartesianGrid strokeDasharray="3 3" />
						{xAxis && <XAxis dataKey={xAxis.dataKey} label={xAxis.label ? { value: xAxis.label, position: 'insideBottom', offset: -5 } : undefined} />}
						{yAxis && <YAxis label={yAxis.label ? { value: yAxis.label, angle: -90, position: 'insideLeft' } : undefined} />}
						<Tooltip />
						{legend && <Legend />}
						{series.map((s, index) => (
							<Line
								key={s.dataKey}
								type="monotone"
								dataKey={s.dataKey}
								name={s.name}
								stroke={s.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
								strokeWidth={2}
							/>
						))}
					</LineChart>
				);

			case 'area':
				return (
					<AreaChart {...commonProps}>
						<CartesianGrid strokeDasharray="3 3" />
						{xAxis && <XAxis dataKey={xAxis.dataKey} label={xAxis.label ? { value: xAxis.label, position: 'insideBottom', offset: -5 } : undefined} />}
						{yAxis && <YAxis label={yAxis.label ? { value: yAxis.label, angle: -90, position: 'insideLeft' } : undefined} />}
						<Tooltip />
						{legend && <Legend />}
						{series.map((s, index) => (
							<Area
								key={s.dataKey}
								type="monotone"
								dataKey={s.dataKey}
								name={s.name}
								stroke={s.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
								fill={s.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
								fillOpacity={0.6}
							/>
						))}
					</AreaChart>
				);

			case 'pie':
				// For pie charts, use the first series' dataKey
				const pieDataKey = series[0]?.dataKey || 'value';
				return (
					<PieChart>
						<Pie
							data={data}
							dataKey={pieDataKey}
							nameKey={xAxis?.dataKey || 'name'}
							cx="50%"
							cy="50%"
							outerRadius={height / 3}
							label
						>
							{data.map((_entry, index) => (
								<Cell key={`cell-${index}`} fill={series[0]?.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]} />
							))}
						</Pie>
						<Tooltip />
						{legend && <Legend />}
					</PieChart>
				);

			case 'scatter':
				return (
					<ScatterChart {...commonProps}>
						<CartesianGrid strokeDasharray="3 3" />
						{xAxis && <XAxis dataKey={xAxis.dataKey} label={xAxis.label ? { value: xAxis.label, position: 'insideBottom', offset: -5 } : undefined} />}
						{yAxis && <YAxis dataKey={yAxis.dataKey} label={yAxis.label ? { value: yAxis.label, angle: -90, position: 'insideLeft' } : undefined} />}
						<Tooltip cursor={{ strokeDasharray: '3 3' }} />
						{legend && <Legend />}
						{series.map((s, index) => (
							<Scatter
								key={s.dataKey}
								name={s.name}
								data={data}
								fill={s.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
							/>
						))}
					</ScatterChart>
				);

			default:
				return (
					<div className="lib-chart-error">
						<p>Unsupported chart type: {chartType}</p>
					</div>
				);
		}
	};

	const containerClassName = className ? `lib-chart ${className}` : 'lib-chart';

	return (
		<div className={containerClassName} style={style} data-testid={dataTestId}>
			<ResponsiveContainer width="100%" height={height}>
				{renderChart()}
			</ResponsiveContainer>
		</div>
	);
}
