

from setuptools import setup, find_packages
from package_manager import get_requirements


setup(
    name="iris_project_lib",  # nome do pacote (usado em Azure Artifacts)
    version="0.1.0",
    description="Lib de apoio para processamento e modelagem do Iris Dataset",
    author="Seu Nome ou Equipe",
    author_email="voce@empresa.com",
    packages=find_packages(where="source"),  # procura pacotes dentro da pasta `source/`
    package_dir={"": "source"},              # define que o root está em `source/`
    install_requires=requirements['main'],
    # install_requires=[
    #     "pandas",
    #     "scikit-learn",
    #     "mlflow",
    #     "seaborn"
    # ],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
