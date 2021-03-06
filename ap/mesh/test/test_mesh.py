#! /usr/bin/env python
import os
import sys
from functools import reduce
import numpy as np
import numpy.testing as npt
import ap.mesh.parsers as parsers
import ap.mesh.meshtools as meshtools
import ap.mesh.meshes as meshes

class TestMeshParser(object):
    def __init__(self, nodes, elements, edges, mesh_files):
        """
        Test case for a parsed mesh. Tries to test an Argyris mesh.
        """
        for mesh_file in mesh_files:
            self.nodes = nodes
            self.elements = elements
            self.edges = edges
            parsed_mesh = parsers.parser_factory(*mesh_file)

            npt.assert_almost_equal(self.nodes, parsed_mesh.nodes)
            npt.assert_equal(self.elements, parsed_mesh.elements)
            if parsed_mesh.edges:
                assert np.all(self.edges == parsed_mesh.edges)

            npt.assert_almost_equal(meshtools.project_nodes(lambda x : x[0:2],
                                                     self.elements, self.nodes),
                             self.nodes[:, 0:2], decimal=10)

            if parsed_mesh.edges:
                assert set(map(lambda x : x[0:-1], self.edges)) == \
                       set(map(lambda x : x[0:-1],
                           meshtools.extract_boundary_edges(self.elements)))

            # Test Argyris stuff.
            if self.elements.shape[1] == 6:
                TestArgyrisCase(mesh_file, parsed_mesh)

class TestLagrangeMesh(object):
    def __init__(self, nodes, elements, edges, mesh_files):
        """
        Test case for a Lagrange mesh. Tries to test an Argyris mesh.
        """
        for mesh_file in mesh_files:
            self.nodes = nodes
            # The mesh classes try to flatten nodes if possible. Do it here too.
            if np.all(self.nodes[:, -1] == self.nodes[0, -1]):
                self.nodes = self.nodes[:,0:-1]
            self.elements = elements
            self.edges = edges
            mesh = meshes.mesh_factory(*mesh_file)
            parsed_mesh = parsers.parser_factory(*mesh_file)

            npt.assert_equal(self.nodes, mesh.nodes)
            npt.assert_equal(self.elements, mesh.elements)
            if parsed_mesh.edges:
                assert set(self.edges) == reduce(lambda a, b : a + b,
                                                 mesh.edge_collections.values())

            npt.assert_almost_equal(meshtools.project_nodes(lambda x : x[0:2],
                                                     self.elements, self.nodes),
                             self.nodes[:,0:2], decimal=10)

            if parsed_mesh.edges:
                assert set(map(lambda x : x[0:-1], self.edges)) == \
                       set(map(lambda x : x[0:-1],
                           meshtools.extract_boundary_edges(self.elements)))

            # Test Argyris stuff.
            if self.elements.shape[1] == 6:
                TestArgyrisCase(mesh_file, parsed_mesh)

class TestArgyrisCase(object):
    """
    Test case for an Argyris mesh.
    """
    def __init__(self, mesh_file, parsed_mesh):
        argyris_mesh = meshes.mesh_factory(*mesh_file, argyris=True)
        lagrange_mesh = meshes.mesh_factory(*mesh_file)
        assert argyris_mesh.elements.shape == (parsed_mesh.elements.shape[0],21)

        stacked_nodes = dict()
        edges_by_midpoint = dict()
        for element in argyris_mesh.elements:
            for local_number, global_number in enumerate(element[0:3]):
                corner_nodes = (element[3 + 2*local_number],
                                element[3 + 2*local_number + 1],
                                element[9 + 3*local_number],
                                element[9 + 3*local_number + 1],
                                element[9 + 3*local_number + 2])
                if stacked_nodes.has_key(global_number):
                    assert corner_nodes == stacked_nodes[global_number]
                else:
                    stacked_nodes[global_number] = corner_nodes
                for node in corner_nodes:
                    npt.assert_almost_equal(
                            argyris_mesh.nodes[global_number - 1, :],
                            argyris_mesh.nodes[node - 1, :])

            for midpoint_number, local_edge in enumerate([[0,1], [0,2], [1,2]]):
                midpoint = element[18 + midpoint_number]
                if edges_by_midpoint.has_key(midpoint):
                    npt.assert_equal(edges_by_midpoint[midpoint],
                                     element[local_edge])
                else:
                    edges_by_midpoint[midpoint] = element[local_edge]

        # Ensure that the Argyris mesh and the Lagrange mesh come up with the
        # same edges.
        for name, collection in lagrange_mesh.edge_collections.items():
            argyris_collection = \
                map(lambda x : x.edge,
                    filter(lambda x : x.name == name,
                           argyris_mesh.node_collections)[0].edges)
            for edge in collection:
                argyris_edge = (min(edge[0:2]), max(edge[0:2]), edge[2])
                assert argyris_edge in argyris_collection

