import tarfile
import json
import tkinter as tk
from datetime import datetime

class Emulator:
    def __init__(self, config):
        self.config = config
        self.current_dir = '/home/user'  # начальная директория
        self.fs_archive = config['fs_archive']
        self.log_file = config['log_file']

    def run_command(self, command_line):
        # Разбор команды и аргументов
        command_parts = command_line.split()
        command = command_parts[0]
        args = command_parts[1:] if len(command_parts) > 1 else []

        if command == "ls":
            return self.ls(args)
        elif command == "cd":
            return self.cd(args)
        elif command == "exit":
            return self.exit_shell()
        elif command == "uname":
            return self.uname()
        elif command == "head":
            return self.head(args)
        else:
            return f"Unknown command: {command}"

    def ls(self, args):
        path = args[0] if args else self.current_dir
        result = []
        with tarfile.open(self.fs_archive, 'r') as tar:
            for member in tar.getmembers():
                if member.name.startswith(path):
                    result.append(member.name)
        return "\n".join(result)

    def cd(self, args):
        if not args:
            return "cd: missing argument"
        
        path = args[0]
        with tarfile.open(self.fs_archive, 'r') as tar:
            if path in [m.name for m in tar.getmembers() if m.isdir()]:
                self.current_dir = path
                return f"Changed directory to {path}"
            else:
                return f"cd: no such directory: {path}"

    def exit_shell(self):
        self.log_action('exit', [])
        print("Exiting shell...")
        exit()

    def uname(self):
        return self.config["computer_name"]

    def head(self, args):
        if not args:
            return "head: missing filename argument"
        
        file_path = args[0]
        n = int(args[1]) if len(args) > 1 else 10
        result = []

        with tarfile.open(self.fs_archive, 'r') as tar:
            try:
                file = tar.extractfile(file_path)
                for i in range(n):
                    line = file.readline().decode('utf-8').strip()
                    if line:
                        result.append(line)
                    else:
                        break
            except KeyError:
                return f"head: no such file: {file_path}"
        
        return "\n".join(result)

    def log_action(self, command, args):
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        with open(self.log_file, 'a') as log:
            log.write(f"{timestamp},{command},{' '.join(args)}\n")


class ShellGUI(tk.Tk):
    def __init__(self, emulator):
        super().__init__()
        self.emulator = emulator
        self.title("Shell Emulator")
        self.geometry("600x400")

        self.command_input = tk.Entry(self)
        self.command_input.pack(pady=10, fill=tk.X)

        self.output_text = tk.Text(self)
        self.output_text.pack(pady=10, expand=True, fill=tk.BOTH)

        self.run_button = tk.Button(self, text="Run", command=self.run_command)
        self.run_button.pack()

    def run_command(self):
        command = self.command_input.get()
        result = self.emulator.run_command(command)
        self.output_text.insert(tk.END, result + '\n')
        self.command_input.delete(0, tk.END)


if __name__ == "__main__":
    # Пример конфигурации
    config = {
        "computer_name": "MyComputer",
        "fs_archive": "filesystem.tar",
        "log_file": "log.csv"
    }

    emulator = Emulator(config)
    app = ShellGUI(emulator)
    app.mainloop()


import unittest
from unittest.mock import patch
from io import StringIO

