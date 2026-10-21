# Mathematical Formulations & Algorithmic Foundations

This document provides mathematical formulations for all algorithms implemented across the system.

---

## 1. Divergence From Randomness (DFR InL2 Model)

The DFR framework computes term weight $w(t, d)$ as:
$$w(t, d) = \text{Info}_1 \cdot \text{Info}_2$$

Where:
* **$\text{Info}_1$ (Inverse Document Frequency Model)**:
  $$\text{Info}_1 = -\log_2 \frac{1}{1 + \lambda} - tfn \cdot \log_2 \frac{\lambda}{1 + \lambda}$$
  with $\lambda = \frac{F}{N}$, where $F$ is the total collection term frequency and $N$ is the number of documents in the collection.
* **Length Normalization (L2)**:
  $$tfn = tf \cdot \log_2\left(1 + c \cdot \frac{avg\_l}{l}\right)$$
  where $c$ is a parameter ($c = 1.0$), $avg\_l$ is average document length, and $l$ is document length.
* **$\text{Info}_2$ (Laplace After-Effect)**:
  $$\text{Info}_2 = \frac{tfn}{tfn + 1}$$

Final Document Score:
$$\text{Score}(D, Q) = \sum_{t \in Q \cap D} w(t, D)$$

---

## 2. Language Model Query Likelihood with Dirichlet Prior Smoothing

Given a query $Q = (q_1, q_2, \dots, q_m)$ and document $D$:
$$P(Q|D) = \prod_{i=1}^m P(q_i | D)$$

Under Dirichlet Prior Smoothing:
$$P(q|D) = \frac{c(q, D) + \mu P(q|C)}{|D| + \mu}$$

Where:
* $c(q, D)$ is the raw frequency of term $q$ in document $D$.
* $|D|$ is the length (token count) of document $D$.
* $\mu$ is the Dirichlet prior pseudo-count parameter ($\mu = 1000$).
* $P(q|C) = \frac{\sum_{D} c(q, D)}{\sum_{D} |D|}$ is the collection background probability.

---

## 3. PageRank Power Iteration Algorithm

For a web graph of $N$ nodes with damping factor $d = 0.85$:
$$PR^{(t+1)}(p_i) = \frac{1 - d}{N} + d \sum_{p_j \in \text{In}(p_i)} \frac{PR^{(t)}(p_j)}{\text{Out}(p_j)} + d \sum_{p_k \in \text{Dangling}} \frac{PR^{(t)}(p_k)}{N}$$

Convergence criterion:
$$\sum_{i=1}^N \left| PR^{(t+1)}(p_i) - PR^{(t)}(p_i) \right| < \epsilon \quad (\epsilon = 10^{-6})$$

---

## 4. Local Binary Patterns Histograms (LBPH) Face Recognizer

For a pixel $(x_c, y_c)$ with intensity $i_c$ and $P$ circular neighbors at radius $R$:
$$LBP_{P, R}(x_c, y_c) = \sum_{p=0}^{P-1} s(i_p - i_c) 2^p$$
Where:
$$s(x) = \begin{cases} 1 & \text{if } x \ge 0 \\ 0 & \text{otherwise} \end{cases}$$

The $200 \times 200$ face crop is divided into an $8 \times 8$ grid of cells. A 256-bin histogram is computed for each cell. The resulting feature vector concatenates all 64 histograms ($64 \times 256 = 16,384$ bins).
Distance matching uses Chi-Square distance:
$$\chi^2(H_1, H_2) = \sum_{i} \frac{(H_1[i] - H_2[i])^2}{H_1[i] + H_2[i]}$$

---

## 5. PIN Cryptographic Key Derivation (PBKDF2)

$$DK = \text{PBKDF2}(\text{PRF}, \text{PIN}, \text{Salt}, c, dkLen)$$
* $\text{PRF} = \text{HMAC-SHA256}$
* Iterations: $c = 100,000$
* Output length: $dkLen = 32$ bytes (64 hex characters)
