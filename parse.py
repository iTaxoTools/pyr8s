#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parse a NEXUS file and execute rate commands.
"""

import sys
import dendropy
import core

def parse_value(tokenizer):
    token = tokenizer.require_next_token_ucase()
    if token != '=':
        raise ValueError("Expecting '=' token, but instead found '{}'".format(token))
    token = tokenizer.require_next_token_ucase()
    return token

def parse_rates(tokenizer, analysis):
    results = None
    tokenizer.skip_to_semicolon()
    token = tokenizer.next_token_ucase()
    while not (token == 'END' or token == 'ENDBLOCK') \
        and not tokenizer.is_eof() \
        and not token==None:
        if token == 'BLFORMAT':
            token = tokenizer.require_next_token_ucase()
            while not (token == ';'):
                if token == 'NSITES':
                    token = parse_value(tokenizer)
                    print('* NSITES: {0}'.format(token))
                    analysis.param.branch_length['nsites'] = int(token)
                elif token == 'LENGTHS':
                    token = parse_value(tokenizer)
                    print('* LENGTHS: {0}'.format(token))
                    if token == 'TOTAL':
                        analysis.param.branch_length['persite'] = False
                    elif token == 'PERSITE':
                        analysis.param.branch_length['persite'] = True
                    else:
                        raise ValueError("BLFORMAT.LENGTHS: Unrecognised vale: '{}'".format(token))
                elif token == 'ROUND':
                    token = parse_value(tokenizer)
                    print('* ROUND: {0}'.format(token))
                    if token == 'NO':
                        analysis.param.branch_length['round'] = False
                    elif token == 'YES':
                        analysis.param.branch_length['round'] = True
                    else:
                        raise ValueError("BLFORMAT.ROUND: Unrecognised vale: '{}'".format(token))
                else:
                    raise ValueError("BLFORMAT: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
        elif token == 'COLLAPSE':
            print('Collapse is now automatic, no need to declare it.')
            tokenizer.skip_to_semicolon()
        elif token == 'MRCA':
            ancestor = tokenizer.require_next_token()
            children = []
            token = tokenizer.require_next_token()
            while not (token == ';') \
                and not tokenizer.is_eof() \
                and not token==None:
                children.append(token)
                token = tokenizer.require_next_token()
            analysis.tree.label_mrca(ancestor, children)
            print("Named the mrca '{0}' of {1}.".format(ancestor,children))
        elif token == 'FIXAGE':
            token = tokenizer.require_next_token_ucase()
            node, age = None, None
            while not (token == ';'):
                if token == 'TAXON':
                    token = parse_value(tokenizer)
                    print('* TAXON: {0}'.format(token))
                    node = analysis.tree.find_node_with_taxon_label(token)
                elif token == 'AGE':
                    token = parse_value(tokenizer)
                    print('* AGE: {0}'.format(token))
                    age = int(token)
                else:
                    raise ValueError("FIXAGE: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            if age is not None:
                node.fix = age
            else:
                node.fix = node.age
            node.max = None
            node.min = None
        elif token == 'UNFIXAGE':
            token = tokenizer.require_next_token_ucase()
            node = None
            while not (token == ';'):
                if token == 'TAXON':
                    token = parse_value(tokenizer)
                    print('* TAXON: {0}'.format(token))
                    node = analysis.tree.find_node_with_taxon_label(token)
                else:
                    raise ValueError("UNFIXAGE: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            node.fix = None
        elif token == 'CONSTRAIN':
            token = tokenizer.require_next_token_ucase()
            node, min, max = None, None, None
            all = False
            while not (token == ';'):
                if token == 'TAXON':
                    token = parse_value(tokenizer)
                    print('* TAXON: {0}'.format(token))
                    node = analysis.tree.find_node_with_taxon_label(token)
                elif token == 'MAX_AGE' or token == 'MAXAGE':
                    token = parse_value(tokenizer)
                    print('* MAX_AGE: {0}'.format(token))
                    if token != 'NONE':
                        max = int(token)
                elif token == 'MIN_AGE' or token == 'MINAGE':
                    token = parse_value(tokenizer)
                    print('* MIN_AGE: {0}'.format(token))
                    if token != 'NONE':
                        min = int(token)
                elif token == 'REMOVE':
                    token = parse_value(tokenizer)
                    print('* REMOVE: {0}'.format(token))
                    if token != 'ALL':
                        raise ValueError("CONSTRAIN.REMOVE: Expected 'all': '{}'".format(token))
                else:
                    raise ValueError("CONSTRAIN: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            if all:
                for node in analysis.tree.preorder_node_iter():
                    node.max = None
                    node.min = None
            else:
                node.fix = None
                node.max = max
                node.min = min
        elif token == 'DIVTIME':
            token = tokenizer.require_next_token_ucase()
            while not (token == ';'):
                if token == 'METHOD':
                    token = parse_value(tokenizer)
                    print('* METHOD: {0}'.format(token))
                    if token == 'NPRS' or token == 'NP':
                        analysis.param.method = 'nprs'
                    else:
                        raise ValueError("DIVTIME: Unrecognised method: '{}'".format(token))
                elif token == 'ALGORITHM':
                    token = parse_value(tokenizer)
                    print('* ALGORITHM: {0}'.format(token))
                    if token == 'POWELL' or token == 'PL':
                        analysis.param.algorithm = 'powell'
                    else:
                        raise ValueError("DIVTIME: Unrecognised algorithm: '{}'".format(token))
                else:
                    raise ValueError("DIVTIME: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            results = analysis.run()
        elif token == 'SET':
            token = tokenizer.require_next_token_ucase()
            while not (token == ';'):
                if token == 'NUM TIME GUESSES':
                    token = parse_value(tokenizer)
                    print('* NUM_TIME_GUESSES: {0}'.format(token))
                    analysis.param.general['number_of_guesses'] = int(token)
                elif token == 'NPEXP':
                    token = parse_value(tokenizer)
                    print('* NPEXP: {0}'.format(token))
                    analysis.param.nprs['exponent'] = int(token)
                elif token == 'PENALTY':
                    token = parse_value(tokenizer)
                    print('* PENALTY: {0}'.format(token))
                    if token == 'ADD':
                        analysis.param.nprs['logarithmic'] = False
                    elif token == 'LOG':
                        analysis.param.nprs['logarithmic'] = True
                    else:
                        raise ValueError("PENALTY: Unrecognised option: '{}'".format(token))
                elif token == 'PERTURB_FACTOR':
                    token = parse_value(tokenizer)
                    print('* PERTURB_FACTOR: {0}'.format(token))
                    analysis.param.general['perturb_factor'] = float(token)
                elif token == 'MAXITER':
                    #! for minimize.powell
                    pass
                elif token == 'MAXBARRIERITER':
                    token = parse_value(tokenizer)
                    print('* MAXBARRIERITER: {0}'.format(token))
                    analysis.param.barrier['max_iterations'] = int(token)
                elif token == 'BARRIERMULTIPLIER':
                    token = parse_value(tokenizer)
                    print('* BARRIERMULTIPLIER: {0}'.format(token))
                    analysis.param.barrier['multiplier'] = float(token)
                elif token == 'INITBARRIERFACTOR':
                    token = parse_value(tokenizer)
                    print('* INITBARRIERFACTOR: {0}'.format(token))
                    analysis.param.barrier['initial_factor'] = float(token)
                else:
                    raise ValueError("SET: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
        elif token == 'SHOWAGE':
            #! print results
            print('* {}'.format(token))
            tokenizer.skip_to_semicolon()
        elif token == 'DESCRIBE':
            token = tokenizer.require_next_token_ucase()
            while not (token == ';'):
                if token == 'PLOT':
                    token = parse_value(tokenizer)
                    if token == 'CLADOGRAM':
                        print('* {}'.format(token))
                        pass
                    if token == 'PHYLOGRAM':
                        print('* {}'.format(token))
                        pass
                    if token == 'CHRONOGRAM':
                        print('* {}'.format(token))
                        pass
                    if token == 'RATOGRAM':
                        print('* {}'.format(token))
                        pass
                    if token == 'TREE_DESCRIPTION':
                        print('* {}'.format(token))
                        pass
                    if token == 'PHYLO_DESCRIPTION':
                        print('* {}'.format(token))
                        pass
                    if token == 'RATO_DESCRIPTION':
                        print('* {}'.format(token))
                        pass
                elif token == 'PLOTWIDTH':
                    print('* {}'.format(token))
                    pass
                else:
                    raise ValueError("DESCRIBE: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            # plot happens here
            pass
        elif token == ';':
            print('OOPS, missed a colon')
        else:
            raise ValueError("RATES: Unrecognised command: '{}'".format(token))
        token = tokenizer.next_token_ucase()


def parse(file):
    """First get the tree and create Analysis, then find and parse RATES commands"""
    tree = dendropy.Tree.get(path=file, schema="nexus", suppress_internal_node_taxa=False)
    tree.print_plot()
    analysis = core.Analysis(tree)
    file = open(file,'r')
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
            print('RATES BLOCK FOUND!')
            parse_rates(tokenizer, analysis)
        else:
            while not (token == 'END' or token == 'ENDBLOCK') \
                and not tokenizer.is_eof() \
                and not token==None:
                tokenizer.skip_to_semicolon()
                token = tokenizer.next_token_ucase()
    return analysis


if __name__ == '__main__':
    print('in main')

    if len(sys.argv) >=2:
        print(str(sys.argv))
        a = parse(sys.argv[1])
        if hasattr(a,'_results'):
            a._results.print()

    import timeit
    a._array.make(a.tree)
    a._array.guess()
    f=a._build_objective_nprs()
    p=a._build_barrier_penalty()
    # timeit.timeit('f(a._array.xvar)',globals=globals(),number=10000)
    # timeit.timeit('p(a._array.xvar)',globals=globals(),number=10000)
    # timeit.timeit('a.run()',globals=globals(),number=1)

    if False:
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
