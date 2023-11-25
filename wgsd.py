# MIT License
#
# Copyright (c) 2022 Ferhat Geçdoğan All Rights Reserved.
# Distributed under the terms of the MIT License.
#
# wgsd (aka when gech stores data) - a data interface for my game,
# which is easier to parse and read.
# ----------
# https://github.com/ferhatgec/wgsd.py
# https://github.com/ferhatgec/wgsd
#
# some features:
#  dynamic casting (from, to: boolean, float, integer etc.)
#  built-in regenerating
#  validating nodes
#  fast (you know this is python) key-value changing
#
# syntax:
#
# # comment line
#
# profile1 =
# 	use_music; true;
# 	last_checkpoint; empty;
# 	character_name; gech;
# end; profile1;
#
# profile2 =
# 	empty; true;
# end; profile2;
#
# profile3 =
# 	age; 16;
# end; profile3;
#
#

class block_wgsd:
    def __init__(self):
        self.block_name = 'undefined'
        self.matched_datas = {}

class wgsd:
    def __init__(self):
        self.nodes = []
        self.raw_file = ''

    def __is_valid_integer(self, val):
        return str(val).isdigit()

    def __is_valid_float(self, val):
        if val.replace('.', '', 1).isdigit():
            return True
        return False

    def clear(self):
        self.nodes = []
        self.raw_file = ''

    def reparse_file(self, file):
        self.clear()
        self.parse_file()

    def generate(self):
        generate = ''

        for node in self.nodes:
            generate += node.block_name + ' =\n'

            for node_key in node.matched_datas:
                val = node.matched_datas[node_key]
                generate += f'    {str(node_key)};{str(val)};\n'

            generate += f'end; {node.block_name};\n'

        return generate

    def _reverse_pair_values(self, val):
        if val or not val: return str(val).lower()
        elif val == '': return 'empty'
        else: return str(val)


    def _pair_values(self, val):
        if val == 'true': return True
        elif val == 'false': return False
        elif val == 'empty': return ''
        elif self.__is_valid_integer(val): return int(val)
        elif self.__is_valid_float(val): return float(val)
        else: return val

    def change_key(self, block, key, replace):
        for node in self.nodes:
            if node.block_name == block:
                if key in node.matched_datas:
                    node.matched_datas[key] = self._reverse_pair_values(replace)

    def find_key(self, block, key):
        if block == '': block = 'undefined'

        for node in self.nodes:
            if node.block_name == block:
                if key in node.matched_datas:
                    return self._pair_values(node.matched_datas[key])
                else:
                    return ''
        
        return ''

    def _verify(self):
        pass

    def parse_file(self, file):
        is_block = False

        with open(file, 'r') as file_stream:
            for line in file_stream:
                self.raw_file += line + '\n'

        for line in self.raw_file.splitlines():
            line = line.strip()
            if len(line) > 0:
                if line[0] == '#':
                    continue
                else:
                    if not is_block:
                        is_block = True
                        x = line.split(' ')
                        if len(x) > 0 and x[1] == '=':
                            y = block_wgsd()
                            y.block_name = x[0]
                            self.nodes.append(y)

                        continue
                    else:
                        x = line.split(';')
                        if len(x) >= 2:
                            if x[0] == 'end':
                                is_block = False
                            else:
                                y = self.nodes[len(self.nodes) - 1]
                                y.matched_datas[x[0]] = ';'.join(x[1:]).strip()[:-1]

                        continue

        self._verify()
