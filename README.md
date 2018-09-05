# BrnoLM

A language modeling toolkit built on top of PyTorch, embracing Kaldi-style single-purpose executables.
Currently, it's still built for PyTorch 0.3.

## i-Vectors in Language Modeling: an Efficient Way of Domain Adaptation for Feed-Forward Models
This code (dozens of refactoring commits ago) has been used for experiments reported in an Interspeech 2018 submission (link to a PDF will be added soon).

For examples on training an i-vector FF LM, refer to folder `exp/is2018-smmlm`.
You'll need the implementation of [SMM](https://github.com/skesiraju/smm) around on your system, kindly change `balls/smm_itf/smm_ivec_extractor.py:10` to fit your setup.

## Coming soon
* Further cleanup
* Update to current PyTorch
* Additional decoder structures (NCE, hierarchical softmax, etc.)
