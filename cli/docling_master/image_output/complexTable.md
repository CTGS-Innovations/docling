| Algorithm 1 Training             | Algorithm 2 Sampling                      |
|----------------------------------|-------------------------------------------|
| 1: repeat                        | 1: xT ~ N(0,I)                            |
| 2: x0 ~ q(x0)                    | 2: for t = T,..., 1 do                    |
| 3: t ~ Uniform{1,...,T}          | 3: z ~ N(0,I) if t > 1, else x = 0        |
| 4: e ~ N(0,I)                    | 4: x1-1 = 1 2( x1 - 1 - a1,e(x1,t)) + o,x |
| 5: Take gradient descent step on | 5: end for                                |
| 6: until converged               | 6: return x0                              |