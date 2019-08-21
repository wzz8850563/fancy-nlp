# -*- coding: utf-8 -*-

import numpy as np
from absl import logging
from seqeval.metrics.sequence_labeling import get_entities


class NERPredictor(object):
    """NER predictor for evaluating ner model, output predictive probabilities and predictive tag
    sequences for input sentence"""
    def __init__(self, ner_model, preprocessor):
        """

        Args:
            ner_model: instance of ner model
            preprocessor: `NERPreprocessor` instance to prepare feature input for ner model
        """
        self.ner_model = ner_model
        self.preprocessor = preprocessor

    def predict_prob(self, text):
        """Return probabilities for one sentence

        Args:
            text: can be untokenized (str) or tokenized in char level (list)

        Returns: np.array, shaped [num_chars, num_classes]

        """
        if isinstance(text, list):
            logging.warning('Text is passed in a list. Make sure it is tokenized in char level!')
            features, _ = self.preprocessor.prepare_input([text])
        else:
            assert isinstance(text, str)
            features, _ = self.preprocessor.prepare_input([list(text)])
        pred_probs = self.ner_model.predict(features)
        return pred_probs[0]

    def predict_prob_batch(self, texts):
        """Return probabilities for a batch sentences

        Args:
            texts: a list of texts, each text can be untokenized (str) or
                   tokenized in char level (list)

        Returns: np.array, shaped [num_texts, num_chars, num_classes
        """
        assert isinstance(texts, list)
        if isinstance(texts[0], list):
            logging.warning('Text is passed in a list. Make sure it is tokenized in char level!')
            features, _ = self.preprocessor.prepare_input(texts)
        else:
            assert isinstance(texts[0], str)
            char_cut_texts = [list(text) for text in texts]
            features, _ = self.preprocessor.prepare_input(char_cut_texts)
        pred_probs = self.ner_model.predict(features)
        return pred_probs

    def tag(self, text):
        """Return tag sequence for one sentence

        Args:
            text: can be untokenized (str) or tokenized in char level (list)

        Returns: list of str

        """
        pred_prob = self.predict_prob(text)
        length = min(len(text), pred_prob.shape[0])
        tags = self.preprocessor.label_decode(np.expand_dims(pred_prob, 0), [length])
        return tags[0]

    def tag_batch(self, texts):
        """Return tag sequences for a batch sentences

        Args:
            texts: a list of text, each text can be untokenized (str) or
                   tokenized in char level (list)

        Returns: list of list of str

        """
        pred_probs = self.predict_prob_batch(texts)
        lengths = [min(len(text), pred_prob.shape[0]) for text, pred_prob in zip(texts, pred_probs)]
        tags = self.preprocessor.label_decode(pred_probs, lengths)
        return tags

    @staticmethod
    def entities(text, tag, pred_prob):
        """Return entity according to tag sequence

        """
        results = []
        chunks = get_entities(tag)

        for chunk_type, chunk_start, chunk_end in chunks:
            chunk_end += 1
            entity = {
                'text': ''.join(text[chunk_start: chunk_end]),
                'type': chunk_type,
                'score': float(np.average(pred_prob[chunk_start: chunk_end])),
                'beginOffset': chunk_start,
                'endOffset': chunk_end
            }
            results.append(entity)
        return results

    def pretty_tag(self, text):
        """Return tag sequence for one sentence in a pretty format

        Args:
            text: can be untokenized (str) or tokenized in char level (list)

        Returns:

        """
        pred_prob = self.predict_prob(text)
        length = min(len(text), pred_prob.shape[0])
        tag = self.preprocessor.label_decode(np.expand_dims(pred_prob, 0), [length])

        char_cut = text if isinstance(text, list) else list(text)
        results = {
            'chars': char_cut,
            'entities': self.entities(char_cut, tag, pred_prob)
        }
        return results

    def pretty_tag_batch(self, texts):
        pred_probs = self.predict_prob_batch(texts)
        lengths = [min(len(text), pred_prob.shape[0]) for text, pred_prob in zip(texts, pred_probs)]
        tags = self.preprocessor.label_decode(pred_probs, lengths)

        results = []
        for text, tag, pred_prob in zip(texts, tags, pred_probs):
            char_cut = text if isinstance(text, list) else list(text)
            results.append({
                'chars': char_cut,
                'entities': self.entities(char_cut, tag, pred_prob)
            })
        return results