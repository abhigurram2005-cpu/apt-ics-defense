import mongoose from "mongoose";

const findingSchema = new mongoose.Schema(
  {
    project: { type: mongoose.Schema.Types.ObjectId, ref: "Project", required: true },
    analysisId: { type: String, required: true },
    file: { type: String, required: true },
    line: { type: Number },
    category: {
      type: String,
      enum: ["security", "quality", "performance", "architecture", "dependency"],
      required: true
    },
    severity: {
      type: String,
      enum: ["critical", "high", "medium", "low"],
      required: true
    },
    ruleId: { type: String },
    message: { type: String, required: true },
    explanation: { type: String },
    impact: { type: String },
    recommendation: { type: String },
    alternatives: [
      {
        approach: String,
        tradeoffs: String
      }
    ],
    status: {
      type: String,
      enum: ["open", "acknowledged", "resolved"],
      default: "open"
    }
  },
  { timestamps: true }
);

export default mongoose.model("Finding", findingSchema);
