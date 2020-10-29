#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parse a NEXUS file and execute rate commands.
"""
import dendropy
import core

if __name__ == '__main__':
    print('in main')

    # Somehow get tree
    s = "(A:10,(B:9,(C:8,(D:7,E:6))H):4)V:3;"
    s = "(A:10,(B:9,(C:8,(D:7,:6))H):4):3;"
    # Force internal nodes as taxa, would have been labels otherwise
    t = dendropy.Tree.get_from_string(s, "newick", suppress_internal_node_taxa=False)
    t.is_rooted = True
    t.seed_node.max = 510
    t.seed_node.min = 490
    t.nodes()[2].min = 90
    t.nodes()[2].max = 400
    t.nodes()[5].fix = 200

    # This is how to use Analysis
    a = core.Analysis(t)
    a.param.branch_length['persite'] = True
    a.param.branch_length['nsites'] = 100
    res = a.run()
    print(res)

    file = open('../SAMPLE_SIMPLE','r')
    tokenizer = dendropy.dataio.nexusprocessing.NexusTokenizer(file)
    token = tokenizer.next_token_ucase()
    if not token == '#NEXUS':
        raise ValueError('Not nexus file!')

    while not tokenizer.is_eof():
        token = tokenizer.next_token_ucase()
        while token != None and token != 'BEGIN' and not tokenizer.is_eof():
            token = tokenizer.next_token_ucase()
        token = tokenizer.next_token_ucase()
        if token == 'RATES':
            print('RATES FOUND!')
        else:
            while not (token == 'END' or token == 'ENDBLOCK') \
                and not tokenizer.is_eof() \
                and not token==None:
                tokenizer.skip_to_semicolon()
                token = tokenizer.next_token_ucase()
