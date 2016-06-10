#!/usr/bin/env python

###########################################################
# datasetup.py
#
# Given an initial unclustered ppset file, and optionally
# a seed gold cluster file, creates:
#   - Paraphrase set files in json format
#   - An empty Worker record file in json format
#
# The purpose of the seed gold cluster file is to seed
# the first round of the HIT with the 'gold' clusters
# already sorted. This is useful if you have a set of
# sense-clustered paraphrases already and want to sort
# new words into it.
###########################################################
import optparse
import sys
import os
import json
import copy
from collections import namedtuple
import paraphrase as pp

word_type = namedtuple("word_type", "word, type")

class CrowdPPSet:
    def __init__(self, ppst, goldppset, seeded):
        '''
        Re-arrange original ParaphraseSet and gold clustering solution into
        a format that's more json-friendly. Add crowd_gold attribute and a
        'matches' list for each paraphrase in the ParaphraseSet.
        :param ppset: ParaphraseSet
        :param goldppset: ParaphraseSet
        '''
        self.tgt = ppst.target_word
        self.pos = ppst.pos

        tempppset = copy.deepcopy(ppst)

        if seeded:
            tempgold = copy.deepcopy(goldppset)
            goldwords = set(tempgold.pp_dict.keys())
            tempgold.filter_sense_clustering(tempppset)
            del tempgold.word_type
            del tempgold.pp_dict
            del tempgold.target_word
            del tempgold.pos
            self.wn_gold = copy.deepcopy(tempgold)
            self.crowd_gold = copy.deepcopy(tempgold)
            self.crowd_gold['merges'] = {}
            del tempgold
        else:
            empty = {'sense_clustering': {}, 'cluster_count': 0, 'merges': {}}
            self.wn_gold = empty
            self.crowd_gold = empty
            goldwords = set([])

        del tempppset.pos
        del tempppset.word_type
        del tempppset.sense_clustering
        del tempppset.cluster_count
        for pword, p in tempppset.pp_dict.iteritems():
            del p.word_type
            del p.vector
            del p.pos
            p.matches = {}
            p.workers = set([])
            p.attempts = 0
            if pword in goldwords:
                p.state = 'gold'
            else:
                p.state = 'none'
        del tempppset.target_word
        self.ppset = copy.deepcopy(tempppset)
        del tempppset

        self.old_data = []
        self.unsorted = []
        self.sorted = []
        self.bogusword = 'bogus'
        self.crowdstarter = {}
        self.latest_timestamp = ''
        self.num_anno = 0
        self.lock = 0
        self.trash = []
        self.complete = 0  ## 1=done with clustering, 2=done final merges
        self.seeded = seeded


def jdefault(obj):
    if isinstance(obj, set):
        return list(obj)
    return obj.__dict__

if __name__ == "__main__":
    ## Get command line arguments
    optparser = optparse.OptionParser()
    optparser.add_option("-t", "--tgtlist", type="string", default='hit_data/pp/semeval_tgtlist_rand80', dest="tgtlist", help="File with target words")
    optparser.add_option("-p", "--ppfile", type="string", default='hit_data/pp/semeval_tgtlist_rand80_multiword_xxl_PPDB2.0Score.ppsets', dest="ppfile", help="File with paraphrase sets")
    optparser.add_option("-g", "--goldfile", type="string", default=None, dest="goldfile", help="File with WordNet gold seed clusters")

    optparser.add_option("-o", "--jsondir", type="string", default='hit_data/json', dest="jsondir")
    optparser.add_option("-w", "--workerdir", type="string", default='hit_data/workerjson', dest="workerdir")
    (opts, _) = optparser.parse_args()

    if opts.ppfile is None:
        sys.stderr.write('Provide target word file following -t flag\n')
        exit(0)

    tgtlist = []
    with open(opts.tgtlist, 'rU') as fin:
        for line in fin:
            w, pos = line.strip().split('.')
            tgt = word_type(w, pos)
            tgtlist.append(tgt)
    ppsets = {p: pps for p, pps in pp.read_pps(opts.ppfile).iteritems()
              if p in tgtlist}

    if opts.goldfile is None:
        sys.stdout.write('No gold seed cluster file provided...'
                         'setting up unseeded batch\n')
        seed = False
        crowdpps = {k: CrowdPPSet(ppsets[k], None, seed)
                    for k in ppsets.keys()}
    else:
        sys.stdout.write('Seeding first batch with crowd gold '
                         'clusters from %s\n' % opts.goldfile)
        seed = True
        goldclasses = pp.read_gold(opts.goldfile)
        crowdpps = {k: CrowdPPSet(ppsets[k], goldclasses[k], seed)
                    for k in ppsets.keys()}

    destdir = opts.jsondir
    for wt, cpps in crowdpps.iteritems():
        filename = wt.word+'.'+wt.type
        with open(os.path.join(destdir, filename), 'w') as fout:
            print >> fout, json.dumps(cpps, indent=2, default=jdefault)

    workers = {}
    with open(os.path.join(opts.workerdir, '0_workers.json'),'w') as fout:
        print >> fout, json.dumps(workers, indent=2, default=jdefault)
