import logging, ot, util, yao, json, argparse
from abc import ABC, abstractmethod

# sum of input array has to be 15 or less, because the protocol uses a 4 bit adder
ALICE_INPUT = [1, 2, 3, 4]
BOB_INPUT = [4, 6, 2, 1]

logging.basicConfig(format="[%(levelname)s] %(message)s",
                    level=logging.WARNING)

class YaoGarbler(ABC):
    '''An abstract class for Yao garblers'''
    def __init__(self, circuits):
        circuits = util.parse_json(circuits)
        self.name = circuits['name']
        self.circuits = []

        # read circuit
        for circuit in circuits['circuits']:
            garbled_circuit = yao.GarbledCircuit(circuit)
            pbits = garbled_circuit.get_pbits()
            entry = {
                'circuit': circuit,
                'garbled_circuit': garbled_circuit,
                'garbled_tables': garbled_circuit.get_garbled_tables(),
                'keys': garbled_circuit.get_keys(),
                'pbits': pbits,
                'pbits_out': {w: pbits[w]
                              for w in circuit['out']},
            }
            self.circuits.append(entry)

    @abstractmethod
    def start(self):
        pass


class Alice(YaoGarbler):
    '''
    Alice creates a Yao circuit and sends it to Bob along with her
    encrypted inputs.
    '''
    def __init__(self):
        super().__init__('add.json')
        self.socket = util.GarblerSocket()
        self.ot = ot.ObliviousTransfer(self.socket, enabled=True)

    def start(self):
        '''Start Yao protocol.'''
        for circuit in self.circuits:
            to_send = {
                'circuit': circuit['circuit'],
                'garbled_tables': circuit['garbled_tables'],
                'pbits_out': circuit['pbits_out'],
            }
            
            # print what Alice sends to Bob to file
            with open('output/Alice_send_to_bob.json', 'w', encoding='utf-8') as f:
                json.dump({
                            'circuit': circuit['circuit'],
                            'garbled_tables': str(circuit['garbled_tables']),
                            'pbits_out': circuit['pbits_out'],
                        }, f, ensure_ascii=False, indent=4)
            logging.debug(f"Sending {circuit['circuit']['id']}")
            self.socket.send_wait(to_send)
            self.print(circuit)

    def print(self, entry):
        '''Print circuit evaluation

        Args:
            entry: A dict representing the circuit to evaluate.
        '''
        circuit, pbits, keys = entry['circuit'], entry['pbits'], entry['keys']
        outputs = circuit['out']
        a_wires = circuit.get('alice', [])  # Alice's wires
        a_inputs = {}  # map from Alice's wires to (key, encr_bit) inputs
        b_wires = circuit.get('bob', [])  # Bob's wires
        b_keys = {  # map from Bob's wires to a pair (key, encr_bit)
            w: self._get_encr_bits(pbits[w], key0, key1)
            for w, (key0, key1) in keys.items() if w in b_wires
        }

        print(f"======== {circuit['id']} ========")

        # Transform Alice input to binary
        bits_a = [int(i) for i in list(format(sum(ALICE_INPUT), '04b'))]

        # Map Alice's wires to (key, encr_bit)
        for i in range(len(a_wires)):
            a_inputs[a_wires[i]] = (keys[a_wires[i]][bits_a[i]],
                                    pbits[a_wires[i]] ^ bits_a[i])

        # Send Alice's encrypted inputs and keys to Bob
        result = self.ot.get_result(a_inputs, b_keys)

        # Format output
        str_bits_a = ' '.join(str(x) for x in bits_a)
        str_result = ' '.join([str(result[w]) for w in outputs])

        # print Alice's result to file
        with open('output/Alice_result.json', 'w', encoding='utf-8') as f:
            json.dump(
            {
            'alice': {'wires': ' '.join(map(str, a_wires)), 'binary': str_bits_a, 'decimalValue': int(''.join(str_bits_a.split(' ')), 2)},
            'result': {'wires': ' '.join(map(str, outputs)), 'binary': str_result, 'decimalValue': int(''.join(str_result.split(' ')), 2)},
            }, f, ensure_ascii=False, indent=4)

    def _get_encr_bits(self, pbit, key0, key1):
        return ((key0, 0 ^ pbit), (key1, 1 ^ pbit))


class Bob:
    '''
    Bob receives the Yao circuit from Alice, computes the results and sends
    them back.
    '''
    def __init__(self):
        self.socket = util.EvaluatorSocket()
        self.ot = ot.ObliviousTransfer(self.socket, enabled=True)

    def listen(self):
        '''Start listening for Alice messages.'''
        logging.info('Start listening')
        try:
            for entry in self.socket.poll_socket():
                self.socket.send(True)
                self.send_evaluation(entry)
        except KeyboardInterrupt:
            logging.info('Stop listening')

    def send_evaluation(self, entry):
        '''Evaluate yao circuit and send back the results.

        Args:
            entry: A dict representing the circuit to evaluate.
        '''
        # print the function on the combiend data
        with open('output/Function_on_combined_data.json', 'w', encoding='utf-8') as f:
                json.dump(entry['circuit'], f, ensure_ascii=False, indent=4)
        circuit, pbits_out = entry['circuit'], entry['pbits_out']
        garbled_tables = entry['garbled_tables']
        b_wires = circuit.get('bob', [])  # list of Bob's wires

        print(f"Received {circuit['id']}")

         # Transform Bob's input to binary
        bits_b = [int(i) for i in list(format(sum(BOB_INPUT), '04b'))]

        # Create dict mapping each wire of Bob to Bob's input
        b_inputs_clear = {
            b_wires[i]: bits_b[i]
            for i in range(len(b_wires))
        }

        # print BOB MPC Compute to file
        with open('output/Bob_MPC_compute.json', 'w', encoding='utf-8') as f:
            json.dump({'circuit': circuit, 'garbled_tables': str(garbled_tables), 'pbits_out': pbits_out, 'bob': b_inputs_clear}, f, ensure_ascii=False, indent=4)
        
        # Evaluate and send result to Alice
        self.ot.send_result(circuit, garbled_tables, pbits_out,
                            b_inputs_clear)


def main(party):
    logging.getLogger().setLevel(logging.WARNING)
    if party == 'alice':
        Alice().start()
    elif party == 'bob':
        Bob().listen()
    elif party == 'verify':
        # Verify the solution with a NON-MPC method, to find out if the result is correct
        with open('output/Bob_result.json') as bob_json, open('output/Alice_result.json') as alice_json:
            bobResult = json.load(bob_json)['bob']['decimalValue']
            aliceJSON = json.load(alice_json)
            aliceResult = aliceJSON['alice']['decimalValue']
            sumMPC = aliceJSON['result']['decimalValue']
            print(f"Bob's input: {bobResult}")
            print(f"Alice's input: {aliceResult}")
            print(f"Summed value using MPC: {sumMPC}")
            print(f"Summed value not using MPC: {bobResult + aliceResult}")
            print(f'Correct: {(bobResult + aliceResult) == sumMPC}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Yao protocol.')
    parser.add_argument('party', choices=['alice', 'bob', 'verify'], help='the yao party to run')
    main(party=parser.parse_args().party)
