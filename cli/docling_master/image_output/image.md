Algorithm 1 Training

1: repeat

2: xo ~ q(xo)

3: t ~ Uniform{1,...,T})

4: e ~ N(0,I)

5: Take gradient descent step on

Va[e - e(Va,Xo +V1 - e(e,t))] 2

6: until converged

Equation 10 reveals that p, must predict 1 (xe - S,e) given xe. Since xe is available as input to the model, we may choose the parameterization

1 1 (xe - V1 - e(e,x)) = 1 (xe - V1 - e(e,x(x)) ) = 1 (xe - V1 - e(e,x(x)) ) where e,e is a function approximator intended to predict e from xe. To sample xe-1 ~ P(xe-1|x) is

to compute xe-1 = 1 (xe - B,e) (xe,x(x)) + o,z, where z ~ VN(0,I). The complete sampling procedure, Algorithm 2 resembles Langevin dynamics with e as a learned gradient of the data density. Furthermore, with the parameterization (11), Eq. (10) simplifies to:

Ex,e [20%e(1-1) 1 1 (xe-1) 2] (12) which resembles denoising score matching over multiple noise scales indexed by t [35]. As Eq. (12)

is equal to (one term of) the variational bound for the Langevin-like reverse process (11), we see that optimizing an objective resembling denoising score matching is equivalent to using variational inference to fit the finite-time marginal of a sampling chain resembling Langevin dynamics.

To summarize, we can train the reverse process mean function approximator p to predict p, or by modifying its parameterization, we can train it to predict e. (There is also the possibility of predicting xo, but we found this to lead to worse sample quality early in our experiments.) We have shown that the e-prediction parameterization both resembles Langevin dynamics and simplifies the diffusion model's variational bound to an objective that resembles denoising score matching. Nonetheless, it is just another parameterization of p(xe-1|x), so we verify its effectiveness in Section 4 in an ablation where we compare predicting e against predicting p.

## 3.3 Data scaling, reverse process decoder, and Lo

We assume that image data consists of integers in {0,1,...,255} scaled linearly to [-1,1]. This ensures that the neural network reverse process operates on consis tently scaled inputs starting from the standard normal prior p(xe). To obtain discrete log likelihoods, we set the last term of the reverse process to an independent discrete decoder derived from the Gaussian N(xo,p(xe,1),p2I):

$$\rho _ { e } ( x _ { 0 } | x _ { 1 } ) = \prod _ { i = 1 } ^ { 1 / 4 - \frac { 1 } { 2 } } N ( \mathbb { R } _ { i } ; \rho _ { e } ( x _ { 1 }, 1 ), \sigma _ { i } ^ { 2 } ) \mathrm d r$$

$$\delta _ { 4 } ( \mathbb { R } ) = \begin{cases} \frac { 1 } { 2 5 6 } & \mathrm i f \, \, \mathrm i = 1 \\ \frac { 1 } { 2 5 6 } & \mathrm i f \, \, \mathrm i > - 1 \end{cases}$$

where D is the data dimensionality and the i superscript indicates extraction of one coordinate. (It would be straightforward to instead incorporate a more powerful decoder like a conditional autoregressive model, but we leave that to future work.) Similar to the discretized continuous distributions used in VAE decoders and autoregressive models [34,5], our choice here ensures that the variational bound is a lossless codelength of discrete data, without need of adding noise to the data or incorporating the Jacobian of the scaling operation into the log likelihood. At the end of sampling, we display p,e(x,1) noiselessly.

## 3.4 Simplified training objective

With the reverse process and decoder defined above, the variational bound, consisting of terms derived from Eqs. (12) and (13), is clearly differentiable with respect to @ and is ready to be employed for