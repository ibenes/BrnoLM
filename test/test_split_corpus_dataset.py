import split_corpus_dataset
import ivec_appenders
import unittest

import numpy as np
import torch
import common

from utils import getStream

class BatchBuilderTest(unittest.TestCase):
    def setUp(self):
        self.vocab = {
            "a": 0,
            "b": 1,
            "c": 2
        }
        self.ivec_eetor = lambda x: torch.from_numpy(np.asarray([hash(x) % 1337], dtype=np.float32))
        self.ivec_app_ctor = lambda ts: ivec_appenders.CheatingIvecAppender(ts, self.ivec_eetor)

    def batch_equal(self, actual, expected, print_them=False):
        if print_them:
            print(expected)
            print(actual)

        self.assertEqual(len(actual), len(expected))

        for act_comp, exp_comp in zip(actual, expected):
            self.assertTrue(torch.equal(act_comp, exp_comp))

    def get_tokens(self, word_seqs):
        return [[self.vocab[w] for w in seq] for seq in word_seqs]

    def get_tokenized_splits(self, word_seqs, unroll):
        files = [getStream(seq) for seq in word_seqs] 
        tss = [split_corpus_dataset.TokenizedSplit(f, self.vocab, unroll) for f in files]
        
        return tss

    def test_even_batch_single_sample1(self):
        test_seqs = [
            "a b".split(),
            "b b".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor,len(tss))
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[0, 1]]),
            torch.LongTensor([[1, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in test_seqs]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

    def test_even_batch_single_sample2(self):
        test_seqs = [
            "b b".split(),
            "b c".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, len(tss))
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1, 1]]),
            torch.LongTensor([[1, 2]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in test_seqs]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

    def test_even_batch_single_sample_unroll2(self):
        test_seqs = [
            "a b c".split(),
            "b b b".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=2)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, len(tss))
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[0, 1], [1, 1]]),
            torch.LongTensor([[1, 1], [2, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in test_seqs]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

    def test_even_batch_multi_sample(self):
        test_seqs = [
            "a b c".split(),
            "b b b".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, len(tss))
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[0, 1]]),
            torch.LongTensor([[1, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in test_seqs]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1, 1]]),
            torch.LongTensor([[2, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in test_seqs]),
            torch.LongTensor([0, 1]),
        )

        self.batch_equal(batch, expectation)

    def test_even_batch_multi_sample_len(self):
        test_seqs = [
            "a b c".split(),
            "b b b".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, len(tss))
        batches = iter(batches)

        self.assertEqual(len(list(batches)), 2)

    def test_uneven_batch(self):
        test_seqs = [
            "a b".split(), 
            "b b b".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, len(tss))
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[0, 1]]),
            torch.LongTensor([[1, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in test_seqs]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1]]),
            torch.LongTensor([[1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in test_seqs[1:]]),
            torch.LongTensor([1])
        )

        self.batch_equal(batch, expectation)

    def test_batcher_requires_nonzero_bsz(self):
        test_seqs = [
            "b b".split(), 
            "b c".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        self.assertRaises(ValueError, split_corpus_dataset.BatchBuilder, tss, self.ivec_app_ctor, 0)

    def test_even_lenght_small_batch(self):
        test_seqs = [
            "b b".split(), 
            "b c".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, 1)
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1]]),
            torch.LongTensor([[1]]),
            torch.stack([self.ivec_eetor(" ".join(test_seqs[0][:-1]))]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1]]),
            torch.LongTensor([[2]]),
            torch.stack([self.ivec_eetor(" ".join(test_seqs[1][:-1]))]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

    def test_even_lenght_small_batch_2(self):
        test_seqs = [
            "a b".split(), 
            "b b".split(), 
            "b c".split(),
            "c a".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, 2)
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[0, 1]]),
            torch.LongTensor([[1, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in test_seqs[0:2]]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1, 2]]),
            torch.LongTensor([[2, 0]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in test_seqs[2:4]]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

    def test_uneven_length_small_batch(self):
        test_seqs = [
            "a b c".split(),
            "a b".split(),
            "b b b".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, 2)
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[0, 0]]),
            torch.LongTensor([[1, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in [test_seqs[0], test_seqs[1]]]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1, 1]]),
            torch.LongTensor([[2, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in [test_seqs[0], test_seqs[2]]]),
            torch.LongTensor([0]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1]]),
            torch.LongTensor([[1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in [test_seqs[2]]]),
            torch.LongTensor([1]),
        )

        self.batch_equal(batch, expectation)

    def test_insufficient_stream_length(self):
        test_seqs = [
            "a b c".split(),
            "a".split(),
            "b b b".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, 2)
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[0, 1]]),
            torch.LongTensor([[1, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in [test_seqs[0], test_seqs[2]]]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1, 1]]),
            torch.LongTensor([[2, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in [test_seqs[0], test_seqs[2]]]),
            torch.LongTensor([0,1]),
        )

        self.batch_equal(batch, expectation)

    def test_reproducibility(self):
        test_seqs = [
            "a b c".split(),
            "a b".split(),
            "b b b".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, 2)
        epoch1 = list(iter(batches))
        epoch2 = list(iter(batches))

        self.assertEqual(len(epoch1), len(epoch2))
        for b_e1, b_e2 in zip(epoch1, epoch2):
            self.batch_equal(b_e1, b_e2)

    def test_no_discard_even_lenght_small_batch(self):
        test_seqs = [
            "b b".split(), 
            "b c".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, 1, discard_h=False)
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1]]),
            torch.LongTensor([[1]]),
            torch.stack([self.ivec_eetor(" ".join(test_seqs[0][:-1]))]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1]]),
            torch.LongTensor([[2]]),
            torch.stack([self.ivec_eetor(" ".join(test_seqs[1][:-1]))]),
            torch.LongTensor([0]),
        )

        self.batch_equal(batch, expectation)

    def test_no_discard_uneven_length_small_batch(self):
        test_seqs = [
            "a b c".split(),
            "a b".split(),
            "b b b".split(),
        ]
        tss = self.get_tokenized_splits(test_seqs, unroll=1)
        tokens = self.get_tokens(test_seqs)

        batches = split_corpus_dataset.BatchBuilder(tss, self.ivec_app_ctor, 2, discard_h=False)
        batches = iter(batches)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[0, 0]]),
            torch.LongTensor([[1, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in [test_seqs[0], test_seqs[1]]]),
            torch.LongTensor([]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1, 1]]),
            torch.LongTensor([[2, 1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in [test_seqs[0], test_seqs[2]]]),
            torch.LongTensor([0,1]),
        )

        self.batch_equal(batch, expectation)

        batch = next(batches)
        expectation = (
            torch.LongTensor([[1]]),
            torch.LongTensor([[1]]),
            torch.stack([self.ivec_eetor(" ".join(words[:-1])) for words in [test_seqs[2]]]),
            torch.LongTensor([1]),
        )

        self.batch_equal(batch, expectation)

