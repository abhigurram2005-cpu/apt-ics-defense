"""Transformer encoder in pure NumPy (forward + manual backprop + Adam). No PyTorch needed.

Architecture (pre-LayerNorm): token + learned positional embedding -> N x [multi-head
self-attention, feed-forward (ReLU)] with residuals -> final LayerNorm -> masked mean pooling
-> linear classifier. Padding (id 0) is masked in attention and pooling.
"""
import time, os, json
import numpy as np
import config

EPS = 1e-5


def init_params(vocab, n_classes, max_len, d, layers, ff, seed=config.SEED, dtype=np.float32):
    rng = np.random.default_rng(seed)
    def lin(i, o): return rng.uniform(-1, 1, (i, o)) * np.sqrt(6.0 / (i + o))
    p = {"E": rng.normal(0, 0.1, (vocab, d)), "P": rng.normal(0, 0.1, (max_len, d))}
    for l in range(layers):
        for n in ("q", "k", "v", "o"):
            p[f"W{n}{l}"] = lin(d, d); p[f"b{n}{l}"] = np.zeros(d)
        p[f"W1_{l}"] = lin(d, ff); p[f"c1_{l}"] = np.zeros(ff)
        p[f"W2_{l}"] = lin(ff, d); p[f"c2_{l}"] = np.zeros(d)
        for n in ("1", "2"):
            p[f"g{n}_{l}"] = np.ones(d); p[f"be{n}_{l}"] = np.zeros(d)
    p["gf"], p["bf"] = np.ones(d), np.zeros(d)
    p["Wc"], p["bc"] = lin(d, n_classes), np.zeros(n_classes)
    return {k: v.astype(dtype) for k, v in p.items()}


def _ln_f(x, g, b):
    mu = x.mean(-1, keepdims=True); xc = x - mu
    rstd = 1.0 / np.sqrt((xc * xc).mean(-1, keepdims=True) + EPS)
    xh = xc * rstd
    return xh * g + b, (xh, rstd, g)


def _ln_b(dy, c):
    xh, rstd, g = c
    dxh = dy * g
    dx = rstd * (dxh - dxh.mean(-1, keepdims=True) - xh * (dxh * xh).mean(-1, keepdims=True))
    return dx, (dy * xh).sum(tuple(range(dy.ndim - 1))), dy.sum(tuple(range(dy.ndim - 1)))


