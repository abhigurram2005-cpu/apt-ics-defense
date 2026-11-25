import mongoose from "mongoose";

export async function connectDB() {
  const uri = process.env.MONGO_URI || "mongodb://localhost:27017/ai-guardian";
  try {
    await mongoose.connect(uri);
    console.log("MongoDB connected");
  } catch (err) {
    console.error("MongoDB connection failed:", err.message);
    // Don't crash the whole server in dev if Mongo isn't up yet —
    // routes that need it will just fail until it connects/retries.
    setTimeout(() => connectDB(), 5000);
  }
}
