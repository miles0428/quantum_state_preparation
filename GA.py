'''
This file is used to implement the genetic algorithm on the quantum circuit for preparing the target statevector

author : Yu-Cheng Chung
email  : ycchung@ntnu.edu.tw
date   : 2023 08 Sep

dependencies:

    gene.py
    qiskit
    numpy
    multiprocessing
    qiskit_algorithms


'''
import qiskit as qk
import numpy as np
import multiprocessing as mp
from qiskit_algorithms import optimizers
import os
from gene import Gene_Circuit

def get_prob_distribution(circuit : qk.QuantumCircuit, theta : list|np.ndarray) -> np.ndarray:
    '''
    Get the probability distribution of a circuit
    Args:
        circuit: a quantum circuit
        theta: a list of theta
    Returns:
        prob_distribution: the probability distribution of the circuit
    '''
    circuit = circuit.bind_parameters({circuit.parameters[i]:theta[i] for i in range(len(theta))})
    circuit.measure_all()
    backend = qk.Aer.get_backend('qasm_simulator')
    job = qk.execute(circuit, backend, shots=1000)
    result = job.result()
    counts = result.get_counts()
    prob_distribution = np.zeros(2**num_qubit)
    for key in counts.keys():
        prob_distribution[int(key, 2)] = counts[key]/1000
    return prob_distribution

#define the fidelity function
def get_fidelity(statevector : np.ndarray, target_statevector : np.ndarray) -> float:
    '''
    Get the fidelity of a statevector
    Args:
        statevector: the statevector of the circuit
        target_statevector: the target statevector
    Returns:
        fidelity: the fidelity of the statevector
    '''
    fidelity = np.abs(np.dot(np.conj(np.array(statevector)), target_statevector))**2
    return fidelity

def statevector(Gene : Gene_Circuit, theta : np.ndarray, backend : qk.providers.backend) -> np.ndarray:
    '''
    Get the statevector of a circuit
    Args:
        Gene : Gene_Circuit
        theta: a list of theta
        backend: the backend of the circuit
    Returns:
        statevector: the statevector of the circuit
    '''
    circuit = Gene.bind_parameters(theta)
    job = qk.execute(circuit, backend)
    result = job.result()
    statevector = result.get_statevector()
    return statevector

def get_optimized_fidelity(Gene : Gene_Circuit, target_statevector:np.ndarray) -> (float, int, np.ndarray):
    '''
    Get the optimized fidelity of a gene
    Args:
        Gene: Gene_Circuit
        num_qubit: number of qubits
    Returns:
        fidelity: the optimized fidelity of the gene
        depth: the depth of the circuit
        theta: the optimized theta
    '''
    backend = qk.Aer.get_backend('statevector_simulator')
    num_parameters = Gene.num_parameters
    theta = np.random.rand(num_parameters)
    #define the loss function
    def loss(theta):
        fidelity = get_fidelity(statevector(Gene, theta, backend), target_statevector)
        loss = -fidelity
        return loss
    
    theta = optimizer.minimize(loss, x0=theta)
    #get the optimized probability distribution
    fidelity=get_fidelity(statevector(Gene, theta.x, backend), target_statevector)
    depth=Gene.depth()
    return fidelity,depth,theta.x

def get_fidelity_depth(gene : list) -> (float, int, np.ndarray):
    '''
    this function is used to get the fidelity and depth of a gene
    Args:
        gene: a list of 0-10
    Returns:
        fidelity: the fidelity of the gene
        depth: the depth of the circuit
        theta: the optimized theta
    '''
    Gene = Gene_Circuit(gene, num_qubit)
    # print(gene)
    fidelity,depth,theta = get_optimized_fidelity(Gene, target_statevector)
    # print(theta)
    # print(statevector(Gene, theta, qk.Aer.get_backend('statevector_simulator')), target_statevector)
    # print(fidelity)
    return fidelity,depth,theta

num_genes = 20
length_gene = 10
random_gene = np.random.randint(0,11,num_genes*length_gene).reshape(num_genes,length_gene)
mutation_rate = 0.1
#calculate the fidelity and depth for each gene
#use multiprocessing to speed up
path = 'data'
expriement = 'test'
os.makedirs(f'{path}/{expriement}',exist_ok=True)
optimizer = optimizers.SPSA(maxiter=1000)
num_qubit = 3
target_statevector = np.array([0.7, 0.7,0,0,0,0,0,0])
iter = 30
if __name__ == '__main__':
    for i in range(iter):
        #use multiprocessing to speed up
        pool = mp.Pool(mp.cpu_count())
        result = pool.map(get_fidelity_depth, random_gene)
        #mkdir 1st_generation
        result=np.array(result,dtype=object)
        pool.close()
        os.makedirs(f'{path}/{expriement}/{i}st_generation',exist_ok=True)
        #save the result
        np.save(f'{path}/{expriement}/{i}st_generation/result.npy', result)
        #save the random gene
        np.save(f'{path}/{expriement}/{i}st_generation/random_gene.npy', random_gene)

        #load the result
        result = np.load(f'{path}/{expriement}/{i}st_generation/result.npy', allow_pickle=True)

        ii = 0
        while (True and ii<100):
            # find the gene with the fidelity larger than 0.99
            gene = result[:,0]>0.99 - 0.01*ii
            ii += 1
            if np.sum(gene)>=6:
                break

        index=np.array([]).astype(int)
        #get the index of 10 genes with the smallest depth and fidelity larger than 0.99

        for j in np.argsort(result[:,1]):
            if gene[j]:
                index=np.append(index,j)
                if len(index)==10:
                    break

        print(f'depth:{result[index,1]}')
        print(f'fidelity:{result[index,0]}')
        #save the 10 genes
        np.save(f'{path}/{expriement}/{i}st_generation/10_smallest_depth_gene.npy', random_gene[index])
        np.save(f'{path}/{expriement}/{i}st_generation/10_smallest_depth_result.npy', result[index])
        
        parent_gene = random_gene[index]
        #use parent gene to generate child gene
        child_gene = np.zeros((num_genes,length_gene)).astype(int)
        for j in range(num_genes):
            #randomly choose a parent gene
            parent = [np.random.randint(0,len(index)), np.random.randint(0,len(index))]
            while parent[0]==parent[1]:
                parent[1]=np.random.randint(0,len(index))
            #randomly choose a crossover point
            crossover_point = np.random.randint(1,length_gene-1)
            #generate child gene
            child_gene[j] = np.concatenate((parent_gene[parent[0]][:crossover_point], parent_gene[parent[1]][crossover_point:]))
            #randomly mutate the child gene
            for k in range(length_gene):
                if np.random.rand()<mutation_rate:
                    child_gene[j][k]=np.random.randint(0,11)
        
        #randomly generate 10 genes
        child_gene[num_genes-int(num_genes/10):] = np.random.randint(0,11,int(num_genes/10)*length_gene).reshape(int(num_genes/10),length_gene)
        #add the 10 genes with the smallest depth
        child_gene[num_genes-int(num_genes/10)-len(index):num_genes-int(num_genes/10)] = random_gene[index]
        random_gene = child_gene.astype(int)

