#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parse a NEXUS file and execute rate commands.
Is a total mess right now.
"""

import sys
import dendropy
import core

_SEPARATOR = '-' * 50

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
            persite = None
            nsites = None
            while not (token == ';'):
                if token == 'NSITES':
                    token = parse_value(tokenizer)
                    print('* NSITES: {0}'.format(token))
                    nsites = int(token)
                elif token == 'LENGTHS':
                    token = parse_value(tokenizer)
                    print('* LENGTHS: {0}'.format(token))
                    if token == 'TOTAL':
                        persite = False
                    elif token == 'PERSITE':
                        persite = True
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
                elif token == 'ULTRAMETRIC':
                    token = parse_value(tokenizer)
                    print('* ULTRAMETRIC: {0}'.format(token))
                    if token == 'NO':
                        pass
                    elif token == 'YES':
                        raise ValueError("BLFORMAT.ULTRAMETRIC: YES is not an option")
                    else:
                        raise ValueError("BLFORMAT.ULTRAMETRIC: Unrecognised vale: '{}'".format(token))
                else:
                    raise ValueError("BLFORMAT: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            if persite is None:
                raise ValueError("BLFORMAT: Expected parameter LENGTHS not given.")
            elif persite:
                if nsites is None:
                    raise ValueError("BLFORMAT: Expected parameter NSITES not given.")
                else:
                    analysis.param.branch_length['persite'] = nsites
            elif not persite:
                analysis.param.branch_length['persite'] = None

        elif token == 'COLLAPSE':
            print('* COLLAPSE: automatic')
            tokenizer.skip_to_semicolon()
        elif token == 'PRUNE':
            print('* PRUNE: automatic')
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
            try:
                analysis.tree.label_mrca(ancestor, children)
            except KeyError:
                raise ValueError("MRCA: Invalid children: {}".format(children))
            print("* MRCA: '{0}' of {1}.".format(ancestor,children))
        elif token == 'FIXAGE':
            token = tokenizer.require_next_token_ucase()
            node, age = None, None
            print('* FIXAGE:', end=' ')
            while not (token == ';'):
                if token == 'TAXON':
                    token = parse_value(tokenizer)
                    node = analysis.tree.find_node_with_taxon(
                        lambda x: x.label.upper() == token)
                    print('TAXON={0}'.format(token), end=' ')
                elif token == 'AGE':
                    token = parse_value(tokenizer)
                    age = int(token)
                    print('AGE={0}'.format(token), end=' ')
                else:
                    raise ValueError("FIXAGE: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            if age is not None:
                node.fix = age
            else:
                node.fix = node.age
            node.max = None
            node.min = None
            print('')
        elif token == 'UNFIXAGE':
            token = tokenizer.require_next_token_ucase()
            node = None
            print('* UNFIXAGE:', end=' ')
            while not (token == ';'):
                if token == 'TAXON':
                    token = parse_value(tokenizer)
                    node = analysis.tree.find_node_with_taxon(
                        lambda x: x.label.upper() == token)
                    print('TAXON={0}'.format(token), end=' ')
                else:
                    raise ValueError("UNFIXAGE: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            node.fix = None
            print('')
        elif token == 'CONSTRAIN':
            token = tokenizer.require_next_token_ucase()
            node, min, max = None, None, None
            all = False
            print('* CONSTRAIN:', end=' ')
            while not (token == ';'):
                if token == 'TAXON':
                    token = parse_value(tokenizer)
                    node = analysis.tree.find_node_with_taxon(
                        lambda x: x.label.upper() == token)
                    print('TAXON={0}'.format(token), end=' ')
                elif token == 'MAX AGE' or token == 'MAXAGE':
                    token = parse_value(tokenizer)
                    if token != 'NONE':
                        max = int(token)
                    print('MAX_AGE={0}'.format(token), end=' ')
                elif token == 'MIN AGE' or token == 'MINAGE':
                    token = parse_value(tokenizer)
                    if token != 'NONE':
                        min = int(token)
                    print('MIN_AGE={0}'.format(token), end=' ')
                elif token == 'REMOVE':
                    token = parse_value(tokenizer)
                    print('REMOVE={0}'.format(token), end=' ')
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
            print('')
        elif token == 'DIVTIME':
            token = tokenizer.require_next_token_ucase()
            print(_SEPARATOR)
            print('* DIVTIME:', end=' ')
            while not (token == ';'):
                if token == 'METHOD':
                    token = parse_value(tokenizer)
                    if token == 'NPRS' or token == 'NP':
                        analysis.param.method = 'nprs'
                    else:
                        raise ValueError("DIVTIME: Unrecognised method: '{}'".format(token))
                    print('METHOD={0}'.format(token), end=' ')
                elif token == 'ALGORITHM':
                    token = parse_value(tokenizer)
                    if token == 'POWELL' or token == 'PL':
                        analysis.param.algorithm = 'powell'
                    else:
                        raise ValueError("DIVTIME: Unrecognised algorithm: '{}'".format(token))
                    print('ALGORITHM={0}'.format(token), end=' ')
                else:
                    raise ValueError("DIVTIME: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            print('\n* BEGIN ANALYSIS: \n')
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
            tokenizer.skip_to_semicolon()
            print('* SHOWAGE:')
            if results is not None:
                results.print()
            else:
                raise ValueError("SHOWAGE: Called before DIVTIME, nothing to show.")
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
                        print('* {} (unweighted branches):'.format(token))
                        core.print_tree(results.chronogram)
                    if token == 'RATOGRAM':
                        print('* {}'.format(token))
                        pass
                    if token == 'TREE DESCRIPTION':
                        print('* {}:'.format(token))
                        print(results.chronogram.as_string(
                            schema="newick",suppress_internal_node_labels=True))
                    if token == 'PHYLO DESCRIPTION':
                        print('* {}'.format(token))
                        pass
                    if token == 'RATO DESCRIPTION':
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
    """First get the tree and create RateAnalysis, then find and parse RATES commands"""
    tree = dendropy.Tree.get(path=file, schema="nexus", suppress_internal_node_taxa=False)
    print("> TREE: from '{}'".format(file))
    tree.print_plot()
    analysis = core.RateAnalysis(tree)
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
        if token == 'RATES' or token=='R8S':
            print('> RATES BLOCK:')
            print(_SEPARATOR)
            parse_rates(tokenizer, analysis)
        else:
            while not (token == 'END' or token == 'ENDBLOCK') \
                and not tokenizer.is_eof() \
                and not token==None:
                tokenizer.skip_to_semicolon()
                token = tokenizer.next_token_ucase()
    return analysis


if __name__ == '__main__':
    print(' ')

    if len(sys.argv) >=2:
        a = parse(sys.argv[1])

    # import timeit
    # a._array.make(a.tree)
    # a._array.guess()
    # f=a._build_objective_nprs()
    # g=a._build_gradient_nprs()
    # p=a._build_barrier_penalty()
    # timeit.timeit('f(a._array.variable)',globals=globals(),number=10000)
    # timeit.timeit('p(a._array.variable)',globals=globals(),number=10000)
    # timeit.timeit('a.run()',globals=globals(),number=1)
