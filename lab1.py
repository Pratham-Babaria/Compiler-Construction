import io
import os
import sys
import getopt

class Scanner:

    def __init__(self, file_path: str):
        self.file = open(file_path, 'r')
        self.file.seek(0, io.SEEK_END)
        self.size = self.file.tell()
        self.file.seek(0, io.SEEK_SET)
        self.current_line = ''
        self.line_num = 0

    def __del__(self):
        self.file.close()

    def next_line(self):
        self.current_line = ''

    def next_token(self):
        if self.size == self.file.tell() and not self.current_line:
            return self.line_num, 'EOF', 'EOF'

        if not self.current_line:
            self.current_line = self.file.readline().rstrip()
            self.line_num += 1

        # check if it is a blank line
        if not self.current_line:
            return self.line_num, 'BLANK', ''

        if '//' in self.current_line:
            self.current_line = self.current_line.split('//')[0].rstrip()
            return self.line_num, 'COMMENT', ''

        # if we get here, we know the remaining parts of the line are not a comment, not blank, and no eof
        # so it is a normal token

        self.current_line = self.current_line.lstrip()
        token = ''
        type = ''
        while self.current_line:
            cur_char = self.current_line[0]
            if cur_char == '=' and token == '':
                type = 'ASSIGN'
            elif cur_char == 'r' and self.current_line[1] != 's' and token == '':
                type = 'REG'
            elif cur_char >= 'a' and cur_char <= 'z' and token == '':
                type = 'CMD'
            elif cur_char == ',' and token == '':
                type = 'COMMA'
            elif token == '':
                type = 'NUM'
            if cur_char == ',' and token:
                return self.line_num, type, token
            elif cur_char == ',':
                self.current_line = self.current_line[1:]
                return self.line_num, type, ','
            elif cur_char == '=' and len(token) > 0:
                return self.line_num, type, token
            elif token == '=>':
                return self.line_num, type, token
            elif cur_char == ' ' or cur_char == '\t':
                self.current_line = self.current_line.lstrip()
                return self.line_num, type, token
            else:
                token += self.current_line[0]
                self.current_line = self.current_line[1:]

            if type == 'NUM' and not token.isdigit():
                return self.line_num, 'INVALID_NUM', token

        if token:
            return self.line_num, type, token
        self.current_line = ''


