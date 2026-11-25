import HealthScoreCard from "./components/HealthScoreCard";
import IssueList from "./components/IssueList";

// Sprint 1: mock data so C can build UI without waiting on A's backend.
// Sprint 3: replace with a real fetch("/api/projects/:id/health") + issues call.
const mockHealth = {
  overallScore: 84,
  categoryScores: { security: 78, quality: 89, performance: 91, architecture: 82 }
};

const mockIssues = [
  {
    id: "1",
    file: "src/routes/auth.js",
    line: 42,
    category: "security",
    severity: "high" as const,
    message: "Password handling needs improvement"
  },
  {
    id: "2",
    file: "src/services/UserService.js",
    line: 18,
    category: "architecture",
    severity: "medium" as const,
    message: "Route handler bypasses the service layer"
  }
];

export default function App() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <h1 className="text-2xl font-semibold">AI Guardian</h1>
      <HealthScoreCard {...mockHealth} />
      <div>
        <h2 className="mb-2 text-lg font-medium">Issues</h2>
        <IssueList issues={mockIssues} />
      </div>
    </div>
  );
}
