"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type LinePoint = {
  label: string;
  value: number;
  secondary?: number;
};

type BarPoint = {
  label: string;
  value: number;
};

type PiePoint = {
  name: string;
  value: number;
};

export function TrendLineChart({
  title,
  data,
  valueLabel,
  secondaryLabel,
}: {
  title: string;
  data: LinePoint[];
  valueLabel: string;
  secondaryLabel?: string;
}) {
  return (
    <div className="panel">
      <h3>{title}</h3>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(31,31,31,0.12)" strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#c95f37" name={valueLabel} strokeWidth={3} />
            {secondaryLabel ? (
              <Line
                type="monotone"
                dataKey="secondary"
                stroke="#1f5f6b"
                name={secondaryLabel}
                strokeWidth={2}
              />
            ) : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function RankingBarChart({
  title,
  data,
}: {
  title: string;
  data: BarPoint[];
}) {
  return (
    <div className="panel">
      <h3>{title}</h3>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(31,31,31,0.12)" strokeDasharray="3 3" />
            <XAxis dataKey="label" angle={-15} textAnchor="end" interval={0} height={60} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#1f5f6b" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function SharePieChart({ title, data }: { title: string; data: PiePoint[] }) {
  return (
    <div className="panel">
      <h3>{title}</h3>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" outerRadius={92} fill="#d8a05a" label />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function InlineLinePlot({
  data,
  valueLabel,
  secondaryLabel,
}: {
  data: LinePoint[];
  valueLabel: string;
  secondaryLabel?: string;
}) {
  return (
    <div className="inline-chart">
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid stroke="rgba(31,31,31,0.1)" strokeDasharray="3 3" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} width={36} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#c95f37" name={valueLabel} strokeWidth={3} dot={false} />
          {secondaryLabel ? (
            <Line
              type="monotone"
              dataKey="secondary"
              stroke="#1f5f6b"
              name={secondaryLabel}
              strokeWidth={2}
              dot={false}
            />
          ) : null}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function InlineBarPlot({ data }: { data: BarPoint[] }) {
  return (
    <div className="inline-chart">
      <ResponsiveContainer>
        <BarChart data={data}>
          <CartesianGrid stroke="rgba(31,31,31,0.1)" strokeDasharray="3 3" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} interval={0} angle={-12} textAnchor="end" height={54} />
          <YAxis tickLine={false} axisLine={false} width={30} />
          <Tooltip />
          <Bar dataKey="value" fill="#1f5f6b" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function InlinePiePlot({ data }: { data: PiePoint[] }) {
  return (
    <div className="inline-chart">
      <ResponsiveContainer>
        <PieChart>
          <Tooltip />
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={70} fill="#d8a05a" label />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
