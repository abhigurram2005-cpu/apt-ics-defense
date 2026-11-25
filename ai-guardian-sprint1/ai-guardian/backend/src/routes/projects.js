import { Router } from "express";
import Project from "../models/Project.js";
import Finding from "../models/Finding.js";

const router = Router();

// GET /api/projects/:id/health
router.get("/:id/health", async (req, res) => {
  const project = await Project.findById(req.params.id);
  if (!project) return res.status(404).json({ error: "Project not found" });

  res.json({
    projectId: project._id,
    overallScore: project.overallScore,
    categoryScores: project.categoryScores,
    history: project.history
  });
});

// GET /api/projects/:id/issues
router.get("/:id/issues", async (req, res) => {
  const findings = await Finding.find({ project: req.params.id }).sort({ createdAt: -1 });
  res.json({ issues: findings });
});

export default router;
