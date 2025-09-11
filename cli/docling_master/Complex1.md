## Denoising Diffusion Probabilistic Models

Jonathan Ho UC Berkeley jonathano@berkeley.edu

Ajay Jain UC Berkeley ajayj@berkeley.edu

## Abstract

We present high quality image synthesis results using diffusion probabilistic models, a class of latent variable models inspired by considerations from nonequilibrium thermodynamics. Our best results are obtained by training on a weighted variational bound designed according to a novel connection between diffusion probabilistic models and denoising score matching with Langevin dynamics, and our models naturally admit a progressive lossy decomposition scheme that can be interpreted as a generalization of autoregressive decoding. On the unconditional CIFAR10 dataset, we obtain an Inception score of 9.46 and a state-of-the-art FID score of 3.17. On 256x256 LSUN, we obtain sample quality similar to ProgressiveGAN. Our implementation is available at https://github.com/hojonathanho/diffusion .

## 1 Introduction

Deep generative models of all kinds have recently exhibited high quality samples in a wide variety of data modalities. Generative adversarial networks (GANs), autoregressive models, flows, and variational autoencoders (VAEs) have synthesized striking image and audio samples [14, 27, 3, 58, 38, 25, 10, 32, 44, 57, 26, 33, 45], and there have been remarkable advances in energy-based modeling and score matching that have produced images comparable to those of GANs [11, 55].

Figure 1: Generated samples on Celeba-HQ 256 × 256 (left) and unconditional CIFAR10 (right)

<!-- image -->

Pieter Abbeel UC Berkeley pabbeel@cs.berkeley.edu

Figure 2: The directed graphical model considered in this work.

<!-- image -->

This paper presents progress in diffusion probabilistic models [53]. A diffusion probabilistic model (which we will call a "diffusion model" for brevity) is a parameterized Markov chain trained using variational inference to produce samples matching the data after finite time. Transitions of this chain are learned to reverse a diffusion process, which is a Markov chain that gradually adds noise to the data in the opposite direction of sampling until signal is destroyed. When the diffusion consists of small amounts of Gaussian noise, it is sufficient to set the sampling chain transitions to conditional Gaussians too, allowing for a particularly simple neural network parameterization.

Diffusion models are straightforward to define and efficient to train, but to the best of our knowledge, there has been no demonstration that they are capable of generating high quality samples. We show that diffusion models actually are capable of generating high quality samples, sometimes better than the published results on other types of generative models (Section 4). In addition, we show that a certain parameterization of diffusion models reveals an equivalence with denoising score matching over multiple noise levels during training and with annealed Langevin dynamics during sampling (Section 3.2) [55, 61]. We obtained our best sample quality results using this parameterization (Section 4.2), so we consider this equivalence to be one of our primary contributions.

Despite their sample quality, our models do not have competitive log likelihoods compared to other likelihood-based models (our models do, however, have log likelihoods better than the large estimates annealed importance sampling has been reported to produce for energy based models and score matching [11, 55]). We find that the majority of our models' lossless codelengths are consumed to describe imperceptible image details (Section 4.3). We present a more refined analysis of this phenomenon in the language of lossy compression, and we show that the sampling procedure of diffusion models is a type of progressive decoding that resembles autoregressive decoding along a bit ordering that vastly generalizes what is normally possible with autoregressive models.

## 2 Background

Diffusion models [53] are latent variable models of the form ρ$\_{θ}$ ( x$\_{0}$ ) := ∫ ρ$\_{θ}$ ( x$\_{0}$ · t ) dx$\_{1}$ · τ , where x$\_{1}$, . . . , x$\_{T}$ are latents of the same dimensionality as the data x$\_{0}$ ∼ q ( x$\_{0}$ ) . The joint distribution ρ$\_{θ}$ ( x$\_{0}$ · T ) is called the reverse process , and it is defined as a Markov chain with learned Gaussian transitions starting at ρ ( x$\_{T}$ ) = N ( x$\_{T}$ ; 0 ; I ) :

$$\rho _ { \theta } ( x _ { 0 } \colon T ) \coloneqq \rho ( x _ { T } ) \prod _ { t = 1 } ^ { T } \rho _ { \theta } ( x _ { t - 1 } | x _ { t } ), \quad \rho _ { \theta } ( x _ { t - 1 } | x _ { t } ) \coloneqq \mathcal { N } ( x _ { t - 1 } ; \mu _ { \theta } ( x _ { t }, t ), \Sigma _ { \theta } ( x _ { t }, t ) ) \quad ( 1 )$$

What distinguishes diffusion models from other types of latent variable models is that the approximate posterior q ( x$\_{1}$ · T | x$\_{0}$ ) called the forward process or diffusion process , is fixed to a Markov chain that gradually adds Gaussian noise to the data according to a variance schedule β$\_{1}$, . . . , β$\_{T}$ :

$$\sigma ( x _ { 1 } \colon \mathcal { T } | x _ { 0 } ) = \prod _ { t = 1 } ^ { T } \left [ q ( x _ { t } | x _ { t - 1 } ), \quad q ( x _ { t } | x _ { t - 1 } ) = \mathcal { N } ( x _ { t } ; \sqrt { 1 - \beta _ { t } } x _ { t - 1 }, \beta _ { T } ) \right ] \quad ( 2 )$$

Training is performed by optimizing the usual variational bound on negative log likelihood:

$$\mathbb { E } \left [ - \log \rho ( x _ { 0 } ) \right ] \leq \mathbb { E } _ { q } \left [ - \log \frac { \rho _ { \theta } ( x _ { 0 } \cdot T ) } { q ( x _ { 1 } \cdot T | x _ { 0 } ) } \right ] = \mathbb { E } _ { q } \left [ - \log \rho ( x _ { T } ) - \sum _ { t \geq 1 } \log \frac { \rho _ { \theta } ( x _ { 1 } \cdot T | x _ { 1 } ) } { q ( x _ { t } | x _ { t - 1 } ) } \right ] = \colon L \ ( 3 )$$

The forward process variances β$\_{t}$ can be learned by reparameterization [33] or held constant as hyperparameters, and expressiveness of the reverse process is ensured in part by the choice of Gaussian conditionals in ρ$\_{θ}$ ( x$\_{t}$$\_{-}$$\_{1}$ | x$\_{t}$ ) , because both processes have the same functional form when β$\_{t}$ are small [53]. A notable property of the forward process is that it admits sampling x$\_{t}$ at an arbitrary timestep t in closed form: using the notation α$\_{t}$ := 1 - β$\_{t}$ and α$\_{t}$ := ∏ t $\_{=1}$Π$\_{s}$ α$\_{s}$ , we have