class TestLs(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def test_ls_valid_directory(self, mock_stdout):
        # Симулируем наличие файлов в /home/user
        with patch('tarfile.open') as mock_tarfile:
            mock_tarfile.return_value.getmembers.return_value = [
                type('tarinfo', (object,), {'name': '/home/user/file1'})(),
                type('tarinfo', (object,), {'name': '/home/user/file2'})()
            ]
            emulator = Emulator(config)
            emulator.ls('/home/user')
            output = mock_stdout.getvalue().strip()
            self.assertIn('file1', output)
            self.assertIn('file2', output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_ls_empty_directory(self, mock_stdout):
        # Симулируем пустую директорию
        with patch('tarfile.open') as mock_tarfile:
            mock_tarfile.return_value.getmembers.return_value = []
            emulator = Emulator(config)
            emulator.ls('/home/user/empty_dir')
            output = mock_stdout.getvalue().strip()
            self.assertEqual(output, "")

    @patch('sys.stdout', new_callable=StringIO)
    def test_ls_nonexistent_directory(self, mock_stdout):
        # Симулируем несуществующую директорию
        with patch('tarfile.open') as mock_tarfile:
            mock_tarfile.return_value.getmembers.return_value = []
            emulator = Emulator(config)
            result = emulator.ls('/home/user/nonexistent_dir')
            self.assertIn('no such directory', result)

class TestCd(unittest.TestCase):

    def test_cd_valid_directory(self):
        # Симулируем существующую директорию
        with patch('tarfile.open') as mock_tarfile:
            mock_tarfile.return_value.getmembers.return_value = [
                type('tarinfo', (object,), {'name': '/home/user/documents', 'isdirectory': True})()
            ]
            emulator = Emulator(config)
            result = emulator.cd('/home/user/documents')
            self.assertEqual(emulator.current_dir, '/home/user/documents')
            self.assertIn('Changed directory', result)

    def test_cd_nonexistent_directory(self):
        # Симулируем несуществующую директорию
        with patch('tarfile.open') as mock_tarfile:
            mock_tarfile.return_value.getmembers.return_value = []
            emulator = Emulator(config)
            result = emulator.cd('/home/user/nonexistent_dir')
            self.assertIn('no such directory', result)

    def test_cd_missing_argument(self):
        # Проверка на отсутствие аргумента
        emulator = Emulator(config)
        result = emulator.cd([])
        self.assertEqual(result, 'cd: missing argument')

class TestExit(unittest.TestCase):

    @patch('sys.exit')
    def test_exit(self, mock_exit):
        emulator = Emulator(config)
        with patch('builtins.print') as mock_print:
            emulator.exit_shell()
            mock_print.assert_called_with("Exiting shell...")
            mock_exit.assert_called_once()

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_exit_log_action(self, mock_open):
        emulator = Emulator(config)
        emulator.exit_shell()
        # Проверка, что логирование произошло
        mock_open.assert_called_with(config['log_file'], 'a')

    @patch('sys.exit')
    def test_exit_multiple(self, mock_exit):
        emulator = Emulator(config)
        emulator.exit_shell()  # Первый выход
        with self.assertRaises(SystemExit):
            emulator.exit_shell()  # Второй выход должен вызвать ошибку

class TestUname(unittest.TestCase):

    def test_uname(self):
        emulator = Emulator(config)
        result = emulator.uname()
        self.assertEqual(result, 'MyComputer')

    def test_uname_empty(self):
        empty_config = {"computer_name": ""}
        emulator = Emulator(empty_config)
        result = emulator.uname()
        self.assertEqual(result, "")

    def test_uname_missing_config(self):
        missing_config = {}
        emulator = Emulator(missing_config)
        with self.assertRaises(KeyError):
            emulator.uname()

class TestHead(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def test_head_valid_file(self, mock_stdout):
        # Симулируем чтение файла
        with patch('tarfile.open') as mock_tarfile:
            mock_file = unittest.mock.Mock()
            mock_file.readline.return_value = b'Line 1\n'
            mock_tarfile.return_value.extractfile.return_value = mock_file
            emulator = Emulator(config)
            result = emulator.head(['/home/user/file.txt', 2])
            output = mock_stdout.getvalue().strip()
            self.assertIn('Line 1', output)

    def test_head_nonexistent_file(self):
        # Симулируем несуществующий файл
        with patch('tarfile.open') as mock_tarfile:
            mock_tarfile.return_value.extractfile.side_effect = KeyError
            emulator = Emulator(config)
            result = emulator.head(['/home/user/nonexistent_file.txt'])
            self.assertIn('no such file', result)

    def test_head_missing_argument(self):
        # Проверка на отсутствие аргумента
        emulator = Emulator(config)
        result = emulator.head([])
        self.assertEqual(result, 'head: missing filename argument')

if __name__ == '__main__':
    unittest.main()

