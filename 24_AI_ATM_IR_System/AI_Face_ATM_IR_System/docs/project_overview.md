# Project Overview & Architecture Manual

## 1. System Intent & Motivation

The **AI-Based Face Recognition ATM Security and Intelligent Information Retrieval System** addresses two interdependent enterprise paradigms:
1. **Multi-Factor Biometric Banking Security**: Replacing vulnerable magnetic-stripe and single-factor PIN interfaces with an intelligent 3-stage authentication protocol (Account ID &rarr; Live LBPH Face Verification &rarr; Salted PBKDF2 PIN Verification).
2. **Enterprise Information Retrieval & Intelligence**: Implementing modern IR techniques, ranging from finite automata Boolean filtering and statistical language models to distributed MapReduce inverted indexing, PageRank link analysis, and semantic knowledge graphs.

## 2. Authentication Workflow

```
[User Arrives at Terminal]
          │
          ▼
   [Account Lookup] ──── (Account Exists & Not Locked?)
          │                              │ No ──> [Halt & Log Warning]
          ▼ Yes
[Open Camera / Face Scan]
          │
          ▼
[Haar Cascade Face Detection] ──> [Preprocess Grayscale 200x200]
          │
          ▼
 [LBPH Prediction Distance] ──── (Distance <= 70.0 across 5 Frames?)
          │                              │ No ──> [Reject Biometric Attempt]
          ▼ Yes
   [Prompt for PIN]
          │
          ▼
[Verify PBKDF2 Salted Hash] ──── (Match Stored Hash?)
          │                              │ No ──> [Increment Failed Attempts]
          │                                        (>= 3 Tries -> 15 min Lockout)
          ▼ Yes
 [ATM Dashboard & IR Workbench]
```

## 3. High-Priority Viva Talking Points

1. **Why LBPH instead of deep learning for ATM edge kiosks?**
   - LBPH (Local Binary Patterns Histograms) runs in real-time on CPU hardware without demanding multi-gigabyte GPU accelerators.
   - It partitions the normalized face crop into an $8 \times 8$ grid of cells and computes local texture histograms, yielding high illumination robustness.
2. **How does Divergence From Randomness (DFR) differ from classic TF-IDF?**
   - Classic TF-IDF is heuristic. DFR is rooted in probabilistic information theory: the more a term's frequency in a document deviates from what would be expected by pure chance across the corpus, the more informative it is.
3. **How does PageRank converge?**
   - It models random web surfing as a Markov chain with a stationary probability vector $\mathbf{p}$. The power iteration method guarantees convergence to the principal eigenvector when the transition matrix is made irreducible and aperiodic via damping ($d = 0.85$).