def _split(x, H):  # (B,T,d) -> (B,H,T,dh)
    B, T, d = x.shape
    return x.reshape(B, T, H, d // H).transpose(0, 2, 1, 3)


def _merge(x):  # (B,H,T,dh) -> (B,T,d)
    B, H, T, dh = x.shape
    return x.transpose(0, 2, 1, 3).reshape(B, T, H * dh)


def forward(p, X, heads, layers, keep_cache=False):
    B, T = X.shape
    mask = (X > 0)                                   # True = real token
    neg = np.where(mask, 0.0, -1e9).astype(p["E"].dtype)[:, None, None, :]
    h = p["E"][X] + p["P"][:T][None]
    cache = {"X": X, "mask": mask, "L": []}
    for l in range(layers):
        c = {}
        a, c["ln1"] = _ln_f(h, p[f"g1_{l}"], p[f"be1_{l}"]); c["a"] = a
        q = _split(a @ p[f"Wq{l}"] + p[f"bq{l}"], heads)
        k = _split(a @ p[f"Wk{l}"] + p[f"bk{l}"], heads)
        v = _split(a @ p[f"Wv{l}"] + p[f"bv{l}"], heads)
        dh = q.shape[-1]
        s = (q @ k.transpose(0, 1, 3, 2)) / np.sqrt(dh) + neg
        s -= s.max(-1, keepdims=True)
        pr = np.exp(s); pr /= pr.sum(-1, keepdims=True)
        ctx = _merge(pr @ v)
        h = h + ctx @ p[f"Wo{l}"] + p[f"bo{l}"]
        c.update(q=q, k=k, v=v, pr=pr, ctx=ctx, dh=dh)
        a2, c["ln2"] = _ln_f(h, p[f"g2_{l}"], p[f"be2_{l}"]); c["a2"] = a2
        f1 = a2 @ p[f"W1_{l}"] + p[f"c1_{l}"]
        r = np.maximum(f1, 0); c["f1"] = f1; c["r"] = r
        h = h + r @ p[f"W2_{l}"] + p[f"c2_{l}"]
        cache["L"].append(c)
    z, cache["lnf"] = _ln_f(h, p["gf"], p["bf"])
    m = mask[..., None].astype(z.dtype)
    cnt = np.maximum(m.sum(1), 1.0)
    pooled = (z * m).sum(1) / cnt
    logits = pooled @ p["Wc"] + p["bc"]
    cache.update(pooled=pooled, m=m, cnt=cnt)
    return (logits, cache) if keep_cache else logits


def loss_and_grads(p, X, y, heads, layers, class_w=None):
    logits, C = forward(p, X, heads, layers, keep_cache=True)
    B, T = X.shape
    ex = np.exp(logits - logits.max(1, keepdims=True)); pr = ex / ex.sum(1, keepdims=True)
    w = np.ones(B, dtype=logits.dtype) if class_w is None else class_w[y].astype(logits.dtype)
    loss = float((-np.log(pr[np.arange(B), y] + 1e-12) * w).sum() / w.sum())
    dlog = pr.copy(); dlog[np.arange(B), y] -= 1; dlog *= (w / w.sum())[:, None]
    g = {}
    g["Wc"] = C["pooled"].T @ dlog; g["bc"] = dlog.sum(0)
    dpool = dlog @ p["Wc"].T
    dz = C["m"] * (dpool / C["cnt"])[:, None, :]
    dh, g["gf"], g["bf"] = _ln_b(dz, C["lnf"])
    d = dh.shape[-1]
    for l in reversed(range(layers)):
        c = C["L"][l]
        # FFN
        df2 = dh
        g[f"W2_{l}"] = c["r"].reshape(-1, c["r"].shape[-1]).T @ df2.reshape(-1, d)
        g[f"c2_{l}"] = df2.sum((0, 1))
        dr = df2 @ p[f"W2_{l}"].T; dr = dr * (c["f1"] > 0)
        a2 = c["a2"]
        g[f"W1_{l}"] = a2.reshape(-1, d).T @ dr.reshape(-1, dr.shape[-1])
        g[f"c1_{l}"] = dr.sum((0, 1))
        da2 = dr @ p[f"W1_{l}"].T
        dx, g[f"g2_{l}"], g[f"be2_{l}"] = _ln_b(da2, c["ln2"])
        dh = dh + dx
        # Attention
        do = dh
        g[f"Wo{l}"] = c["ctx"].reshape(-1, d).T @ do.reshape(-1, d); g[f"bo{l}"] = do.sum((0, 1))
        H = c["q"].shape[1]
        dctx = _split(do @ p[f"Wo{l}"].T, H)
        pr_, q, k, v, dh_ = c["pr"], c["q"], c["k"], c["v"], c["dh"]
        dv = pr_.transpose(0, 1, 3, 2) @ dctx
        dp = dctx @ v.transpose(0, 1, 3, 2)
        ds = pr_ * (dp - (dp * pr_).sum(-1, keepdims=True)) / np.sqrt(dh_)
        dq = ds @ k
        dk = ds.transpose(0, 1, 3, 2) @ q
        a = c["a"]; a2d = a.reshape(-1, d).T
        da = 0
        for n, dd in (("q", dq), ("k", dk), ("v", dv)):
            dm = _merge(dd)
            g[f"W{n}{l}"] = a2d @ dm.reshape(-1, d); g[f"b{n}{l}"] = dm.sum((0, 1))
            da = da + dm @ p[f"W{n}{l}"].T
        dx, g[f"g1_{l}"], g[f"be1_{l}"] = _ln_b(da, c["ln1"])
        dh = dh + dx
    g["P"] = np.zeros_like(p["P"]); g["P"][:T] = dh.sum(0)
    V = p["E"].shape[0]
    oh = np.zeros((B * T, V), dtype=dh.dtype); oh[np.arange(B * T), C["X"].reshape(-1)] = 1
    g["E"] = oh.T @ dh.reshape(-1, d)
    g["E"][0] = 0   # padding id has no embedding gradient
    return loss, g


class Adam:
    def __init__(self, p, lr, b1=0.9, b2=0.999, eps=1e-8, clip=1.0):
        self.lr, self.b1, self.b2, self.eps, self.clip, self.t = lr, b1, b2, eps, clip, 0
        self.m = {k: np.zeros_like(v) for k, v in p.items()}
        self.v = {k: np.zeros_like(v) for k, v in p.items()}

    def step(self, p, g, lr=None):
        self.t += 1
        norm = np.sqrt(sum(float((x * x).sum()) for x in g.values()))
        sc = min(1.0, self.clip / (norm + 1e-12))
        lr = self.lr if lr is None else lr
        for k in p:
            gk = g[k] * sc
            self.m[k] = self.b1 * self.m[k] + (1 - self.b1) * gk
            self.v[k] = self.b2 * self.v[k] + (1 - self.b2) * gk * gk
            mh = self.m[k] / (1 - self.b1 ** self.t); vh = self.v[k] / (1 - self.b2 ** self.t)
            p[k] -= lr * mh / (np.sqrt(vh) + self.eps)
        return norm


def predict_proba(p, X, heads, layers, bs=64):
    out = []
    for i in range(0, len(X), bs):
        lg = forward(p, X[i:i + bs], heads, layers)
        e = np.exp(lg - lg.max(1, keepdims=True)); out.append(e / e.sum(1, keepdims=True))
    return np.concatenate(out)


CKPT = f"{config.MODELS_DIR}/train_checkpoint.npz"


def _save_ckpt(p, opt, best_p, state):
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    arrs = {f"p/{k}": v for k, v in p.items()}
    arrs.update({f"m/{k}": v for k, v in opt.m.items()}); arrs.update({f"v/{k}": v for k, v in opt.v.items()})
    if best_p is not None: arrs.update({f"b/{k}": v for k, v in best_p.items()})
    state = dict(state, opt_t=opt.t)
    np.savez(CKPT, __state__=json.dumps(state), **arrs)


def _load_ckpt():
    z = np.load(CKPT, allow_pickle=False)
    grab = lambda pre: {k[len(pre):]: z[k].copy() for k in z.files if k.startswith(pre)}
    return json.loads(str(z["__state__"])), grab("p/"), grab("m/"), grab("v/"), (grab("b/") or None)


def train(ids_tr, y_tr, ids_va, y_va, vocab, n_classes, epochs=config.EPOCHS, log=None, time_budget=None):
    """Resumable. If time_budget (seconds) is hit, saves a checkpoint and returns (None, None, None);
    call again with the same arguments to continue. Returns (params, cfg, total_train_seconds) when done."""
    log = log or (lambda s: print(s, flush=True))
    cfg = dict(vocab=vocab, n_classes=n_classes, max_len=ids_tr.shape[1], d=config.EMB_DIM,
               heads=config.HEADS, layers=config.LAYERS, ff=config.FF_DIM)
    cnt = np.bincount(y_tr, minlength=n_classes).clip(min=1)
    cw = (len(y_tr) / (n_classes * cnt)).astype(np.float32)
    steps_per_ep = int(np.ceil(len(y_tr) / config.BATCH)); total = steps_per_ep * epochs
    if os.path.exists(CKPT):
        st, p, m, v, best_p = _load_ckpt()
        if st["epochs"] != epochs or st["cfg"] != cfg:
            raise SystemExit(f"Checkpoint {CKPT} was made with different settings. Delete it to start fresh.")
        opt = Adam(p, config.LR); opt.m, opt.v, opt.t = m, v, st["opt_t"]
        log(f"Resuming from epoch {st['epoch']+1}, batch {st['pos']//config.BATCH}")
    else:
        p = init_params(vocab, n_classes, cfg["max_len"], cfg["d"], cfg["layers"], cfg["ff"])
        opt = Adam(p, config.LR); best_p = None
        st = dict(epoch=0, pos=0, tot=0.0, best=-1.0, hist=[], secs=0.0, epochs=epochs, cfg=cfg)
    t_call = time.time()
    while st["epoch"] < epochs:
        perm = np.random.default_rng(config.SEED + st["epoch"]).permutation(len(y_tr))
        while st["pos"] < len(perm):
            b = perm[st["pos"]: st["pos"] + config.BATCH]
            step = st["epoch"] * steps_per_ep + st["pos"] // config.BATCH
            loss, g = loss_and_grads(p, ids_tr[b], y_tr[b], cfg["heads"], cfg["layers"], cw)
            warm = min(1.0, (step + 1) / 100)
            decay = 0.5 * (1 + np.cos(np.pi * step / total))
            opt.step(p, g, lr=config.LR * warm * (0.05 + 0.95 * decay))
            st["tot"] += loss * len(b); st["pos"] += len(b)
            if time_budget and time.time() - t_call > time_budget and st["pos"] < len(perm):
                st["secs"] += time.time() - t_call
                _save_ckpt(p, opt, best_p, st)
                log(f"[paused] epoch {st['epoch']+1}/{epochs}, {st['pos']}/{len(perm)} samples. Run the same command again to continue.")
                return None, None, None
        acc = float((predict_proba(p, ids_va, cfg["heads"], cfg["layers"]).argmax(1) == y_va).mean())
        st["hist"].append({"epoch": st["epoch"] + 1, "train_loss": st["tot"] / len(y_tr), "val_acc": acc})
        log(f"epoch {st['epoch']+1}/{epochs}  loss {st['tot']/len(y_tr):.4f}  val_acc {acc:.4f}")
        if acc > st["best"]:
            st["best"], best_p = acc, {k: x.copy() for k, x in p.items()}
        st["epoch"] += 1; st["pos"] = 0; st["tot"] = 0.0
        _save_ckpt(p, opt, best_p, st)
    st["secs"] += time.time() - t_call
    save(best_p, cfg)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    json.dump(st["hist"], open(f"{config.RESULTS_DIR}/transformer_training_log.json", "w"), indent=2)
    os.remove(CKPT)
    return best_p, cfg, st["secs"]


def save(p, cfg, path=f"{config.MODELS_DIR}/transformer_np.npz"):
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    np.savez_compressed(path, __cfg__=json.dumps(cfg), **p)


def load(path=f"{config.MODELS_DIR}/transformer_np.npz"):
    z = np.load(path, allow_pickle=False)
    cfg = json.loads(str(z["__cfg__"]))
    return {k: z[k] for k in z.files if k != "__cfg__"}, cfg