class Parser:
    def __init__(self, scanner: Scanner):
        self.scanner = scanner
        self.repr = []
        self.valid_opcodes = ['load', 'loadI', 'store', 'add', 'sub', 'mult', 'lshift', 'rshift', 'output', 'nop', 'EOF']
        self.three_reg_opcodes = ['add', 'sub', 'mult', 'lshift', 'rshift']
        self.result_string = ''
        self.errors_found = False
        self.line_num = 0

    def __del__(self):
        return

    def syntax_error(self, line, symbol):
        print(f'ERROR {line}: syntax error on symbol {symbol}')
        self.scanner.next_line()
        self.errors_found = True

    def validate_reg(self, reg: str) -> str:
        if reg.startswith('r') and reg[1:].isdigit():
            return reg[1:]
        else:
            self.syntax_error(self.line_num, reg)
            return '-'

    def validate_imm(self, imm: str) -> str:
        if imm.isdigit() or (imm.startswith('-') and imm[1:].isdigit()):
            return imm
        else:
            self.syntax_error(self.line_num, imm)
            return '-'

    def print_status(self):
        print(self.result_string)

    def print_intermediate(self):
        for entry in self.repr:
            print(entry)

    def parse(self):
        line = 0
        while True:
            self.line_num += 1
            line, type, opcode = self.scanner.next_token()
            #if we got a comment, just continue
            if type == 'COMMENT':
                continue
            if type == 'BLANK':
                continue

            sr1 = '-'
            sr2 = '-'
            sr3 = '-'
            vr1 = '-'
            pr1 = '-'
            nu1 = '-'
            vr2 = '-'
            pr2 = '-'
            nu2 = '-'
            vr3 = '-'
            pr3 = '-'
            nu3 = '-'
            token = ''

            if opcode not in self.valid_opcodes:
                self.syntax_error(self.line_num, opcode)
                continue

            if type == 'EOF':
                break
            elif type != 'CMD':
                self.syntax_error(self.line_num, opcode)

            elif opcode == 'output':
                line, type, sr1 = self.scanner.next_token()
                if type != 'NUM':
                    self.syntax_error(self.line_num, sr1)
                    continue

            elif opcode == 'loadI':
                line, type, sr1 = self.scanner.next_token()
                if type == 'INVALID_NUM':
                    self.syntax_error(self.line_num, sr1)
                    continue
                elif type != 'NUM':
                    self.syntax_error(self.line_num, sr1)
                    continue
                line, type, token = self.scanner.next_token()
                if type != 'ASSIGN':
                    self.syntax_error(self.line_num, token)
                    continue
                line, type, sr3 = self.scanner.next_token()
                if type != 'REG':
                    self.syntax_error(self.line_num, sr3)
                    continue

            elif opcode != 'nop':
                line, type, sr1 = self.scanner.next_token()
                if type != 'REG':
                    self.syntax_error(self.line_num, sr1)
                    continue
                if opcode in self.three_reg_opcodes:
                    line, type, token = self.scanner.next_token()
                    if type != 'COMMA':
                        self.syntax_error(self.line_num, token)
                        continue
                    line, type, sr2 = self.scanner.next_token()
                    if type != 'REG':
                        self.syntax_error(self.line_num, sr2)
                        continue
                    line, type, token = self.scanner.next_token()
                    if type != 'ASSIGN':
                        self.syntax_error(self.line_num, token)
                        continue
                    line, type, sr3 = self.scanner.next_token()
                    if type != 'REG':
                        self.syntax_error(self.line_num, sr3)
                        continue
                else:
                    line, type, token = self.scanner.next_token()
                    if type != 'ASSIGN':
                        self.syntax_error(self.line_num, token)
                        continue

                    line, type, sr3 = self.scanner.next_token()
                    if type == 'EOF' or not sr3:
                        self.syntax_error(self.line_num, 'missing register after =>')
                        continue
                    if type != 'REG':
                        self.syntax_error(self.line_num, sr3)
                        continue

            self.repr.append([line, opcode, sr1, pr1, vr1, nu1, sr2, pr2, vr2, nu2, sr3, pr3, vr3, nu3])

        if self.errors_found:
            self.result_string = f"Parse found errors."
        else:
            self.result_string = f"Parse succeeded. Processed {len(self.repr)} operations."


def display_help():
    print("Usage: 412fe [options] <file>")
    print("Options:")
    print("  -h          Display this help message")
    print("  -s <name>   Scan the specified file and print the tokens")
    print("  -p <name>   Parse the specified file and report success or errors")
    print("  -r <name>   Parse and print the intermediate representation of the specified file")


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hs:p:r:')
    except getopt.GetoptError as err:
        print(f"Error: {err}", file=sys.stderr)
        display_help()
        sys.exit(2)

    if len(opts) == 0:
        if len(args) == 0:
            print("ERROR: No input file provided.", file=sys.stderr)
            display_help()
            sys.exit(2)
        else:
            file_path = args[0]
            if not os.path.isfile(file_path):
                print(f"ERROR: file does not exist")
                sys.exit(2)
            scanner = Scanner(file_path)
            parser = Parser(scanner)
            parser.parse()
            parser.print_status()
            sys.exit(0)

    option_dict = dict(opts)
    if '-h' in option_dict:
        display_help()
    elif '-s' in option_dict:
        file_path = option_dict['-s']
        if not os.path.isfile(file_path):
            print(f"ERROR: file does not exist")
            sys.exit(2)
        scanner = Scanner(file_path)
        line_number, type, token = scanner.next_token()
        while token != 'EOF':
            print(f"Line {line_number}: Type: {type}, Token: {token}")
            line_number, type, token = scanner.next_token()
    elif '-p' in option_dict:
        file_path = option_dict['-p']
        if not os.path.isfile(file_path):
            print(f"ERROR: file does not exist")
            sys.exit(2)
        scanner = Scanner(file_path)
        parser = Parser(scanner)
        parser.parse()
        parser.print_status()
    elif '-r' in option_dict:
        file_path = option_dict['-r']
        if not os.path.isfile(file_path):
            print(f"ERROR: file does not exist")
            sys.exit(2)
        scanner = Scanner(file_path)
        parser = Parser(scanner)
        parser.parse()
        parser.print_intermediate()

