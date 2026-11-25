import mongoose from "mongoose";

const projectSchema = new mongoose.Schema(
  {
    name: { type: String, required: true },
    repoUrl: { type: String },
    overallScore: { type: Number, default: 100 },
    categoryScores: {
      security: { type: Number, default: 100 },
      quality: { type: Number, default: 100 },
      performance: { type: Number, default: 100 },
      architecture: { type: Number, default: 100 }
    },
    history: [
      {
        date: { type: Date, default: Date.now },
        score: Number
      }
    ]
  },
  { timestamps: true }
);

export default mongoose.model("Project", projectSchema);