def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]


class TokenizedSplitTests(common.TestCase):
    def setUp(self):
        self.test_words_short = "a b c a".split()
        self.test_words_long = "a b c a a".split()

        self.vocab = {
            "a": 0,
            "b": 1,
            "c": 2
        }
        

    def test_single_word(self):
        data_source = getStream(self.test_words_short)
        ts = split_corpus_dataset.TokenizedSplit(data_source, self.vocab, 1)
        tokens_string = next(iter(ts))
        expectation = (torch.LongTensor([0]), torch.LongTensor([1])) # input, target
        self.assertEqual(tokens_string, expectation)

    def test_single_word_seq(self):
        data_source = getStream(self.test_words_short)
        ts = split_corpus_dataset.TokenizedSplit(data_source, self.vocab, 1)
        tokens_strings = list(iter(ts))
        expectation = [(torch.LongTensor([0]), torch.LongTensor([1])), (torch.LongTensor([1]), torch.LongTensor([2])), (torch.LongTensor([2]), torch.LongTensor([0]))]
        self.assertEqual(tokens_strings, expectation)

    def test_single_word_len(self):
        data_source = getStream(self.test_words_short)
        ts = split_corpus_dataset.TokenizedSplit(data_source, self.vocab, 1)
        self.assertEqual(len(ts), len(self.test_words_short)-1)

    def test_len_no_output(self):
        data_source = getStream(self.test_words_short)
        ts = split_corpus_dataset.TokenizedSplit(data_source, self.vocab, 5)
        self.assertEqual(len(ts), 0)

    def test_two_word_seq(self):
        data_source = getStream(self.test_words_short)
        ts = split_corpus_dataset.TokenizedSplit(data_source, self.vocab, 2)
        tokens_strings = list(iter(ts))
        expectation = [(torch.LongTensor([0, 1]), torch.LongTensor([1, 2]))]
        self.assertEqual(tokens_strings, expectation)

    def test_two_word_seq_long(self):
        data_source = getStream(self.test_words_long)
        ts = split_corpus_dataset.TokenizedSplit(data_source, self.vocab, 2)
        tokens_strings = list(iter(ts))
        expectation = [(torch.LongTensor([0, 1]), torch.LongTensor([1, 2])), (torch.LongTensor([2, 0]), torch.LongTensor([0, 0]))]
        self.assertEqual(tokens_strings, expectation)

    def test_single_word_retrieval(self):
        data_source = getStream(self.test_words_short)
        ts = split_corpus_dataset.TokenizedSplit(data_source, self.vocab, 1)
        words = list(ts.input_words())
        self.assertEqual(words, ['a', 'b', 'c']) # we expect the input words

    def test_two_word_retrieval(self):
        data_source = getStream(self.test_words_short)
        ts = split_corpus_dataset.TokenizedSplit(data_source, self.vocab, 2)
        words = list(ts.input_words())
        self.assertEqual(words, ['a b']) # we expect the input words
