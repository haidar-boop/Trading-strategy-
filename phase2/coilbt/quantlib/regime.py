# Adapted from the uploaded quant_system research sandbox (synthetic-data
# methodology toolkit); integrated verbatim-algorithm into the phase2 harness.
"""
regime.py - Gaussian Hidden Markov Model from scratch (numpy only).

Detects latent market regimes from a small feature set. The class deliberately
exposes BOTH:
  - smooth()  : full forward-backward posterior  -> uses the WHOLE series
                (look-ahead; only valid for in-sample analysis / labelling)
  - filter()  : causal forward pass               -> uses ONLY data up to t
                (this is what you must use live)
A core demo shows how much regime accuracy silently inflates if you cheat and
use smoothed labels - a classic, subtle backtest leak.

Multivariate Gaussian emissions; Rabiner-scaled recursions for stability.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import multivariate_normal


class GaussianHMM:
    def __init__(self, n_states=3, n_iter=50, tol=1e-4, reg=1e-6, seed=0):
        self.K = n_states
        self.n_iter = n_iter
        self.tol = tol
        self.reg = reg
        self.rng = np.random.default_rng(seed)

    # ---------- emission probabilities ----------
    def _emission_logprob(self, X):
        T = X.shape[0]
        logB = np.zeros((T, self.K))
        for k in range(self.K):
            logB[:, k] = multivariate_normal.logpdf(
                X, mean=self.mu[k], cov=self.cov[k], allow_singular=True)
        return logB

    # ---------- init ----------
    def _init_params(self, X):
        T, D = X.shape
        # k-means-ish init via quantiles of the first feature
        order = np.argsort(X[:, 0])
        chunks = np.array_split(order, self.K)
        self.mu = np.array([X[c].mean(axis=0) for c in chunks])
        self.cov = np.array([np.cov(X[c].T) + self.reg * np.eye(D)
                             for c in chunks])
        self.pi = np.full(self.K, 1 / self.K)
        self.A = np.full((self.K, self.K), 0.1 / (self.K - 1))
        np.fill_diagonal(self.A, 0.9)

    # ---------- scaled forward-backward ----------
    def _forward_backward(self, B):
        T = B.shape[0]
        alpha = np.zeros((T, self.K))
        c = np.zeros(T)
        alpha[0] = self.pi * B[0]
        c[0] = alpha[0].sum() + 1e-300
        alpha[0] /= c[0]
        for t in range(1, T):
            alpha[t] = (alpha[t - 1] @ self.A) * B[t]
            c[t] = alpha[t].sum() + 1e-300
            alpha[t] /= c[t]

        beta = np.zeros((T, self.K))
        beta[-1] = 1.0
        for t in range(T - 2, -1, -1):
            beta[t] = (self.A @ (B[t + 1] * beta[t + 1])) / c[t + 1]

        gamma = alpha * beta
        gamma /= gamma.sum(axis=1, keepdims=True) + 1e-300
        loglik = np.sum(np.log(c))
        return alpha, beta, gamma, c, loglik

    # ---------- EM (Baum-Welch) ----------
    def fit(self, X):
        X = np.asarray(X, float)
        T, D = X.shape
        self._init_params(X)
        prev_ll = -np.inf
        for _ in range(self.n_iter):
            logB = self._emission_logprob(X)
            B = np.exp(logB - logB.max(axis=1, keepdims=True))  # scale for stability
            alpha, beta, gamma, c, ll = self._forward_backward(B)

            # xi (transition expectations)
            xi_sum = np.zeros((self.K, self.K))
            for t in range(T - 1):
                num = (alpha[t][:, None] * self.A
                       * (B[t + 1] * beta[t + 1])[None, :]) / c[t + 1]
                xi_sum += num
            # M-step
            self.pi = gamma[0] / gamma[0].sum()
            self.A = xi_sum / xi_sum.sum(axis=1, keepdims=True)
            for k in range(self.K):
                gk = gamma[:, k]
                w = gk.sum()
                self.mu[k] = (gk[:, None] * X).sum(axis=0) / w
                dx = X - self.mu[k]
                self.cov[k] = (gk[:, None, None] * (dx[:, :, None] * dx[:, None, :])
                               ).sum(axis=0) / w + self.reg * np.eye(D)
            if abs(ll - prev_ll) < self.tol:
                break
            prev_ll = ll
        self.loglik_ = ll
        return self

    # ---------- inference ----------
    def smooth(self, X):
        """Full posterior P(state_t | ALL data). Look-ahead; in-sample only."""
        X = np.asarray(X, float)
        logB = self._emission_logprob(X)
        B = np.exp(logB - logB.max(axis=1, keepdims=True))
        _, _, gamma, _, _ = self._forward_backward(B)
        return gamma

    def filter(self, X):
        """Causal posterior P(state_t | data up to t). Use this LIVE."""
        X = np.asarray(X, float)
        T = X.shape[0]
        logB = self._emission_logprob(X)
        B = np.exp(logB - logB.max(axis=1, keepdims=True))
        alpha = np.zeros((T, self.K))
        a = self.pi * B[0]
        alpha[0] = a / a.sum()
        for t in range(1, T):
            a = (alpha[t - 1] @ self.A) * B[t]
            alpha[t] = a / (a.sum() + 1e-300)
        return alpha

    def viterbi(self, X):
        X = np.asarray(X, float)
        T = X.shape[0]
        logB = self._emission_logprob(X)
        logA = np.log(self.A + 1e-300)
        delta = np.zeros((T, self.K))
        psi = np.zeros((T, self.K), dtype=int)
        delta[0] = np.log(self.pi + 1e-300) + logB[0]
        for t in range(1, T):
            for k in range(self.K):
                seq = delta[t - 1] + logA[:, k]
                psi[t, k] = np.argmax(seq)
                delta[t, k] = seq[psi[t, k]] + logB[t, k]
        path = np.zeros(T, dtype=int)
        path[-1] = np.argmax(delta[-1])
        for t in range(T - 2, -1, -1):
            path[t] = psi[t + 1, path[t + 1]]
        return path
