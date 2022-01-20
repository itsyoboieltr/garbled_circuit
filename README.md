# garbled_circuit

I implemented Yao’s protocol for two parties with AES using the [GitHub repository](https://github.com/ojroques/garbled-circuit) provided for the task, and a circuit I designed to add values. The program is mainly about two parties, Alice and Bob, who want to execute a function without disclosing any private information (which is usually their input, that can be a lot of things, basically anything sensitive, for example: their salary). Consequently, in an ideal secure multi-party computation scenario, the parties will not get to know each other’s inputs, however, each of them will learn the result of the function executed (based on their inputs) in the end. In my implementation, Alice is the garbler, the party who creates the circuit and sends it to Bob, while Bob is the evaluator, the party who evaluates the circuit and sends the results back to Alice. 

# How to run?

1. Clone this repository

2. Install dependencies (the code was written and tested on Python 3.10.0): 

```
pip3 install --user pyzmq cryptography sympy
```

3. Open two terminal windows in the root folder of the repository

4. First terminal window will be the garbler, that creates the circuit and sends it to the evaluator:

```
python main.py alice
```

5. Second terminal window will be the evaluator, that evaluates the circuit and sends the results back to the garbler:

```
python main.py bob
```

6. After it finished, verify the results in a non-MPC way, to make sure it is correct

```
python main.py verify
```

All the output, such as the data sent between the parties and the individual results for the parties are saved to the output folder in .json format.

If you want to change the input to the function, you have to change the constants 'ALICE_INPUT' and 'BOB_INPUT' in main.py lines 5-6.

Make sure that the sum of each input array is 15 or less, because the implementation uses a 4 bit adder, which will not give accurate results on integers higher than 4 bits.
