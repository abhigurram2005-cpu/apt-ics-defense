import "dotenv/config";
import express from "express";
import cors from "cors";
import { connectDB } from "./config/db.js";
import analysisRoutes from "./routes/analysis.js";
import projectRoutes from "./routes/projects.js";

const app = express();
app.use(cors());
app.use(express.json({ limit: "5mb" })); // whole-file payloads can be large

connectDB();

app.get("/health", (req, res) => res.json({ status: "ok" }));
app.use("/api", analysisRoutes);
app.use("/api/projects", projectRoutes);

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`AI Guardian backend running on port ${PORT}`));
