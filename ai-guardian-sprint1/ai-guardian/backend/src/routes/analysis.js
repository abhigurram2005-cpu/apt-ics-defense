import { Router } from "express";
import { analyzeCode, explainFindings } from "../controllers/analysisController.js";

const router = Router();

router.post("/analyze", analyzeCode);
router.post("/explain", explainFindings);

export default router;
