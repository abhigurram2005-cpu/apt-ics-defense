type CategoryScores = {
  security: number;
  quality: number;
  performance: number;
  architecture: number;
};

type Props = {
  overallScore: number;
  categoryScores: CategoryScores;
};

// Sprint 2 (Member C): wire this to real data from GET /api/projects/:id/health
export default function HealthScoreCard({ overallScore, categoryScores }: Props) {
  return (
    <div className="rounded-xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-medium">Project health</h2>
        <span className="text-3xl font-semibold">{overallScore}/100</span>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Object.entries(categoryScores).map(([category, score]) => (
          <div key={category} className="rounded-lg bg-gray-50 p-3">
            <div className="text-xs uppercase text-gray-500">{category}</div>
            <div className="text-xl font-medium">{score}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
