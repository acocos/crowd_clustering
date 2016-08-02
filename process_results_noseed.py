#!/usr/bin/env python

###########################################################
# process_results_noseed.py
#
# Pull latest results for paraphrase clustering HIT from
# AMT results file, calculate worker accuracy, and update json
# files with results
#
# - For each worker, calculate accuracy at classifying
#   'bogus' term in trash; add workers below threshold to
#   a reject list
# - For each HIT, add clustering solution to appropriate
#   JSON file
# - For each HIT, check whether all workers have completed;
#   For each paraphrase in unsorted list, check agreement.
#   If agreement is over threshold, add that term to
#   crowd gold solution and update state of paraphrase
# - Accept valid HITs (from non-rejected workers)
#
###########################################################

import time
import os
import csv
import glob
import sys
import json
import optparse
from settings import settings
import networkx as nx
from scipy.stats import beta
from copy import deepcopy
import itertools

WORKER_ACC_THRESHOLD = settings['WORKER_ACC_THRESHOLD']
CLUSTER_AGR_THRESHOLD = settings['CLUSTER_AGR_THRESHOLD']
MERGE_THRESHOLD = settings['MERGE_THRESHOLD']
MAX_ATTEMPTS = settings['MAX_ATTEMPTS']


def binom_interval(success, total, confint=0.90):
    quantile = (1 - confint) / 2.
    lower = beta.ppf(quantile, success, total - success + 1)
    upper = beta.ppf(1 - quantile, success + 1, total - success)
    return (lower, upper)


def UnicodeDictReader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for row in csv_reader:
        goodrow = {}
        for key, value in row.iteritems():
            try:
                goodrow[key] = unicode(value, 'utf-8').encode('utf8')
            except TypeError:
                goodrow[key] = value
        yield goodrow


def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


def jdefault(obj):
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, frozenset):
        return list(obj)
    return obj.__dict__


def update_add(a, b):
    '''
    Combine contents of two dictionaries of dictionaries, by adding entries
    :return: dict, updated version of a
    '''
    bk = set(b.keys())
    ak = set(a.keys())
    for w in bk-ak:
        a[w] = b[w]
    for w in bk & ak:
        for k in a[w]:
            a[w][k] = a[w][k]+b[w][k]
    return a


def get_results_manual(rdf):
    if os.path.isdir(rdf):
        resultsfile = max(glob.iglob(rdf+'/*results.csv'))
    else:
        resultsfile = rdf
    res = [row for row in csv.DictReader(open(resultsfile, 'rU'))]
    return res, resultsfile


def strtolist(st):
    if st == '[]':
        return []
    else:
        st = st.replace('[','').replace(']','')
        l = st.split(', ')
        return [li[1:-1] for li in l]


