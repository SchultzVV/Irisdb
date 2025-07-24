"""
Não alterar este arquivo.
A responsabilidade deste arquivo é de gerenciar
os requirements da biblioteca criada com maior
facilidade.
"""
import os
from typing import List, Dict


class Requirements:
    """Classe responsável por facilitar geração de requirements.

    Todas as bibliotecas que forem escritas
    no arquivo requirements.txt, ou requirements.*.txt,
    serão passadas para o setup.py de maneira automática.
    """

    def list_files(self) -> str:
        """Lista os arquivos do diretório."""
        return os.listdir()

    def get_requirements_files(self):
        """Pega todos os arquivos que começam com requirements."""
        return [file for file in self.list_files() if file.startswith("requirements")]

    def parse_requirements(self, file: str):
        """Pega as dependências do arquivo de requirements."""
        with open(file, "r") as f:
            return f.read().splitlines()

    def file_name(self, file_name: str):
        """Pega o nome do arquivo de requirements."""
        if file_name.split(".")[1] == "txt":
            return "main"
        else:
            return file_name.split(".")[1]

    def generate_requirements_dict(self) -> Dict[str, List[str]]:
        """Gera um dicionário com os arquivos de requirements e suas dependências."""
        return {
            self.file_name(file): self.parse_requirements(file)
            for file in self.get_requirements_files()
        }


def get_requirements():
    """Executa a classe Requirements e retorna um dicionário com os arquivos de requirements."""
    requirements = Requirements()
    return requirements.generate_requirements_dict()