# The tests rely on parsing several files. Change the directory and then change
# back.
original_directory = os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
try:
    TestMeshParser(np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0.5,0.5,0]]),
                   np.array([[1,2,5],[2,3,5],[3,4,5],[4,1,5]]),
                   [(1,2,1),(2,3,2),(3,4,3),(4,1,4)],
                   [["linears1.mesh"], ["linears1_nodes.txt",
                                        "linears1_elements.txt"],
                    ["linears1_elements.txt", "linears1_nodes.txt"]])

    # case for extra nodes
    TestLagrangeMesh(np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0.5,0.5,0]]),
                   np.array([[1,2,5],[2,3,5],[3,4,5],[4,1,5]]),
                   [(1,2,1),(2,3,2),(3,4,3),(4,1,4)],
                   [["linears1_shifted.mesh"], ["linears1_nodes_shifted.txt",
                                        "linears1_elements_shifted.txt"],
                    ["linears1_elements_shifted.txt", "linears1_nodes_shifted.txt"]])

    TestMeshParser(np.array([[0.000000, 0.000000], [0.000000, 0.000000],
     [0.500000, 0.000000], [0.500000, 0.000000], [0.000000, 0.000000],
     [1.000000, 0.000000], [0.500000, 0.500000], [0.000000, 1.000000],
     [0.000000, 0.000000], [0.000000, 1.500000], [0.000000, 0.500000],
     [1.000000, 0.000000], [1.000000, 0.500000], [0.000000, 1.500000],
     [0.000000, 0.000000], [0.000000, 4.000000], [0.000000, 2.000000],
     [4.000000, 0.000000], [1.500000, 4.000000], [0.000000, 1.000000],
     [4.000000, 0.000000], [0.500000, 4.000000], [0.000000, 0.000000],
     [3.500000, 0.000000], [0.000000, 3.000000], [0.000000, 0.000000],
     [2.500000, 0.000000], [0.000000, 2.000000], [0.000000, 0.500000],
     [1.500000, 0.000000], [1.000000, 1.000000], [0.000000, 1.500000],
     [0.500000, 0.000000], [2.000000, 0.000000], [0.000000, 0.500000],
     [3.500000, 0.000000], [2.000000, 3.500000], [0.000000, 1.500000],
     [3.500000, 0.000000], [1.000000, 3.500000], [0.000000, 0.500000],
     [3.000000, 0.000000], [0.500000, 2.500000], [0.000000, 0.500000],
     [2.000000, 0.000000], [1.000000, 1.500000], [0.000000, 1.500000],
     [1.000000, 0.000000], [2.000000, 0.500000], [0.000000, 2.500000],
     [0.000000, 0.000000], [1.000000, 3.000000], [0.000000, 2.000000],
     [3.000000, 0.000000], [1.500000, 3.000000], [0.000000, 1.000000],
     [2.500000, 0.000000], [1.000000, 2.000000], [0.000000, 1.500000],
     [1.500000, 0.000000], [2.000000, 1.000000], [0.000000, 2.500000],
     [0.500000, 0.000000], [3.000000, 0.000000], [0.000000, 1.500000]]),
     np.array([[1, 3, 2], [6, 5, 3], [4, 2, 5], [3, 5, 2], [23, 22, 10], [21, 9, 22],
     [6, 10, 9], [22, 9, 10], [19, 7, 20], [4, 8, 7], [21, 20, 8], [7, 8, 20],
     [6, 9, 5], [21, 8, 9], [4, 5, 8], [9, 8, 5], [52, 46, 48], [39, 40, 46],
     [41, 48, 40], [46, 40, 48], [19, 20, 30], [21, 31, 20], [39, 30, 31],
     [20, 31, 30], [23, 33, 22], [41, 32, 33], [21, 22, 32], [33, 32, 22],
     [39, 31, 40], [21, 32, 31], [41, 40, 32], [31, 32, 40], [23, 34, 33],
     [43, 42, 34], [41, 33, 42], [34, 42, 33], [51, 53, 47], [55, 50, 53],
     [43, 47, 50], [53, 50, 47], [52, 48, 54], [41, 49, 48], [55, 54, 49],
     [48, 49, 54], [43, 50, 42], [55, 49, 50], [41, 42, 49], [50, 49, 42],
     [65, 64, 63], [61, 62, 64], [60, 63, 62], [64, 62, 63], [52, 54, 57],
     [55, 59, 54], [61, 57, 59], [54, 59, 57], [51, 56, 53], [60, 58, 56],
     [55, 53, 58], [56, 58, 53], [61, 59, 62], [55, 58, 59], [60, 62, 58],
     [59, 58, 62], [19, 30, 18], [39, 29, 30], [17, 18, 29], [30, 29, 18],
     [52, 44, 46], [35, 38, 44], [39, 46, 38], [44, 38, 46], [11, 16, 24],
     [17, 28, 16], [35, 24, 28], [16, 28, 24], [39, 38, 29], [35, 28, 38],
     [17, 29, 28], [38, 28, 29], [12, 13, 25], [14, 26, 13], [36, 25, 26],
     [13, 26, 25], [11, 24, 15], [35, 27, 24], [14, 15, 27], [24, 27, 15],
     [52, 45, 44], [36, 37, 45], [35, 44, 37], [45, 37, 44], [14, 27, 26],
     [35, 37, 27], [36, 26, 37], [27, 37, 26]]), [], [["ell.mesh"]])

    TestMeshParser(np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
    [0.3333333333325, 0, 0], [0.66666666666579, 0, 0], [0.16666666666633, 0, 0],
    [0.49999999999868, 0, 0], [0.83333333333289, 0, 0], [1, 0.3333333333325, 0],
    [1, 0.66666666666579, 0], [1, 0.16666666666633, 0], [1, 0.49999999999868, 0],
    [1, 0.83333333333289, 0], [0.66666666666759, 1, 0], [0.33333333333472, 1, 0],
    [0.83333333333364, 1, 0], [0.50000000000141, 1, 0], [0.16666666666736, 1, 0],
    [0, 0.66666666666759, 0], [0, 0.33333333333472, 0], [0, 0.83333333333364, 0],
    [0, 0.50000000000141, 0], [0, 0.16666666666736, 0],
    [0.50000000000007, 0.49999999999997, 0], [0.29166666666684, 0.70833333333344, 0],
    [0.29166666666653, 0.2916666666668, 0], [0.70833333333346, 0.70833333333324, 0],
    [0.70833333333328, 0.29166666666651, 0], [0.49999999999982, 0.17261904761947, 0],
    [0.17261904761972, 0.50000000000021, 0], [0.82738095238055, 0.49999999999982, 0],
    [0.50000000000021, 0.8273809523803, 0], [0.14583333333342, 0.85416666666672, 0],
    [0.31250000000078, 0.85416666666672, 0], [0.14583333333326, 0.1458333333334, 0],
    [0.14583333333326, 0.31250000000076, 0], [0.14583333333342, 0.68750000000052, 0],
    [0.31249999999951, 0.1458333333334, 0], [0.68750000000053, 0.85416666666662, 0],
    [0.85416666666673, 0.85416666666662, 0], [0.85416666666673, 0.68749999999951, 0],
    [0.85416666666664, 0.31249999999951, 0], [0.85416666666664, 0.14583333333326, 0],
    [0.68749999999953, 0.14583333333326, 0], [0.39583333333317, 0.23214285714314, 0],
    [0.49999999999994, 0.33630952380972, 0], [0.3958333333333, 0.39583333333339, 0],
    [0.23214285714328, 0.60416666666683, 0], [0.33630952380989, 0.50000000000009, 0],
    [0.39583333333346, 0.60416666666671, 0], [0.23214285714312, 0.39583333333351, 0],
    [0.50000000000014, 0.66369047619013, 0], [0.39583333333353, 0.76785714285687, 0],
    [0.60416666666667, 0.39583333333324, 0], [0.60416666666655, 0.23214285714299, 0],
    [0.66369047619031, 0.49999999999989, 0], [0.767857142857, 0.60416666666653, 0],
    [0.60416666666676, 0.6041666666666, 0], [0.76785714285691, 0.39583333333317, 0],
    [0.60416666666684, 0.76785714285677, 0], [0.5833333333328, 0.086309523809735, 0],
    [0.41666666666616, 0.086309523809735, 0], [0.91369047619027, 0.5833333333328, 0],
    [0.91369047619027, 0.41666666666616, 0], [0.086309523809858, 0.41666666666747, 0],
    [0.086309523809858, 0.5833333333339, 0], [0.41666666666747, 0.91369047619015, 0],
    [0.5833333333339, 0.91369047619015, 0]]),
    np.array([[16, 4, 26, 19, 34, 35],
     [1, 27, 21, 36, 37, 24],
     [4, 20, 26, 22, 38, 34],
     [1, 5, 27, 7, 39, 36],
     [3, 15, 28, 17, 40, 41],
     [3, 28, 11, 41, 42, 14],
     [10, 29, 2, 43, 44, 12],
     [2, 29, 6, 44, 45, 9],
     [27, 30, 25, 46, 47, 48],
     [26, 31, 25, 49, 50, 51],
     [27, 25, 31, 48, 50, 52],
     [26, 25, 33, 51, 53, 54],
     [29, 25, 30, 55, 47, 56],
     [25, 32, 28, 57, 58, 59],
     [29, 32, 25, 60, 57, 55],
     [25, 28, 33, 59, 61, 53],
     [5, 6, 30, 8, 62, 63],
     [10, 11, 32, 13, 64, 65],
     [20, 21, 31, 23, 66, 67],
     [16, 33, 15, 68, 69, 18],
     [26, 20, 31, 38, 67, 49],
     [15, 33, 28, 69, 61, 40],
     [5, 30, 27, 63, 46, 39],
     [10, 32, 29, 65, 60, 43],
     [27, 31, 21, 52, 66, 37],
     [16, 26, 33, 35, 54, 68],
     [6, 29, 30, 45, 56, 62],
     [11, 28, 32, 42, 58, 64]]),
   [(1, 5, 7, 1),
    (5, 6, 8, 1),
    (6, 2, 9, 1),
    (2, 10, 12, 2),
    (10, 11, 13, 2),
    (11, 3, 14, 2),
    (3, 15, 17, 3),
    (15, 16, 18, 3),
    (16, 4, 19, 3),
    (4, 20, 22, 4),
    (20, 21, 23, 4),
    (21, 1, 24, 4)],
     [["unitsquare.mesh"], ["unitsquare.msh"]])
finally:
    os.chdir(original_directory)