if __name__ == "__main__":
    ## Get command line arguments
    optparser = optparse.OptionParser()
    optparser.add_option("-j", "--jsondir", type="string", default='hit_data/json', dest="jsondir", help="Directory containing paraphrase set json files")
    optparser.add_option("-r", "--resultsdirfile", type="string", default='hit_data/results', dest="resultsdirfile", help="Results directory (picks most recently updated) or .csv file")
    optparser.add_option("-w", "--workerdir", type="string", default='hit_data/workerjson', dest="workerdir")
    optparser.add_option("-c", "--clustermode", type="string", default='biconnected', dest="clustermode", help="Mode for clustering terms: 'biconnected' or 'clique'")

    (opts, _) = optparser.parse_args()

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    ## Get most up-to-date results
    results, resultsfile = get_results_manual(opts.resultsdirfile)

    ## First pass thru results: worker accuracy and correct/incorrect trash
    batchworkers = {}  # maintain worker performance data
    good_trash = set([])
    bad_trash = set([])
    targets = set([])
    bogalone_assignments = set([])
    for row in results:
        if row['AssignmentStatus'] == 'Submitted':  # only check new entries
            tgt = row['Answer.tgt']
            pos = row['Answer.pos']
            jsonfilename = '.'.join([tgt,pos])
            targets.add(jsonfilename)
            wid = row['WorkerId']
            if wid not in batchworkers:
                batchworkers[wid] = {'correct': 0,
                                     'incorrect': 0,
                                     'pct': 1.0,
                                     'correct_hits': [],
                                     'incorrect_hits': [],
                                     'incorrect_assignments': [],
                                     'correct_assignments': []}
            hit_id = row['HITId']
            bog = row['Answer.bogus']
            a_id = row['AssignmentId']
            trashbin = set(row['Answer.trash'].split('|')[0].split('@!'))

            ## Also approve if bogus term is alone in a bin
            bogalone = False
            for key,ans in row.iteritems():
                    if 'newbox' in key:
                        contents = list(set([k for k in ans.strip().split('|')[0].split('@!') if len(k)>0]))
                        if len(contents) == 1 and contents[0]==bog:
                            bogalone=True
                            bogalone_assignments.add(a_id)

            if bog in trashbin or bogalone:
                good_trash.add(a_id)
                batchworkers[wid]['correct'] += 1
                batchworkers[wid]['correct_hits'].append(hit_id)
                batchworkers[wid]['correct_assignments'].append(a_id)
            else:
                bad_trash.add(a_id)
                batchworkers[wid]['incorrect'] += 1
                batchworkers[wid]['incorrect_hits'].append(hit_id)
                batchworkers[wid]['incorrect_assignments'].append(a_id)
        else:
            print 'Ignoring AssignmentId %s (status is "%s", should be "Submitted" to process it)' \
                  % (str(row['AssignmentId']), row['AssignmentStatus'])

    ## Update worker records
    with open(max(glob.iglob(opts.workerdir+'/*workers.json')), 'rU') as fin:
        oldworkers = byteify(json.load(fin))
    batchworkers = update_add(batchworkers, oldworkers)
    blacklist = set([])  # maintain set of signif. low-accuracy workers
    for id, w in batchworkers.iteritems():
        success = binom_interval(w['correct'], w['correct']+w['incorrect'])[1]
        batchworkers[id]['pct'] = success
        if success < WORKER_ACC_THRESHOLD:
            blacklist.add(id)
    new_workerfile = timestamp+'_workers.json'
    with open(os.path.join(opts.workerdir, new_workerfile), 'w') as fout:
        print >> fout, json.dumps(batchworkers, indent=2, default=jdefault)

    ## Review each HIT result and update appropriate JSON file
    correct_submissions = {}
    output_data = []
    errcount = {t:0 for t in targets}
    for row in results:
        if row['AssignmentStatus'] == 'Submitted':  # only check new entries
            ## Record hit data
            tgt = row['Answer.tgt']
            pos = row['Answer.pos']
            jsonfilename = '.'.join([tgt,pos])
            bogus = row['Answer.bogus']
            hit_id = row['HITId']
            latest_timestamp = row['Answer.latest_timestamp']
            if jsonfilename not in correct_submissions:
                correct_submissions[jsonfilename] = 0
            ## Reject if worker in blacklist, otherwise accept. If worker did not correctly
            ## sort bogus word, give them a warning; still accept the result, since
            ## it enables us to keep HIT iterations atomic and shouldn't significantly impact
            ## the result (assuming very few bad HITs per target per round)
            wid = row['WorkerId']
            a_id = row['AssignmentId']
            if wid not in blacklist:
                row['Approve'] = 'X'
                if a_id in bogalone_assignments or a_id in bad_trash:
                    row['RequesterFeedback'] = settings['APPROVE_FEEDBACK_BOGALONE'] %(bogus, tgt)
                else:
                    row['RequesterFeedback'] = settings['APPROVE_FEEDBACK']
                correct_submissions[jsonfilename] += 1

                ## Process worker's clustering solution
                with open(os.path.join(opts.jsondir, jsonfilename),'rU') as fin:
                    oldjson = byteify(json.load(fin))
                unsorted = set(oldjson['unsorted'])
                cluster_assignments = {w: set([]) for w in unsorted}
                merges = []
                for key,ans in row.iteritems():
                    if 'goldclass' in key or 'newbox' in key or 'trash' in key:
                        contents = set(ans.strip().split('|')[0].split('@!')) - {bogus} - {''}
                        if 'newbox' in key:
                            cname = 'newbox'
                        else:
                            cname = key.replace('Answer.','')
                        for word in contents & unsorted:
                            cluster_assignments[word].add((cname, frozenset(contents)))
                    elif 'merged' in key and len(ans.strip()) > 0:
                        merges.append(frozenset([item for sublist in [m.split('|') for m in ans.strip().split(',')] for item in sublist]))
                for word, assgn in cluster_assignments.iteritems():
                    try:
                        oldjson['ppset']['pp_dict'][word]['workers'].append(wid)
                    except KeyError:
                        print jsonfilename, unsorted, word, assgn
                    for clus, contents in assgn:
                        try:
                            oldjson['ppset']['pp_dict'][word]['matches'][clus].append(contents)
                        except KeyError:
                            oldjson['ppset']['pp_dict'][word]['matches'][clus] = [contents]
                for mrg in merges:
                    try:
                        oldjson['crowd_gold']['merges'][str(list(mrg))] += 1
                    except KeyError:
                        oldjson['crowd_gold']['merges'][str(list(mrg))] = 1
                with open(os.path.join(opts.jsondir, jsonfilename), 'w') as fout:
                    print >> fout, json.dumps(oldjson, indent=2, default=jdefault)
            else:
                row['Reject'] = settings['REJECT_BLACKLIST']\
                                %(WORKER_ACC_THRESHOLD,
                                batchworkers[wid]['correct'],
                                batchworkers[wid]['incorrect'])

        output_data.append(row)

    ## Approve or reject HITs as necessary
    headers = results[0].keys()
    graded = csv.writer(open(resultsfile.replace('.csv','.graded')+'.csv', 'w'))
    graded.writerow(headers)
    ac=0
    rc=0
    for row in output_data:
        graded.writerow([row[h] for h in headers])
        if row['Approve']>0:
            ac += 1
            print 'Approved count', ac
        elif row['Reject']>0:
            rc += 1
            print 'Rejected count', rc
            errcount[jsonfilename] += 1


    ## Check if any words have received enough annotations to add to crowd gold
    req_anno = settings['REDUNDANCY']
    for t in targets:
        clus_this_rnd = set([])
        with open(os.path.join(opts.jsondir, t),'rU') as fin:
            thisjson = byteify(json.load(fin))
        if correct_submissions[t] < req_anno:  # skip files that had one or more rejections
            continue
        print 'Target word', t, 'Bogus term', thisjson['bogusword'], 'Errors', errcount[t]
        newclus = nx.Graph()

        max_attempts_reached = set([])
        for word, entry in thisjson['ppset']['pp_dict'].iteritems():
            if entry['state'] != 'in_progress':
                continue
            thisjson['ppset']['pp_dict'][word]['attempts'] += 1
            added = False
            for clus, contentlist in entry['matches'].iteritems():
                if float(len(contentlist))/req_anno >= CLUSTER_AGR_THRESHOLD:
                    ## Add to crowd gold
                    added = True
                    if 'goldclass' in clus:
                        clusnum = clus.replace('goldclass','')
                        thisjson['crowd_gold']['sense_clustering'][clusnum].append(word)
                        clus_this_rnd.add(word)
                    elif clus == 'trash':
                        thisjson['trash'].append(word)
                        clus_this_rnd.add(word)
                    elif clus == 'newbox':
                        for contents in contentlist:
                            newclus.add_nodes_from(contents)
                            if contents == [word]:  # add edge between word and itself only if it's solo
                                if newclus.has_edge(word, word):
                                    newclus[word][word]['weight'] += 2
                                else:
                                    newclus.add_edge(word, word, weight=2)
                            else:
                                for w in set(contents) - {word}:
                                    if newclus.has_edge(word, w):
                                        newclus[word][w]['weight'] += 1
                                    else:
                                        newclus.add_edge(word, w, weight=1)
            if not added and entry['attempts'] >= MAX_ATTEMPTS:
                max_attempts_reached.add(word)


        ## Output connected components from newclus as new crowd gold clusters
        newG = nx.Graph([(u,v,d) for u,v,d in newclus.edges(data=True) if float(d['weight'])/(2*req_anno) >= CLUSTER_AGR_THRESHOLD])
        if opts.clustermode == 'clique':
            new_crowd_gold = {i+1: l for i,l in enumerate(list(nx.find_cliques(newG)))}
        elif opts.clustermode == 'biconnected':
            new_crowd_gold = {i+1: l for i,l in enumerate(list(nx.biconnected_components(newG)))}
        else:
            sys.stderr.write('Unknown clustermode. Please use one of [clique, biconnected].\n')
            exit(1)

        clus_this_rnd = clus_this_rnd | \
                        set([item for sublist in
                             new_crowd_gold.values()
                             for item in sublist])

        try:
            maxclusnum = max([int(n) for n in
                          thisjson['crowd_gold']['sense_clustering'].keys()])
        except ValueError:
            maxclusnum = 0
        for clusnum, wordlist in new_crowd_gold.iteritems():
            newclus = str(maxclusnum + int(clusnum))
            thisjson['crowd_gold']['sense_clustering'][newclus] = wordlist
            maxclusnum = int(newclus)


        # Merge as necessary
        if 'merges' not in thisjson['crowd_gold']: # TODO: REMOVE
            thisjson['crowd_gold']['merges'] = {}
        mx = nx.Graph()
        mx.add_nodes_from([g for g in thisjson['crowd_gold']['sense_clustering'].keys()])
        for mrg, votes in thisjson['crowd_gold']['merges'].iteritems():
            mlist = strtolist(mrg)
            for u,v in itertools.combinations(mlist,2):
                unum = u.replace('goldclass','')
                vnum = v.replace('goldclass','')
                if mx.has_edge(unum, vnum):
                    mx[unum][vnum]['weight'] += votes
                else:
                    mx.add_edge(unum, vnum, weight=votes)
        newmx = nx.Graph([(u,v,d) for u,v,d in mx.edges(data=True) if float(d['weight'])/(req_anno) >= MERGE_THRESHOLD])

        mrg = list(nx.connected_components(newmx))

        for contents in mrg:
            newcontents = list(set([item for sublist in [thisjson['crowd_gold']['sense_clustering'][n] for n in contents] for item in sublist]))
            newclusname = contents.pop()
            thisjson['crowd_gold']['sense_clustering'][newclusname] = newcontents
            while len(contents) > 0:
                thisjson['crowd_gold']['sense_clustering'].pop(contents.pop(), None)

        ## Add words that have reached MAX_ATTEMPTS to their own cluster
        try:
            maxclusnum = max([int(n) for n in
                          thisjson['crowd_gold']['sense_clustering'].keys()])
        except ValueError:
            maxclusnum = 0
        for word in max_attempts_reached:
            maxclusnum += 1
            newclus = str(maxclusnum)
            thisjson['crowd_gold']['sense_clustering'][newclus] = [word]
            clus_this_rnd.add(word)


        thisjson['crowd_gold']['cluster_count'] = len(thisjson['crowd_gold']['sense_clustering'])

        ## Reset HIT for this target and record old data
        if 'old_data' not in thisjson or len(thisjson['old_data']) == 0:
            thisjson['old_data'] = {}
        thisjson['old_data'][timestamp] = {k: deepcopy(thisjson[k]) for k in ['ppset','crowd_gold',
                                                                    'crowdstarter','unsorted',
                                                                    'bogusword','crowdstarter',
                                                                    'sorted','trash']}
        thisjson['old_data'][timestamp]['clus_this_rnd'] = clus_this_rnd

        goldwords = {w for sublist in thisjson['crowd_gold']['sense_clustering'].values() for w in sublist}
        for word in thisjson['unsorted']:
            if word in goldwords:
                state = 'crowdgold'
            elif word in thisjson['trash']:
                state = 'trash'
            else:
                state = 'attempted'
            thisjson['ppset']['pp_dict'][word]['matches'] = {}
            thisjson['ppset']['pp_dict'][word]['state'] = state
            thisjson['ppset']['pp_dict'][word]['workers'] = []

        thisjson['crowd_gold']['merges'] = {}
        thisjson['lock'] = 0
        thisjson['crowdstarter'] = {}
        thisjson['unsorted'] = []
        thisjson['bogusword'] = ''

        ## Check if we're totally finished clustering this target or done with final merge
        states = set([thisjson['ppset']['pp_dict'][w]['state'] for w in
                      thisjson['ppset']['pp_dict']])
        if thisjson['complete'] == 1:
            print 'All finished final merge for target', t
            thisjson['complete'] = 2
        elif 'in_progress' not in states and 'none' not in states and 'attempted' not in states:
            print 'All finished clustering paraphrases for target', t
            thisjson['complete'] = 1

        with open(os.path.join(opts.jsondir, t),'w') as fout:
            print >> fout, json.dumps(thisjson, indent=2, default=jdefault)
