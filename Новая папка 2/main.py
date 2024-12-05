import argparse
import struct
import csv


class UVMAssembler:
    def __init__(self, input_path, output_path, log_path):
        self.input_path = input_path
        self.output_path = output_path
        self.log_path = log_path

    def assemble(self):
        with open(self.input_path, 'r') as source, open(self.output_path, 'wb') as binary_file, open(self.log_path, 'w', newline='') as log_file:
            csv_writer = csv.writer(log_file)
            csv_writer.writerow(["Text", "Binary", "Description"])  # Заголовки для CSV

            for line in source:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                instruction, binary = self.parse_instruction(line)
                description = self.describe_instruction(line)

                # Записываем данные в CSV
                csv_writer.writerow([instruction, binary.hex(), description])

                # Записываем бинарные данные в файл
                binary_file.write(binary)

    def parse_instruction(self, line):
        parts = line.split()
        opcode = int(parts[0])

        # Применяем универсальный способ упаковки данных
        binary = self.pack_instruction(opcode, parts)

        return line, binary

    def pack_instruction(self, opcode, parts):
        # Динамически обрабатываем команды в зависимости от опкода
        if opcode == 106:  # Load constant
            constant = int(parts[1])
            return struct.pack('<BH', opcode, constant)
        elif opcode == 73:  # Read memory
            offset = int(parts[1])
            return struct.pack('<BH', opcode, offset)
        elif opcode == 104:  # Write memory
            address = int(parts[1])
            return struct.pack('<BH', opcode, address)
        elif opcode == 71:  # Unary NOT
            address = int(parts[1])
            return struct.pack('<BH', opcode, address)
        else:
            # Для нераспознанных опкодов можно вернуть их как есть или обработать как "неизвестный"
            return struct.pack('<B', opcode)

    def describe_instruction(self, line):
        """Добавляет описание инструкции для читаемости лога."""
        parts = line.split()
        opcode = int(parts[0])
        if opcode == 106:
            return f"Load constant {parts[1]} into the accumulator"
        elif opcode == 73:
            return f"Read memory at offset {parts[1]}"
        elif opcode == 104:
            return f"Write accumulator value to memory at address {parts[1]}"
        elif opcode == 71:
            return f"Perform bitwise NOT at memory address {parts[1]}"
        else:
            return f"Unknown opcode {opcode}"


class UVMInterpreter:
    def __init__(self, binary_path, result_path, memory_range):
        self.binary_path = binary_path
        self.result_path = result_path
        self.memory_range = memory_range
        self.memory = [0] * 1024  # Example memory size
        self.accumulator = 0

    def run(self):
        with open(self.binary_path, 'rb') as binary_file, open(self.result_path, 'w', newline='') as result_file:
            csv_writer = csv.writer(result_file)
            csv_writer.writerow(["Opcode", "Action", "Accumulator", "Memory"])

            while True:
                instruction = binary_file.read(3)  # Max command size
                if not instruction:
                    break
                self.execute_instruction(instruction, csv_writer)

    def execute_instruction(self, instruction, csv_writer):
        opcode = instruction[0]
        action_log = self.execute_opcode(opcode, instruction)

        # Записываем в CSV: опкод, действие, аккумулятор и состояние памяти
        csv_writer.writerow([opcode, action_log, self.accumulator, self.memory[:10]])  # Записываем первые 10 адресов памяти

    def execute_opcode(self, opcode, instruction):
        """Универсальная функция для выполнения инструкций по опкоду."""
        if opcode == 106:  # Load constant
            constant, = struct.unpack('<H', instruction[1:3])
            self.accumulator = constant
            return f"Load constant {constant} into accumulator"
        elif opcode == 73:  # Read memory
            offset, = struct.unpack('<H', instruction[1:3])
            self.accumulator = self.memory[offset]
            return f"Read memory at offset {offset} into accumulator"
        elif opcode == 104:  # Write memory
            address, = struct.unpack('<H', instruction[1:3])
            self.memory[address] = self.accumulator
            return f"Write accumulator value {self.accumulator} to memory at address {address}"
        elif opcode == 71:  # Unary NOT
            address, = struct.unpack('<H', instruction[1:3])
            self.memory[address] = ~self.memory[address]
            return f"Perform bitwise NOT at memory address {address}, result: {self.memory[address]}"
        else:
            return "Unknown opcode"

def main():
    parser = argparse.ArgumentParser(description="UVM Assembler and Interpreter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Команда assemble
    assemble_parser = subparsers.add_parser("assemble", help="Assemble a program into binary")
    assemble_parser.add_argument("input", help="Path to the assembly source file")
    assemble_parser.add_argument("output", help="Path to the output binary file")
    assemble_parser.add_argument("log", help="Path to the log CSV file")

    # Команда run
    run_parser = subparsers.add_parser("run", help="Run a binary file on the UVM")
    run_parser.add_argument("binary", help="Path to the binary file")
    run_parser.add_argument("result", help="Path to the result CSV file")
    run_parser.add_argument("memory_range", nargs=2, type=int, help="Memory range to output (start end)")

    args = parser.parse_args()

    if args.command == "assemble":
        assembler = UVMAssembler(args.input, args.output, args.log)
        assembler.assemble()
    elif args.command == "run":
        interpreter = UVMInterpreter(args.binary, args.result, tuple(args.memory_range))
        interpreter.run()


if __name__ == "__main__":
    main()
