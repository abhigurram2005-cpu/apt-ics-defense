type Issue = {
  id: string;
  file: string;
  line?: number;
  category: string;
  severity: "critical" | "high" | "medium" | "low";
  message: string;
};

type Props = {
  issues: Issue[];
};

const severityColor: Record<Issue["severity"], string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-gray-100 text-gray-700"
};

// Sprint 2 (Member C): wire this to real data from GET /api/projects/:id/issues
export default function IssueList({ issues }: Props) {
  if (issues.length === 0) {
    return <p className="text-sm text-gray-500">No issues found yet.</p>;
  }

  return (
    <ul className="divide-y divide-gray-100 rounded-xl border border-gray-200">
      {issues.map((issue) => (
        <li key={issue.id} className="flex items-start justify-between gap-4 p-4">
          <div>
            <p className="text-sm font-medium">{issue.message}</p>
            <p className="text-xs text-gray-500">
              {issue.file}
              {issue.line ? `:${issue.line}` : ""} · {issue.category}
            </p>
          </div>
          <span className={`rounded-full px-2 py-1 text-xs font-medium ${severityColor[issue.severity]}`}>
            {issue.severity}
          </span>
        </li>
      ))}
    </ul>
  );
}