$$q ( x _ { t } | x _ { 0 } ) = \mathcal { N } ( x _ { t } ; \sqrt { \frac { \hat { \sigma } _ { t } } { \hat { \sigma } _ { t } x _ { 0 } } }, ( 1 - \hat { \sigma } _ { t } ) \mathbb { I } )$$

Efficient training is therefore possible by optimizing random terms of L with stochastic gradient descent. Further improvements come from variance reduction by rewriting L (3) as:

## Algorithm 1 Training

1: repeat

x$\_{0}$

∼

x$\_{0}$

(

)

(

,

,

,

(

,

(

)

(

,

(

,

,

(

,

(

,

(

,

(

,

(

,

(

,

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

(

Table 1: CIFAR10 results. NLL measured in bits/dim.

| Model                      | IS          | FID   | NLL Test (Train)   | Table 2: Unconditional CIFAR10 reverse                                                                                                                 |             |
|----------------------------|-------------|-------|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|
| Conditional                |             |       |                    | process parameterization and training objec- tive ablation. Blank entries were unstable to train and generated poor samples with out-of- range scores. |             |
| EBM [11]                   | 8.30        | 37.9  | 0.06               | 0.06                                                                                                                                                   |             |
| JEM [17]                   | 8.76        | 38.4  | 0.06               | 0.06                                                                                                                                                   |             |
| BigGAN [3]                 | 9.22        | 14.73 | 0.06               | 0.06                                                                                                                                                   |             |
| StyleGAN2 + ADA (v1) [29]  | 10.06       | 2.67  | 0.06               | 0.06                                                                                                                                                   |             |
| Unconditional              |             |       |                    | Objective                                                                                                                                              | IS          |
| Diffusion (original) [53]  | ≤ 5.40      | L     | 0.06               | 0.06                                                                                                                                                   |             |
| Gated PixelCNN [59]        | 4.60        | 65.93 | 3.03 (2.90)        | L, learned diagonal Σ                                                                                                                                  | 7.28 ± 0.10 |
| Sparse Transformer [7]     | 5.29        | 49.46 | 2.80               | L, fixed isotropic Σ                                                                                                                                   | 8.06 ± 0.09 |
| PixelQN [43]               | 6.78        | 38.2  | 0.06               | 0.06                                                                                                                                                   |             |
| EBM [11]                   | 6.78        | 31.75 | 0.06               | 0.06                                                                                                                                                   |             |
| NCSNv2 [56]                | 8.87 ± 0.12 | 31.75 | 0.06               | 0.06                                                                                                                                                   |             |
| NCSN [55]                  | 25.32       | 25.32 | 0.06               | 0.06                                                                                                                                                   |             |
| SNGAN [39]                 | 8.22 ± 0.05 | 0.05  | 0.05               | 0.05                                                                                                                                                   |             |
| SNGAN-DDLS [4]             | 0.99 ± 0.10 | 15.42 | 0.05               | 0.05                                                                                                                                                   |             |
| StyleGAN2                  | 9.74 ± 0.05 | 3.26  | 0.05               | 0.05                                                                                                                                                   |             |
| Ours (L, fixed isotropic ) | 7.67 ± 0.13 | 13.51 | ≤ 3.70 (3.69)      | 0.05                                                                                                                                                   |             |
| Ours (L, simple )          | 9.46 ± 0.11 | 3.17  | ≤ 3.75 (3.72)      | 0.05                                                                                                                                                   |             |

training. However, we found it beneficial to sample quality (and simpler to implement) to train on the following variant of the variational bound:

Figure 3: LSUN Church samples. FID=7.89

<!-- image -->

## Algorithm 3 Sending x$\_{0}$

1: Send x$\_{T}$ ∼ q ( x$\_{T}$ | x$\_{0}$ ) using p ( x$\_{T}$ )

2: for t = T - 1 , . . . , 2 , 1 do

2:

3:

4:

5:

3: Send x$\_{T}$ ∼ q ( x$\_{T}$ | x$\_{1}$ +1 , x$\_{0}$ ) using p$\_{0}$ ( x$\_{1}$ | x$\_{t}$$\_{+1}$ )

4:

5:

Send x$\_{0}$ using p$\_{0}$ ( x$\_{0}$ | x$\_{0}$ )

end for

We find that training our models on the true variational bound yields better codelengths than training on the simplified objective, as expected, but the latter yields the best sample quality. See Fig. 1 for CIFAR10 and CelebA-HQ 256 × 256 samples, Fig. 3 and Fig. 4 for LSUN 256 × 256 samples [71], and Appendix D for more.

## 4.2 Reverse process parameterization and training objective ablation

In Table 2, we show the sample quality effects of reverse process parameterizations and training objectives (Section 3.2). We find that the baseline option of predicting 𝑖 works well only when trained on the true variational bound instead of unweighted mean squared error, a simplified objective akin to Eq. (14). We also see that learning reverse process variances (by incorporating a parameterized diagonal ∑ 𝑖 $\_{𝑑𝑡}$) into the variational bound) leads to unstable training and poorer sample quality compared to fixed variances. Predicting 𝑖 , as we proposed, performs approximately as well as predicting 𝜂 when trained on the variational bound with fixed variances, but much better when trained with our simplified objective.

## 4.3 Progressive coding

Table 1 also shows the codelengths of our CIFAR10 models. The gap between train and test is at most 0.03 bits per dimension, which is comparable to the gaps reported with other likelihood-based models and indicates that our diffusion model is not overfitting (see Appendix D for nearest neighbor visualizations). Still, while our lossless codelengths are better than the large estimates reported for energy based models and score matching using annealed importance sampling [11], they are not competitive with other types of likelihood-based generative models [7].

Since our samples are nonetheless of high quantity, we conclude that diffusion models have an inductive bias that makes them excellent lossy compressors. Treating the variational bound terms L$\_{1}$ + · · · + L$\_{T}$ as rate and L$\_{0}$ as distortion, our CIFAR10 model with the highest quality samples has a rate of 1.78 bits/dim and a distortion of 1.97 bits/dim, which amounts to a root mean squared error of 0.95 on a scale from 0 to 255. More than half of the lossless codelengths describe imperceptible distortions.

Progressive lossy compression We can probe further into the rate-distortion behavior of our model by introducing a progressive lossy code that mirrors the form of Eq. (5): see Algorithms 3 and 4, which assume access to a procedure, such as minimal random coding [19, 20], that can transmit a sample 𝑥 ∼ 𝑞 ( 𝑥 ) using approximately D$\_{KL}$ ( 𝑥 ( 𝑞 )) || 𝑝 ( 𝑥 ) 〉 bits on average for any distributions 𝑝 and 𝑞 , for which only 𝑝 is available to the receiver beforehand. When applied to 𝑥$\_{0}$ ∼ 𝑞 ( 𝑥$\_{0}$ ) , Algorithms 3 and 4 transmit 𝑥$\_{𝑡}$ , . . . , 𝑥$\_{0}$ in sequence using a total expected codelength equal to Eq. (5). The receiver,

at any time t , has the partial information x$\_{t}$ fully available and can progressively estimate:

$$\mathbf x _ { 0 } \approx \mathbf x _ { 0 } = \left ( \mathbf x _ { t } - \sqrt { 1 - \frac { \alpha _ { t } \ell _ { 0 } } { \alpha _ { t } } } \mathbf x _ { t } \right ) / \sqrt { \frac { \alpha _ { t } } { \alpha _ { t } } }$$

due to Eq. (4). (A stochastic reconstruction x$\_{0}$ ∼ ρ$\_{0}$ ( x$\_{0}$ ) x$\_{t}$ ) is also valid, but we do not consider it here because it makes distortion more difficult to evaluate.) Figure 5 shows the resulting ratedistortion plot on the CIFAR10 test set. At each time t , the distortion is calculated as the root mean squared error √ ‖ x$\_{0}$ - x$\_{0}$ - x$\_{0}$ ‖ $^{2}$/D , and the rate is calculated as the cumulative number of bits received so far at time t . The distortion decreases steeply in the low-rate region of the rate-distortion plot, indicating that the majority of the bits are indeed allocated to imperceptible distortions.

line chart

<!-- image -->

|   Ratio (RMS) |   Rise (RMS) |
|---------------|--------------|
|             0 |            0 |
|           200 |            0 |
|           400 |            0 |
|           600 |            0 |
|           800 |            0 |
|          1000 |            0 |

Progressive generation We also run a progressive unconditional generation process given by progressive decompression from random bits. In other words, we predict the result of the reverse process, ¯ x$\_{0}$ , while sampling from the reverse process using Algorithm 2. Figures 6 and 10 show the resulting sample quality of ¯ x$\_{0}$ over the course of the reverse process. Large scale image features appear first and details appear last. Figure 7 shows stochastic prediction x$\_{0}$ ∼ ρ$\_{0}$ ( x$\_{0}$ ) x$\_{t}$ ) with x$\_{t}$ frozen for various t . When t is small, all but fine details are preserved, and when t is large, only large scale features are preserved. Perhaps these are hints of conceptual compression [18].

Figure 6: Unconditional CIFAR10 progressive generation (¯ x$\_{0}$ over time, from left to right). Extended samples and sample quality metrics over time in the appendix (Figs. 10 and 14).

<!-- image -->

Figure 7: When conditioned on the same latent, Celeba-HQ 256 × 256 samples share high-level attributes. Bottom-right quadrants are x$\_{t}$$\_{1}$ , and other quadrants are samples from ρ$\_{0}$ ( x$\_{0}$ ) x$\_{t}$ .

<!-- image -->

Connection to autoregressive decoding Note that the variational bound (5) can be rewritten as:

$$L = D _ { K L } ( q ( x _ { T } ) \, \| \, \rho ( x _ { T } ) ) + \sum _ { t \geq 1 } D _ { K L } ( q ( x _ { t - 1 } ) \, \| \, \rho _ { 0 } ( x _ { t - 1 } ) ) \, \, \, + H ( x _ { 0 } ) \quad ( 1 6 )$$

(See Appendix A for a derivation.) Now consider setting the diffusion process length T to the dimensionality of the data, defining the forward process so that q ( x$\_{t}$ | x$\_{0}$ ) places all probability mass on x$\_{0}$ with the first t coordinates masked out (i.e. q ( x$\_{t}$ | x$\_{t}$$\_{-}$$\_{1}$ ) masks out the t th coordinate), setting ρ ( x$\_{T}$ ) to place all mass on a blank image, and, for the sake of argument, taking ρ$\_{0}$ ( x$\_{t}$$\_{-}$$\_{1}$ | x$\_{t}$ ) to

Figure 8: Interpolations of CelebA-HQ 256x256 images with 500 timesteps of diffusion.

<!-- image -->

be a fully expressive conditional distribution. With these choices, D$\_{KL}$ ( q ( x$\_{T}$ ) || p ( x$\_{T}$ )) = 0, and minimizing D$\_{KL}$ ( q ( x$\_{T}$ - 1) || x$\_{T}$ ) p ( x$\_{T}$ - 1) x$\_{T}$ trains to copy coordinates t + 1, ..., t unchanged and to predict the t th coordinate given t + 1, ..., T . Thus, training p$\_{θ}$ with this particular diffusion is training an autoregressive model.

We can therefore interpret the Gaussian diffusion model (2) as a kind of autoregressive model with a generalized bit ordering that cannot be expressed by reordering data coordinates. Prior work has shown that such reorderings introduce inductive biases that have an impact on sample quality [38], so we speculate that the Gaussian diffusion serves a similar purpose, perhaps to greater effect since Gaussian noise might be more natural to add to images compared to masking noise. Moreover, the Gaussian diffusion length is not restricted to equal the data dimension; for instance, we use T = 1000, which is less than the dimension of the 32 × 32 × 3 or 256 × 256 × 3 images in our experiments. Gaussian diffusions can be made shorter for fast sampling or longer for model expressiveness.

## 4.4 Interpolation

We can interpolate source images x$\_{0}$, x$\_{0}$ ∼ q ( x$\_{0}$ ) in latent space using q as a stochastic encoder, x$\_{t}$, x$\_{t}$ ∼ q ( x$\_{t}$ ) [ x$\_{0}$ ] , then decoding the linearly interpolated latent φ$\_{t}$ = (1 - λ ) x$\_{0}$ + λ φ$\_{x}$$\_{0}$ into image space by the reverse process, χ$\_{0}$ ∼ ρ ( x$\_{0}$ ) [ x$\_{0}$ ] . In effect, we use the reverse process to remove artifacts from linearly interpolating corrupted versions of the source images, as depicted in Fig. 8 (left). We fix the noise for different values of λ so χ$\_{x}$ and η$\_{x}$ remain the same. Fig. 8 (right) shows interpolations and reconstructions of original CelebA-HQ 256 × 256 images (t = 500). The reverse process produces high-quality reconstructions, and plausible interpolations that smoothly vary attributes such as pose, skin tone, hairstyle, expression and background, but not eyewear. Larger t results in coarser and more varied interpolations, with novel samples at t = 1000 (Appendix Fig. 9).

## 5 Related Work

While diffusion models might resemble flows [9, 46, 10, 32, 5, 16, 23] and VAEs [33, 47, 37], diffusion models are designed so that q has no parameters and the top-level latent x$\_{T}$ has nearly zero mutual information with the data χ$\_{0}$ . Our e-prediction reverse process parameterization establishes a connection between diffusion models and denoising score matching over multiple noise levels with annealed Langevin dynamics for sampling [55, 56]. Diffusion models, however, admit straightforward log likelihood evaluation, and the training procedure explicitly trains the Langevin dynamics sampler using variational inference (see Appendix C. for details). The connection also has the reverse implication that a certain weighted form of denoising score matching is the same as variational inference to train a Langevin-like sampler. Other methods for learning transition operators of Markov chains include infusion training [2], variational walkback [15], generative stochastic networks [1], and others [50, 54, 36, 42, 35, 65].

By the known connection between score matching and energy-based modeling, our work could have implications for other recent work on energy-based models [67-69, 12, 70, 13, 11, 41, 17, 8]. Our rate-distortion curves are computed over time in one evaluation of the variational bound, reminiscent of how rate-distortion curves can be computed over distortion penalties in one run of annealed importance sampling [24]. Our progressive decoding argument can be seen in convolutional DRAW and related models [18, 40] and may also lead to more general designs for subscale orderings or sampling strategies for autoregressive models [38, 64].

## 6 Conclusion

We have presented high quality image samples using diffusion models, and we have found connections among diffusion models and variational inference for training Markov chains, denoising score matching and annealed Langevin dynamics (and energy-based models by extension), autoregressive models, and progressive lossy compression. Since diffusion models seem to have excellent inductive biases for image data, we look forward to investigating their utility in other data modalities and as components in other types of generative models and machine learning systems.

## Broader Impact

Our work on diffusion models takes on a similar scope as existing work on other types of deep generative models, such as efforts to improve the sample quality of GANs, flows, autoregressive models, and so forth. Our paper represents progress in making diffusion models a generally useful tool in this family of techniques, so it may serve to amplify any impacts that generative models have had (and will have) on the broader world.

Unfortunately, there are numerous well-known malicious uses of generative models. Sample generation techniques can be employed to produce fake images and videos of high profile figures for political purposes. While fake images were manually created long before software tools were available, generative models such as ours make the process easier. Fortunately, CNN-generated images currently have subtle flaws that allow detection [62], but improvements in generative models may make this more difficult. Generative models also reflect the biases in the datasets on which they are trained. As many large datasets are collected from the internet by automated systems, it can be difficult to remove these biases, especially when the images are unlabeled. If samples from generative models trained on these datasets proliferate throughout the internet, then these biases will only be reinforced further.

On the other hand, diffusion models may be useful for data compression, which, as data becomes higher resolution and as global internet traffic increases, might be crucial to ensure accessibility of the internet to wide audiences. Our work might contribute to representation learning on unlabeled raw data for a large range of downstream tasks, from image classification to reinforcement learning, and diffusion models might also become viable for creative uses in art, photography, and music.

## Acknowledgments and Disclosure of Funding

This work was supported by ONR PECASE and the NSF Graduate Research Fellowship under grant number DGE-1752814. Google's TensorFlow Research Cloud (TFRC) provided Cloud TPUs.

## References

- [1] Guillaume Alain, Yoshua Bengio, Li Yao, Jason Yosinski, Eric Thibodeau-Laufer, Saizheng Zhang, and Pascal Vincent. GSNs: generative stochastic networks. Information and Inference: A Journal of the IMA , 5(2):210-249, 2016.
- [2] Florian Bordes, Sina Honari, and Pascal Vincent. Learning to generate samples from noise through infusion training. In International Conference on Learning Representations , 2017.
- [3] Andrew Brock, Jeff Donahue, and Karen Simonyan. Large scale GAN training for high fidelity natural image synthesis. In International Conference on Learning Representations , 2019.
- [4] Tong Che, Ruixiang Zhang, Jascha Sohl-Dickstein, Hugo Larochelle, Liam Paul, Yuan Cao, and Yoshua Bengio. Your GAN is secretly an energy-based model and you should use discriminator driven latent sampling. arXiv preprint arXiv:2003.06060 , 2020.
- [5] Tian Qi Chen, Yulia Rubanova, Jesse Bettencourt, and David K Duvenaud. Neural ordinary differential equations. In Advances in Neural Information Processing Systems , pages 6571-6583, 2018.
- [6] Xi Chen, Nikhil Mishra, Mostafa Rohaninejad, and Pieter Abbeel. PixelSNAIL: An improved autoregressive generative model. In International Conference on Machine Learning , pages 863-871, 2018.
- [7] Rewon Child, Scott Gray, Alec Radford, and Illya Sutskever. Generating long sequences with sparse transformers. arXiv preprint arXiv:1904.10509 , 2019.

| [8]   | Yuntian Deng, Anton Bakhtin, Myle Ott, Arthur Szlam, and Marc' Aurelio Ranzato. Residual energy-based models for text generation. arXiv preprint arXiv:2004.11714 , 2020.                                                                                                              |
|-------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [9]   | Lauren Dinh, David Krueger, and Yoshua Bengio. NICE: Non-linear independent components estimation. arXiv preprint arXiv:1410.8516 , 2014.                                                                                                                                              |
| [10]  | Lauren Dinh, Jascha Sohl-Dickstein, and Samy Bengio. Density estimation using Real NVP. arXiv preprint arXiv:1605.08803 , 2016.                                                                                                                                                        |
| [11]  | Yilun Du and Igor Mordatch. Implicit generation and modeling with energy based models. In Advances in Neural Information Processing Systems , pages 3603-3613, 2019.                                                                                                                   |
| [12]  | Ruiqi Gao, Yang Lu, Junpei Zhou, Song-Chun Zhu, and Ying Nian Wu. Learning generative ConvNets via multi-grid modeling and sampling. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition , pages 9155-9164, 2018.                                         |
| [13]  | Ruiqi Gao, Erik Nikjamp, Diederik P Kingma, Zhen Xu, Andrew M Dai, and Ying Nian Wu. Flow contrastive estimation of energy-based models. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition , pages 7518-7528, 2020.                                 |
| [14]  | Ian Godfellow, Jean Pouget-Abdiale, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron Courville, and Yoshua Bengio. Generative adversarial nets. In Advances in Neural Information Processing Systems , pages 2672-2680, 2014.                                            |
| [15]  | Anirudh Goyal, Nan Rosemary Ke, Surya Ganguli, and Yoshua Bengio. Variational walkback: Learning a transition operator as a stochastic recurrent net. In Advances in Neural Information Processing Systems , pages 4392-4402, 2017.                                                    |
| [16]  | Will Grathrowli, Ricky T. Q. Chen, Jesse Betencourt, and David Duvenaud. FFJORD: Free-form continuous dynamics for scalable reversible generative models. In International Conference on Learning Representations , 2019.                                                              |
| [17]  | Will Grathrowli, Kuan-Chieh Wang, Joen-Herrink Jacobsen, David Duvenaud, Mohammad Norouzi, and Kevin Swersky. Your classifier is secretly an energy based model and you should treat it like one. In International Conference on Learning Representations , 2020.                      |
| [18]  | Karol Gregor, Frederic Besse, Danilo Jimenez Rezende, Ivo Danihelka, and Daan Wierstra. Towards conceptual compression. In Advances in Neural Information Processing Systems , pages 3549-3557, 2016.                                                                                  |
| [19]  | Prahladh Harsha, Rahul Jain, David McAllester, and Jaikumar Radhakrishnan. The communication complexity of correlation. In Twenty-Second Annual IEEE Conference on Computational Complexity (CCC'07) , pages 10-23. IEEE, 2007.                                                        |
| [20]  | Marton Havasi, Robert Peharz, and José Miguel Hernández-Lobato. Minimal random code learning: Getting bits back from compressed model parameters. In International Conference on Learning Representations , 2019.                                                                      |
| [21]  | Martin Heusel, Hubert Ramsauer, Thomas Unterthiner, Bernhard Nessler, and Sepp Hochreiter. GANs trained by a two-time-scale update rule converge to a local Nash equilibrium. In Advances in Neural Information Processing Systems , pages 6626-6637, 2017.                            |
| [22]  | Irina Higgins, Loo Michet, Arka Pal, Christopher Burgess, Xavier Glorot, Matthew Botvinick, Shakir Mohamed, and Alexander Lerchner. beta-VAE: Learning basic visual concepts with a constrained variational framework. In International Conference on Learning Representations , 2017. |
| [23]  | Jonathan Ho, Xi Chen, Aravind Sinvas, Yan Duan, and Pieter Abbeel. Flow++: Improving flow-based generative models with variational dequantization and architecture design. In International Conference on Machine Learning , 2019.                                                     |
| [24]  | Sicong Huang, Alireza Makhzani, Yanshui Cao, and Roger Grosse. Evaluating lossy compression rates of deep generative models. In International Conference on Machine Learning , 2020.                                                                                                   |
| [25]  | Nal Kalchbrenner, Aaron van den Oord, Karen Simonyan, Ivo Danihelka, Oriol Vinyals, Alex Graves, and Koray Kavukcuoglu. Video pixel networks. In International Conference on Machine Learning , pages 1771-1779, 2017.                                                                 |
| [26]  | Nal Kalchbrenner, Erich Elsen, Karen Simonyan, Seb Noury, Norman Casagrande, Edward Lockhart, Florian Stimberg, Aaron van den Oord, Sander Dieleman, and Koray Kavukcuoglu. Efficient neural audio synthesis. In International Conference on Machine Learning , pages 2410-2419, 2018. |
| [27]  | Tero Karras, Timo Aila, Samuli Laine, and Jaakko Lehtinen. Progressive growing of GANs for improved quality, stability, and variation. In International Conference on Learning Representations , 2018.                                                                                 |
| [28]  | Tero Karras, Samuli Laine, and Timo Aila. A style-based generator architecture for generative adversarial networks. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition , pages                                                                           |

- [29] Tero Karras, Miika Aittala, Janne Hellsten, Samiuli Laine, Jaakko Lehtinen, and Timo Aila. Training generative adversarial networks with limited data. arXiv preprint arXiv:2006.06676v1 , 2020.
- [30] Tero Karras, Samuli Laine, Miika Aittala, Janne Hellsten, Jaakko Lehtinen, and Timo Aila. Analyzing and improving the image quality of StyleGAN. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition , pages 8110-8119, 2020.
- [31] Diederik P Kingma and Jimmy Ba. Adam: A method for stochastic optimization. In International Conference on Learning Representations , 2015.
- [32] Diederik P Kingma and Prafulla Dhariwal. Glow: Generative flow with invertible 1x1 convolutions. In Advances in Neural Information Processing Systems , pages 10215-10224, 2018.
- [33] Diederik P Kingma and Max Welling. Auto-encoding variational Bayes. arXiv preprint arXiv:1312.6114 , 2013.
- [34] Diederik P Kingma, Tim Salimans, Rafal Jofezowicz, Xi Chen, Ilya Sutskever, and Max Welling. Improved variational inference with inverse autoregressive flow. In Advances in Neural Information Processing Systems , pages 4743-4751, 2016.
- [35] John Lawson, George Tucker, Bo Dai, and Rajesh Ranganath. Energy-inspired models: Learning with sample-induced distributions. In Advances in Neural Information Processing Systems , pages 8501-8513, 2019.
- [36] Daniel Levy, Matt D. Hoffman, and Jascha Sohl-Dickstein. Generalizing Hamiltonian Monte Carlo with neural networks. In International Conference on Learning Representations , 2018.
- [37] Lars Maaløe, Marco Fraccaro, Valentin Liïvin, and Ole Winther. BIVA: A very deep hierarchy of latent variables for generative modeling. In Advances in Neural Information Processing Systems , pages 6548-6558, 2019.
- [38] Jacob Menick and Nal Kalchbrenner. Generating high fidelity images with subscale pixel networks and multidimensional upscaling. In International Conference on Learning Representations , 2019.
- [39] Takeru Miyato, Toshiki Kataoka, Masanori Koyama, and Yuichi Yoshida. Spectral normalization for generative adversarial networks. In International Conference on Learning Representations , 2018.
- [40] Alex Nichol. VQ-DRAW: A sequential discrete VAE. arXiv preprint arXiv:2003.01599 , 2020.
- [41] Erik Nijkamp, Micht Hill, Tian Han, Song-Chun Zhu, and Ying Nian Wu. On the anatomy of MCMC-based maximum likelihood learning of energy-based models. arXiv preprint arXiv:1903.12370 , 2019.
- [42] Erik Nijkamp, Micht Hill, Song-Chun Zhu, and Ying Nian Wu. Learning non-convergent non-persistent short-run MCMC toward energy-based model. In Advances in Neural Information Processing Systems , pages 5233-5243, 2019.
- [43] Georg Ostrovski, Will Dabney, and Remi Munos. Autoregressive quantile networks for generative modeling. In International Conference on Machine Learning , pages 3936-3945, 2018.
- [44] Ryan Prenger, Rafael Valle, and Bryan Catanzaro. WaveGlow: A flow-based generative network for speech synthesis. In ICASSP 2019-2019 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP) , pages 3617-3621. IEEE, 2019.
- [45] Ali Razavi, Aaron van den Oord, and Oriol Vinyals. Generating diverse high-fidelity images with VQVAE-2. In Advances in Neural Information Processing Systems , pages 14837-14847, 2019.
- [46] Danilo Rezende and Shakir Mohamed. Variational inference with normalizing flows. In International Conference on Machine Learning , pages 1530-1538, 2015.
- [47] Danilo Jimenez Rezende, Shakir Mohamed, and Daan Wierstra. Stochastic backpropagation and approximate inference in deep generative models. In International Conference on Machine Learning , pages 1278-1286, 2014.
- [48] Olaf Ronneberger, Philipp Fischer, and Thomas Brox. U-Net: Convolutional networks for biomedical image segmentation. In International Conference on Medical Image Computing and Computer-Assisted Intervention , pages 234-241. Springer, 2015.
- [49] Tim Salimans and Durk P Kingma. Weight normalization: A simple reparameterization to accelerate training of deep neural networks. In Advances in Neural Information Processing Systems , pages 901-909, 2016.
- [50] Tim Salimans, Diederik Kingma, and Max Welling. Markov Chain Monte Carlo and variational inference: Bridging the gap. In International Conference on Machine Learning , pages 1218-1226, 2015.

| [51]   | Tim Salimans, Ian Goodfellow, Wojciech Zaremba, Vicki Cheung, Alec Radford, and Xi Chen. Improved techniques for training gans. In Advances in Neural Information Processing Systems , pages 2234-2242, 2016.                                                     |
|--------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [52]   | Tim Salimans, Andrej Karpathy, Xi Chen, and Diederik P Kingma. PixelCNN++: Improving the PixelCNN with discretized logistic mixture likelihood and other modifications. In International Conference on Learning Representations , 2017.                           |
| [53]   | Jascha Sohl-Dickstein, Eric Weiss, Niu Maheswaranathan, and Surya Ganguli. Deep unsupervised learning using nonequilibrium thermodynamics. In International Conference on Machine Learning , pages 2256-2265, 2015.                                               |
| [54]   | Jiaming Song, Shengjia Zhao, and Stefano Ermon. A-NICE-MC: Adversarial training for MCMC. In Advances in Neural Information Processing Systems , pages 5140-5150, 2017.                                                                                           |
| [55]   | Yang Song and Stefano Ermon. Generative modeling by estimating gradients of the data distribution. In Advances in Neural Information Processing Systems , pages 11895-11907, 2019.                                                                                |
| [56]   | Yang Song and Stefano Ermon. Improved techniques for training score-based generative models. arXiv preprint arXiv:2006.09011 , 2020.                                                                                                                              |
| [57]   | Aaron van den Oord, Sander Dieleman, Heiga Zen, Karen Simonyan, Oriol Vinyals, Alex Graves, Nal Kalchbrenner, Andrew Senior, and Koraov Kavukcuoglu. WaveNet: A generative model for raw audio. arXiv preprint arXiv:1609.03499 , 2016.                           |
| [58]   | Aaron van den Oord, Nal Kalchbrenner, and Koray Kavukcuoglu. Pixel recurrent neural networks. International Conference on Machine Learning , 2016.                                                                                                                |
| [59]   | Aaron van den Oord, Nal Kalchbrenner, Oriol Vinyals, Lasse Espeholt, Alex Graves, and Koray Kavukcuoglu. Conditional image generation with PixelCNN decoders. In Advances in Neural Information Processing Systems , pages 4790-4798, 2016.                       |
| [60]   | Ashish Vaswani, Noam Shazeer, Niko Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is all you need. In Advances in Neural Information Processing Systems , pages 599-6008, 2017.                              |
| [61]   | Pascal Vincent. A connection between score matching and denoising autoencoders. Neural Computation , 23(7):1661-1674, 2011.                                                                                                                                       |
| [62]   | Sheng-Yu Wang, Oliver Wang, Richard Zhang, Andrew Owens, and Alexei A Efros. Cnn-generated images are surprisingly easy to spot.for now. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition , 2020.                                 |
| [63]   | Xiaolong Wang, Ross Girshick, Abhinav Gupta, and Kaiming He. Non-local neural networks. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition , pages 7794-7803, 2018.                                                                 |
| [64]   | Auke J Wiggers and Emiel Hoogeboom. Predictive sampling with forecasting autoregressive models. arXiv preprint arXiv:2002.09928 , 2020.                                                                                                                           |
| [65]   | Hao Wu, Jonas Köhler, and Frank Noé. Stochastic normalizing flows. arXiv preprint arXiv:2002.06707 , 2020.                                                                                                                                                        |
| [66]   | Yuxin Wu and Kaiming He. Group normalization. In Proceedings of the European Conference on Computer Vision (ECCV) , pages 3-19, 2018.                                                                                                                             |
| [67]   | Jianwen Xie, Yang Lu, Song-Chun Zhu, and Yingnian Wu. A theory of generative convnet. In International Conference on Machine Learning , pages 2635-2644, 2016.                                                                                                    |
| [68]   | Jianwen Xie, Song-Chun Zhu, and Ying Nian Wu. Synthesizing dynamic patterns by spatial-temporal generative convnet. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition , pages 7093-7101, 2017.                                     |
| [69]   | Jianwen Xie, Zilong Zheng, Ruiqui Gao, Wenguan Wang, Song-Chun Zhu, and Ying Nian Wu. Learning descriptor networks for 3d shape synthesis and analysis. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition , pages 8629-8638, 2018. |
| [70]   | Jianwen Xie, Song-Chun Zhu, and Ying Nian Wu. Learning energy-based spatial-temporal generative convnets for dynamic patterns. IEEE Transactions on Pattern Analysis and Machine Intelligence , 2019.                                                             |
| [71]   | Fisher Yu, Yinda Zhang, Shuran Song, Ari Seff, and Jianxiong Xiao. LSN: Construction of a large-scale image dataset using deep learning with humans in the loop. arXiv preprint arXiv:1506.03365 , 2015.                                                          |
| [72]   | Sergey Zagoruyko and Nikos Komodakis. Wide residual networks. arXiv preprint arXiv:1605.07146 , 2016.                                                                                                                                                             |

## Extra information

LSUN FID scores for LSUN datasets are included in Table 3. Scores marked with * are reported by StyleGAN2 as baselines, and other scores are reported by their respective authors.

Table 3: FID scores for LSUN 256 × 256 datasets

|                              | Table 3: FID scores for LSUN 256 × 256 datasets   | Table 3: FID scores for LSUN 256 × 256 datasets   | Table 3: FID scores for LSUN 256 × 256 datasets   | Table 3: FID scores for LSUN 256 × 256 datasets   |
|------------------------------|---------------------------------------------------|---------------------------------------------------|---------------------------------------------------|---------------------------------------------------|
| Model                        | LSUN Bedroom                                      | LSUN Church                                       | LSUN Cat                                          |                                                   |
| ProgressiveGAN [27]          | 8.34                                              | 6.42                                              | 37.52                                             |                                                   |
| StyleGAN [28]                | 2.65                                              | 4.21*                                             | 8.53*                                             |                                                   |
| StyleGAN2 [30]               | -                                                 | 3.86                                              | 6.93                                              |                                                   |
| Ours ( L$_{simple}$ )        | 6.36                                              | 7.89                                              | 19.75                                             |                                                   |
| Ours ( L$_{simple}$ , large) | 4.90                                              | -                                                 | -                                                 |                                                   |

Progressive compression Our lossy compression argument in Section 4.3 is only a proof of concept, because Algorithms 3 and 4 depend on a procedure such as minimal random coding [20], which is not tractable for high dimensional data. These algorithms serve as a compression interpretation of the variational bound (5) of Sohl-Dickstein et al. [53], not yet as a practical compression system.

Table 4: Unconditional CIFAR10 test set rate-distortion values (accompanies Fig. 5)

| Table 4: Unconditional CIFAR10 test set rate-distortion values (accompanies Fig. 5)   | Table 4: Unconditional CIFAR10 test set rate-distortion values (accompanies Fig. 5)   | Table 4: Unconditional CIFAR10 test set rate-distortion values (accompanies Fig. 5)   | Table 4: Unconditional CIFAR10 test set rate-distortion values (accompanies Fig. 5)   |
|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| Reverse process time ( T - t + 1 )                                                    | Rate (bits/dim)                                                                       | Distortion (RMSE [0 , 255])                                                           | Distortion (RMSE [0 , 255])                                                           |
| 1000                                                                                  | 1.77581                                                                               | 0.95136                                                                               |                                                                                       |
| 900                                                                                   | 0.11994                                                                               | 12.02277                                                                              |                                                                                       |
| 800                                                                                   | 0.05415                                                                               | 18.47482                                                                              |                                                                                       |
| 700                                                                                   | 0.02866                                                                               | 24.43656                                                                              |                                                                                       |
| 600                                                                                   | 0.01507                                                                               | 30.80948                                                                              |                                                                                       |
| 500                                                                                   | 0.00716                                                                               | 38.03236                                                                              |                                                                                       |
| 400                                                                                   | 0.00282                                                                               | 46.12765                                                                              |                                                                                       |
| 300                                                                                   | 0.00081                                                                               | 54.18826                                                                              |                                                                                       |
| 200                                                                                   | 0.00013                                                                               | 60.97170                                                                              |                                                                                       |
| 100                                                                                   | 0.00000                                                                               | 67.60125                                                                              |                                                                                       |

## A Extended derivations

Below is a derivation of Eq. (5), the reduced variance variational bound for diffusion models. This material is from Sohl-Dickstein et al. [53]; we include it here only for completeness.

$$L = \mathbb { E } _ { q } \left [ - \log \frac { \rho _ { 0 } ( \chi _ { 0 } \colon T ) } { q ( \chi _ { 1 } \colon T | \chi _ { 0 } ) } \right ] \\ = \mathbb { E } _ { q } \left [ - \log p ( \chi _ { 0 } \colon - \sum _ { t \geq 1 } \log \frac { \rho _ { 0 } ( \chi _ { 1 } \colon T | \chi _ { 0 } ) } { q ( \chi _ { 1 } | \chi _ { 0 } - t ) } \right ] \\ = \mathbb { E } _ { q } \left [ - \log p ( \chi _ { 1 } \colon - \sum _ { t > 1 } \log \frac { \rho _ { 0 } ( \chi _ { 1 } \colon T | \chi _ { 1 } ) } { q ( \chi _ { 1 } | \chi _ { 1 } - t ) } - \log \frac { \rho _ { 0 } ( \chi _ { 0 } | \chi _ { 1 } ) } { q ( \chi _ { 1 } | \chi _ { 0 } - t ) } \right ] \\ = \mathbb { E } _ { q } \left [ - \log p ( \chi _ { 1 } \colon - \sum _ { t > 1 } \log \frac { \rho _ { 0 } ( \chi _ { 1 } \colon T | \chi _ { 1 } ) } { q ( \chi _ { 1 } | \chi _ { 0 } - t ) } - \log \frac { \rho _ { 0 } ( \chi _ { 0 } | \chi _ { 1 } ) } { q ( \chi _ { 1 } | \chi _ { 0 } - t ) } \right ] \\ = \mathbb { E } _ { q } \left [ - \log p ( \chi _ { 1 } \colon - \sum _ { t > 1 } \log \frac { \rho _ { 0 } ( \chi _ { 1 } \colon T | \chi _ { 1 } ) } { q ( \chi _ { 1 } | \chi _ { 0 } - t ) } - \log \frac { \rho _ { 0 } ( \chi _ { 0 } | \chi _ { 1 } ) } { q ( \chi _ { 1 } | \chi _ { 0 } - t ) } \right ]$$

$$= \mathbb { E } _ { q } \left [ D _ { K L } ( q ( x _ { T } | x _ { 0 } ) \, \, \, \| \, \, p ( x _ { T } ) ) + \sum _ { t > 1 } D _ { K L } ( q ( x _ { t - 1 } | x _ { t }, x _ { 0 } ) \, \, \, \| \, \, p _ { 0 } ( x _ { t - 1 } | x _ { t } ) ) - \log p _ { 0 } ( x _ { 0 } | x _ { 1 } ) \right ]$$

The following is an alternate version of L . It is not tractable to estimate, but it is useful for our discussion in Section 4.3.

Final experiments were trained once and evaluated throughout training for sample quality. Sample quality scores and log likelihood are reported on the minimum FID value over the course of training. On CIFAR10, we calculated Inception and FID scores on 50000 samples using the original code from the OpenAI [51] and TTUR [21] repositories, respectively. On LSUN, we calculated FID scores on 50000 samples using code from the StyleGAN2 [30] repository. CIFAR10 and Celeba-HQ were loaded as provided by TensorFlow Datasets (https://www.tensorflow.org/datasets), and LSUN was prepared using code from StyleGAN. Dataset splits (or lack thereof) are standard from the papers that introduced their usage in a generative modeling context. All details can be found in the source code release.

## C Discussion on related work

Our model architecture, forward process definition, and prior differ from NCSN [55, 56] in subtle but important ways that improve sample quality, and, notably, we directly train our sampler as a latent variable model rather than adding it after training post-hoc. In greater detail:

- 1. We use a U-Net with self-attention; NCSN uses a RefineNet with dilated convolutions. We condition all layers on t by adding in the Transformer sinusoidal position embedding, rather than only in normalization layers (NCSNv1) or only at the output (v2).
- 2. Diffusion models scale down the data with each forward process step (by a √$\_{1}$$\_{-}$ β$\_{t}$ factor) so that variance does not grow when adding noise, thus providing consistently scaled inputs to the neural net reverse process. NCSN commits this scaling factor.
- 3. Unlike NCSN, our forward process destroys signal ( D$\_{k}$L$\_{t}$ ( q ( x$\_{t}$ ) | x$\_{0}$ ) | N ( 0 , I )) ≈ 0), ensuring a close match between the prior and aggregate posterior of x$\_{T}$ . Also unlike NCSN, our β$\_{t}$ are very small, which ensures that the forward process is reversible by a Markov chain with conditional Gaussians. Both of these factors prevent distribution shift when sampling.
- 4. Our Langevin-like sampler has coefficients (learning rate, noise scale, etc.) derived rigorously from β$\_{t}$ in the forward process. Thus, our training procedure directly trains our sampler to match the data distribution after T steps: it trains the sampler as a latent variable model using variational inference. In contrast, NCSN's sampler coefficients are set by hand post-hoc, and their training procedure is not guaranteed to directly optimize a quality metric of their sampler.

## D Samples

Additional samples Figure 11, 13, 16, 17, 18, and 19 show uncurrant samples from the diffusion models trained on Celeba-HQ, CIFAR10 and LSUN datasets.

Latent structure and reverse process stochasticity During sampling, both the prior x$\_{T}$ ∼ N ( 0 , 1 ) and Langevin dynamics are stochastic. To understand the significance of the second source of noise, we sampled multiple images conditioned on the same intermediate latent for the CelebA 256 × 256 dataset. Figure 7 shows multiple draws from the reverse process x$\_{0}$ ∼ ρ$\_{θ}$ ( x$\_{0}$ | x$\_{t}$ ) that share the latent x$\_{t}$ for t ∈ { 1000 , 750 , 500 , 250 } . To accomplish this, we run a single reverse chain from an initial draw from the prior. At the intermediate timesteps, the chain is split to sample multiple images. When the chain is split after the prior draw at x$\_{T}$ =1000 , the samples differ significantly. However, when the chain is split after more steps, samples share high-level attributes like gender, hair color, eyewear, saturation, pose and facial expression. This indicates that intermediate latents like x$\_{750}$ encode these attributes, despite their imprecitability.

Coarse-to-fine interpolation Figure 9 shows interpolations between a pair of source CelebA 256 × 256 images as we vary the number of diffusion steps prior to latent space interpolation. Increasing the number of diffusion steps destroys more structure in the source images, which the

model completes during the reverse process. This allows us to interpolate at both fine granularities and coarse granularities. In the limiting case of 0 diffusion steps, the interpolation mixes source images in pixel space. On the other hand, after 1000 diffusion steps, source information is lost and interpolations are novel samples.

Figure 9: Course-to-fine interpolations that vary the number of diffusion steps prior to latent mixing.

<!-- image -->

line chart

<!-- image -->

|   Inception Score |   FID |
|-------------------|-------|
|                 0 |     0 |
|               200 |   100 |
|               400 |   200 |
|               600 |   300 |
|               800 |   400 |
|              1000 |   500 |

line chart

<!-- image -->

|   FID |   Reverse process steps (T - t) |
|-------|---------------------------------|
|     0 |                               0 |
|   200 |                             200 |
|   400 |                             400 |
|   600 |                             600 |
|   800 |                             800 |
|  1000 |                            1000 |

Figure 11: CelebA-HQ 256 × 256 generated samples

<!-- image -->

(b) Inception feature space nearest neighbors

<!-- image -->

Figure 12: CelebA-HQ 256 × 256 nearest neighbors, computed on a 100 × 100 crop surrounding the faces. Generated samples are in the leftmost column, and training set nearest neighbors are in the remaining columns.

<!-- image -->

Figure 13: Unconditional CIFAR10 generated samples

<!-- image -->

Figure 14: Unconditional CIFAR10 progressive generation

<!-- image -->

Figure 15: Unconditional CIFAR10 nearest neighbors. Generated samples are in the leftmost column, and training set nearest neighbors are in the remaining columns.

<!-- image -->

Figure 16: LSUN Church generated samples. FID=7.89

<!-- image -->

Figure 17: LSUN Bedroom generated samples, large model. FID=4.90

<!-- image -->

Figure 18: LSUN Bedroom generated samples, small model. FID=6.36

<!-- image -->

Figure 19: LSUN Cat generated samples. FID=19.75

<!-- image -->