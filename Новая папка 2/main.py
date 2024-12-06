import argparse
import struct
import csv


class UVMAssembler:
    def __init__(self, input_path, output_path, log_path):
        self.input_path = input_path
        self.output_path = output_path
        self.log_path = log_path

    def assemble(self):
        with open(self.input_path, 'r') as source, \
             open(self.output_path, 'wb') as binary_file, \
             open(self.log_path, 'w', newline='', encoding='utf-8') as log_file:
            csv_writer = csv.writer(log_file)
            csv_writer.writerow(["Инструкция", "Бинарный код", "Описание"])

            for line in source:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    instruction, binary, description = self.parse_instruction(line)
                    csv_writer.writerow([instruction, binary.hex(), description])
                    binary_file.write(binary)
                except ValueError as e:
                    print(f"Ошибка обработки строки: {line}")
                    print(e)

    def parse_instruction(self, line):
        parts = line.split()
        opcode = int(parts[0])

        if opcode == 41:  # Загрузка константы
            register = int(parts[1])
            constant = int(parts[2])
            binary = struct.pack('<BHB', opcode, constant, register)
            description = f"Загрузка константы {constant} в регистр {register}"

        elif opcode == 79:  # Чтение из памяти
            register = int(parts[1])
            address = int(parts[2])
            binary = struct.pack('<BHB', opcode, address, register)
            description = f"Чтение из памяти по адресу {address} в регистр {register}"

        elif opcode == 168:  # Запись в память
            address = int(parts[1])
            value = int(parts[2])
            binary = struct.pack('<BHB', opcode, address, value)
            description = f"Запись значения {value} по адресу {address}"

        elif opcode == 226:  # popcnt
            register_b = int(parts[1])
            register_c = int(parts[2])
            binary = struct.pack('<BB', opcode, (register_b << 3) | register_c)
            description = f"popcnt: регистр B={register_b}, регистр C={register_c}"

        elif opcode == 201:  # Сброс регистров
            binary = struct.pack('<B', opcode)
            description = "Сброс всех регистров"

        elif opcode == 4:  # Запись значения из регистра в память
            reg1 = int(parts[1])
            reg2 = int(parts[2])
            binary = struct.pack('<BB', opcode, (reg1 << 3) | reg2)
            description = f"Запись значения из регистра {reg2} в память по адресу из регистра {reg1}"

        else:
            raise ValueError(f"Неизвестный опкод: {opcode}")

        return line, binary, description


class UVMInterpreter:
    def __init__(self, binary_path, result_path, memory_range):
        self.binary_path = binary_path
        self.result_path = result_path
        self.memory_range = memory_range
        self.memory = [0] * 1024
        self.registers = [0] * 8

    def run(self):
        with open(self.binary_path, 'rb') as binary_file:
            while instruction := binary_file.read(4):  # Максимум 4 байта
                self.execute_instruction(instruction)
        self.write_results()

    def execute_instruction(self, instruction):
        opcode = instruction[0]

        if opcode == 41:  # Загрузка константы
            constant, register = struct.unpack('<HB', instruction[1:])
            self.registers[register] = constant

        elif opcode == 79:  # Чтение из памяти
            address, register = struct.unpack('<HB', instruction[1:])
            self.registers[register] = self.memory[address]

        elif opcode == 168:  # Запись в память
            address, value = struct.unpack('<HB', instruction[1:])
            self.memory[address] = value

        elif opcode == 226:  # popcnt
            reg_b = (instruction[1] >> 3) & 0b111
            reg_c = instruction[1] & 0b111
            self.memory[self.registers[reg_c]] = bin(self.registers[reg_b]).count('1')

        elif opcode == 201:  # Сброс регистров
            self.registers = [0] * 8

        elif opcode == 4:  # Запись значения из регистра в память
            reg1 = (instruction[1] >> 3) & 0b111
            reg2 = instruction[1] & 0b111
            self.memory[self.registers[reg1]] = self.registers[reg2]

    def write_results(self):
        with open(self.result_path, 'w', newline='', encoding='utf-8') as result_file:
            csv_writer = csv.writer(result_file)
            csv_writer.writerow(["Адрес/Регистр", "Значение"])

            # Печатаем регистры
            for i, reg in enumerate(self.registers):
                csv_writer.writerow([f"Регистр {i}", reg])

            # Печатаем память в указанном диапазоне
            for address in range(self.memory_range[0], self.memory_range[1] + 1):
                csv_writer.writerow([f"Память {address}", self.memory[address]])


def main():
    parser = argparse.ArgumentParser(description="Ассемблер и интерпретатор для виртуальной машины.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assemble_parser = subparsers.add_parser("assemble", help="Сборка программы в бинарный формат")
    assemble_parser.add_argument("input", help="Путь к текстовому файлу с инструкциями")
    assemble_parser.add_argument("output", help="Путь к бинарному файлу")
    assemble_parser.add_argument("log", help="Путь к файлу логов")

    run_parser = subparsers.add_parser("run", help="Выполнение программы")
    run_parser.add_argument("binary", help="Путь к бинарному файлу")
    run_parser.add_argument("result", help="Путь к файлу результатов")
    run_parser.add_argument("memory_range", nargs=2, type=int, help="Диапазон памяти для вывода (начало конец)")

    args = parser.parse_args()

    if args.command == "assemble":
        assembler = UVMAssembler(args.input, args.output, args.log)
        assembler.assemble()
    elif args.command == "run":
        interpreter = UVMInterpreter(args.binary, args.result, tuple(args.memory_range))
        interpreter.run()


if __name__ == "__main__":
    main()
