# Specification notebook template usage
`templates/spec_template.py` is the canonical starter template for notebook-driven specs.

## Generate TOML from a specification notebook
```bash
uv run pdealchemy notebook-to-toml examples/notebooks/spec_black_scholes.py --output examples/notebooks/spec_black_scholes.toml --overwrite
```

## Equation library file examples
### `library/pde/black_scholes.md`
Black-Scholes backward PDE

\[
\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2}
+ r S \frac{\partial V}{\partial S} - rV = 0
\]

### `library/discretisation/crank_nicolson_standard.md`
Crank-Nicolson discretisation

- Scheme: Crank-Nicolson (second-order accurate)
- Time steps: 200
- Space steps: 401 (log-price grid recommended)

### `library/boundary/asymptotic_call.md`
Upper boundary (call as \(S \to \infty\))

\[
V(t, S) \sim S - K e^{-r(T-t)}
\]

### `library/payoff/vanilla_call.md`
European call payoff

\[
V(T, S) = \max(S - K, 0)
\]
