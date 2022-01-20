# garbled_circuit

How to run?

1. Clone this repository

2. Install dependencies: 

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

If you want to change the input to the function, you have to change the constants 'ALICE_INPUT' and 'BOB_INPUT' in main.py lines 5-6.

Make sure that the sum of each input array is 15 or less, because the implementation uses a 4 bit adder, which will not give accurate results on integers higher than 4 bits.
