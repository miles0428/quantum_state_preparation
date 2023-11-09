'''
This file is used to generate a quantum circuit from a gene

author : Yu-Cheng Chung
email  : ycchung@ntnu.edu.tw
date   : 2023 12 oct

dependencies:
    qiskit
    numpy
    
'''

import qiskit as qk
import numpy as np


class Gene_Circuit(object):
    '''
    Gene Circuit

    Methods:
        generate_circuit_from_gene: generate a quantum circuit with num_qubit qubits
        circuit_0 ~ circuit_10: quantum circuit connect with gene

    '''
    def __init__(self,gene,num_qubit) -> None:
        '''
        Args:
            gene: a array with shape (num_qubit, length_gene) with element called G_ij
            num_qubit: number of qubits
        
        object:
            self.gene: a array with shape (num_qubit, length_gene) with element called G_ij
            self.num_qubit: number of qubits
            self.circuit: a quantum circuit with num_qubit qubits generated from gene
            self.draw: draw the circuit
        '''
        self.gene = gene
        self.num_qubit = num_qubit
        self.circuit = qk.transpile(self.generate_circuit_from_gene())
        self.draw = self.circuit.draw
        self.num_parameters = self.circuit.num_parameters
        self.depth = self.circuit.depth

    def bind_parameters(self, theta : list|np.ndarray) -> qk.QuantumCircuit:
        '''
        bind parameter to the circuit
        Args:
            theta: a list of theta
        Returns:
            bind_circuit: a quantum circuit with parameter binded
        '''
        binded_circuit = self.circuit.bind_parameters({self.circuit.parameters[i]:theta[i] for i in range(len(theta))})
        return binded_circuit

    def generate_circuit_from_gene(self)->qk.QuantumCircuit:
        '''
        Generate a quantum circuit with num_qubit qubits
        Args:
            self.gene: a array with shape (num_qubit, length_gene) with element called G_ij
            self.num_qubit: number of qubits
        Returns:
            circuit: a quantum circuit

        The circuit is generated by the following rule:
        ------------------------------------------------
        | G_00 | G_01 | G_02 | G_03 | G_04 | ...| G_0m |
        ------------------------------------------------
        | G_10 | G_11 | G_12 | G_13 | G_14 | ...| G_1m |
        ------------------------------------------------
        ...
        ------------------------------------------------
        | G_n0 | G_n1 | G_n2 | G_n3 | G_n4 | ...| G_nm |
        ------------------------------------------------

        G_ij is the j-th gate of the i-th qubit
        G_ij will look like tuple(gate,cotrol)
        gate is the index of the gate in gene_gates
        control is the index of the control qubit
        (if the gate have no control, will ignore the control value)

        '''
        
        #gene_gates is a list of gates use to generate the circuit
        gene_gates = ['empty','rz','cx','h','x','sx']
        theta_index = 0
        circuit = qk.QuantumCircuit(self.num_qubit)
        gene = self.gene
        gene = gene.transpose(1,0,2)
        for G_nj in gene:
            for i,G_ij in enumerate(G_nj):
                gate = gene_gates[G_ij[0]]
                control = G_ij[1]
                if control >= self.num_qubit:
                    control = control % self.num_qubit
                if gate == 'empty':
                    continue
                elif gate in ['rx','ry','rz']:
                    getattr(circuit,gate)(qk.circuit.Parameter(f'theta_{theta_index}'),i)
                    theta_index+=1
                elif gate == 'cx':
                    if control == i:
                        continue
                    else:
                        circuit.cx(control,i)
                elif gate in ['h','x','sx']:
                    getattr(circuit,gate)(i)

        return circuit
    
if __name__ == '__main__':
    '''
    test gene:

        [[[0,5],[4,0],[1,3],[2,4]],
         [[0,0],[0,0],[0,0],[0,0]],
         [[4,1],[0,0],[4,0],[4,3]],
         [[5,2],[0,0],[4,3],[4,4]]]

    the circuit would look like:

         ┌─────────────┐     ┌─────────────┐     
    q_0: ┤ Rx(theta_0) ├──■──┤ Ry(theta_1) ├──■──
         └─────────────┘  │  └─────────────┘  │  
    q_1: ───────■─────────┼───────────────────┼──
              ┌─┴─┐     ┌─┴─┐     ┌───┐       │  
    q_2: ─────┤ X ├─────┤ X ├─────┤ X ├───────┼──
              ├───┤     └───┘     └─┬─┘     ┌─┴─┐
    q_3: ─────┤ H ├─────────────────■───────┤ X ├
              └───┘                         └───┘
    '''
    gene = np.array([[[0,5],[4,0],[1,3],[2,4]],
                     [[0,0],[0,0],[0,0],[0,0]],
                     [[4,1],[0,0],[4,0],[4,3]],
                     [[5,2],[0,0],[4,3],[4,4]]])
    num_qubit = 4
    gene_circuit = Gene_Circuit(gene,num_qubit)
    print(gene)
    print(gene_circuit.draw())
    print(gene_circuit.num_parameters)
    print(gene_circuit.depth())