"""Optional PyTorch Transformer encoder matching np_transformer.py architecture and run_all.py --torch API."""
import json
import os
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import config


class TorchOpcodeTransformer(nn.Module):
    def __init__(self, vocab_size: int, n_classes: int, max_len: int = config.MAX_LEN,
                 d_model: int = config.EMB_DIM, nhead: int = config.HEADS,
                 num_layers: int = config.LAYERS, dim_feedforward: int = config.FF_DIM,
                 dropout: float = config.DROPOUT):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_emb = nn.Parameter(torch.randn(1, max_len, d_model) * 0.1)
        enc_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="relu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T)
        pad_mask = (x == 0)
        h = self.tok_emb(x) + self.pos_emb[:, :x.size(1), :]
        h = self.encoder(h, src_key_padding_mask=pad_mask)
        h = self.norm(h)
        valid = (~pad_mask).unsqueeze(-1).float()
        pooled = (h * valid).sum(dim=1) / valid.sum(dim=1).clamp(min=1.0)
        return self.head(pooled)


def train(ids_tr, y_tr, ids_va, y_va, vocab, n_classes, epochs=config.EPOCHS):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(config.SEED)
    model = TorchOpcodeTransformer(vocab_size=vocab, n_classes=n_classes, max_len=ids_tr.shape[1]).to(device)

    cnt = np.bincount(y_tr, minlength=n_classes).clip(min=1)
    # Dampened inverse-sqrt class weights prevent noisy gradients on ultra-rare classes (e.g., HOTBAR=8)
    cw = np.sqrt(len(y_tr) / (n_classes * cnt)).astype(np.float32)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(cw, device=device))

    optimizer = torch.optim.AdamW(model.parameters(), lr=config.LR, weight_decay=1e-4)
    tr_loader = DataLoader(
        TensorDataset(torch.tensor(ids_tr, dtype=torch.long), torch.tensor(y_tr, dtype=torch.long)),
        batch_size=config.BATCH,
        shuffle=True,
    )
    va_x = torch.tensor(ids_va, dtype=torch.long, device=device)

    best_acc = -1.0
    best_state = None
    hist = []
    t0 = time.time()

    for ep in range(1, epochs + 1):
        model.train()
        tot_loss = 0.0
        for bx, by in tr_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            logits = model(bx)
            loss = criterion(logits, by)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            tot_loss += float(loss.item()) * bx.size(0)

        model.eval()
        with torch.no_grad():
            va_preds = model(va_x).argmax(dim=1).cpu().numpy()
        val_acc = float((va_preds == y_va).mean())
        hist.append({"epoch": ep, "train_loss": tot_loss / len(y_tr), "val_acc": val_acc})
        print(f"epoch {ep}/{epochs}  loss {tot_loss/len(y_tr):.4f}  val_acc {val_acc:.4f}", flush=True)

        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    dt = time.time() - t0
    if best_state is not None:
        model.load_state_dict(best_state)
    model.to("cpu").eval()

    os.makedirs(config.MODELS_DIR, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "vocab": vocab, "n_classes": n_classes, "max_len": ids_tr.shape[1]},
               f"{config.MODELS_DIR}/transformer_torch.pt")
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    with open(f"{config.RESULTS_DIR}/transformer_training_log.json", "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2)
    return model, dt


def predict_proba(model: TorchOpcodeTransformer, X: np.ndarray, bs: int = 64) -> np.ndarray:
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(X), bs):
            bx = torch.tensor(X[i:i + bs], dtype=torch.long)
            probs = torch.softmax(model(bx), dim=-1).numpy()
            out.append(probs)
    return np.concatenate(out, axis=0)
