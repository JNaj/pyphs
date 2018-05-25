#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fry May 25 15:23:49 2018

@author: Najnudel
"""
import warnings
from ..core.core import Core
from ..dictionary import electronics


def get_key(dic, value):
    for k, v in dic.items():
            if v == value:
                return k


def isStorageLinear(edge):
    _, _, dic = edge
    return (dic['type'] == 'storage')


def initialize_Leq():
    Leq = 0
    label = 'Leq_'
    keys = []
    nodeslist = []
    return Leq, label, keys, nodeslist


def replace_Ceq(graph, keys, nodes, Ceq, label):
    """
        Replace all parallel capacitors within a parallel graph with 
        equivalent capacitor

        Parameters
        ---------

        graph : Graph
            Graph object to be modified

        keys : list
            list of edges keys to be removed
        
        nodes : tuple
            tuple of edges nodes to be removed
            
        Ceq : sp.Symbol
            value of the equivalent Capacitor
        
        label : str
            label of the equivalent Capacitor
        """
    for key in keys:
        graph.remove_edge(*nodes, key)
    C = {'C' : Ceq}
    C_eq = electronics.Capacitor(label, nodes, **C)
    graph += C_eq
    warnings.warn('Replacing parallel capacitors with equivalent capacitor ' + label)
    

def replace_Leq(graph, keys, nodeslist, Leq, label, firstnode, lastnode):
    """
        Replace all serial inductors within a serial graph with 
        equivalent inductor

        Parameters
        ---------

        graph : Graph
            Graph object to be modified
            
        keys : list
            list of edges keys to be removed
            
        nodeslist : list
            list of edges nodes to be removed

        Leq : sp.Symbol
            value of the equivalent Inductor
        
        label : str
            label of the equivalent Inductor
            
        firstnode : str
            first node of the equivalent Inductor
            
        lastnode : str
            last node of the equivalent Inductor
        """
    for key, nodes in zip(keys, nodeslist):
        graph.remove_edge(*nodes, key) 
    L = {'L' : Leq}
    L_eq = electronics.Inductor(label, (firstnode, lastnode), **L)
    graph += L_eq
    warnings.warn('Replacing serial inductors with equivalent inductor ' + label)
    

def graph_analysis_serial(graph):
    """
        Walk through a serial graph and perform replace_Leq wherever possible
    """
    edges = graph.edgeslist
    Leq, label, keys, nodeslist = initialize_Leq()
    nodesbin = []
    for edge in edges:
        node1, node2, dic = edge
        nodes = node1, node2
        data = graph.get_edge_data(*nodes)
        key = get_key(data, dic)
        if isStorageLinear(edge) and dic['ctrl'] == 'e':
            keys.append(key)
            nodeslist.append(nodes)
            Leq += Core.symbols(str(dic['label']).replace('x', ''))
            label += str(dic['label'])
            if len(keys) == 1:
                firstnode = node1
            else:
                nodesbin.append(node1)
            lastnode = node2
            if edges.index(edge) == len(edges)-1 and len(keys) > 1:
                replace_Leq(graph, keys, nodeslist, Leq, label, firstnode, lastnode)
                Leq, label, keys, nodeslist = initialize_Leq()
        elif len(keys) > 1:
                replace_Leq(graph, keys, nodeslist, Leq, label, firstnode, lastnode)
                Leq, label, keys, nodeslist = initialize_Leq()
        else:
            Leq, label, keys, nodeslist = initialize_Leq()
    graph.remove_nodes_from(nodesbin)
    

def graph_analysis_parallel(graph):
    """
        Walk through a parallel graph and perform replace_Ceq wherever possible
    """
    edges = graph.edgeslist
    Ceq = 0
    label = 'Ceq_'
    keys = []
    nodes = edges[0][0], edges[0][1]
    for edge in edges:
        _, _, dic = edge
        data = graph.get_edge_data(*nodes)
        key = get_key(data, dic)
        if isStorageLinear(edge) and dic['ctrl'] == 'f':
            keys.append(key)
            Ceq += Core.symbols(str(dic['label']).replace('x', ''))
            label += str(dic['label'])
    if len(keys) > 1:
        replace_Ceq(graph, keys, nodes, Ceq, label)
        

def graph_eq(splitgraph):
    """
        Walk through a split graph (call Graph.split_sp method first) and perform
        replace_Ceq and replace_Leq wherever possible
    """
    edges = splitgraph.edgeslist
    for edge in edges:
        if edge[2]['type'] == 'graph':
            subgraph = edge[2]['graph']
            subgraph = graph_eq(subgraph)
    if edges[0][0] == edges[1][0]:
        graph_analysis_parallel(splitgraph)
    else:
        graph_analysis_serial(splitgraph)