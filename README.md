# Aplicações da Lei dos Grandes Números

Trabalho de Probabilidade que demonstra, com **dados reais**, as duas faces da Lei dos
Grandes Números (LGN):

1. **Frequência relativa → probabilidade** (caso discreto);
2. **Média amostral → esperança** (ambos os casos).

A estratégia é contrastar **dois fenômenos de naturezas opostas** para mostrar que a LGN
é universal, mas que a **velocidade** da convergência depende da variabilidade dos dados
(coeficiente de variação $\mathrm{CV}=\sigma/|\mu|$, via erro relativo $\mathrm{CV}/\sqrt{n}$).

| Caso | Dataset | Alvo "verdadeiro" | Convergência |
|------|---------|-------------------|--------------|
| **Discreto** | Mega-Sena (`data/sorteios.csv`) | **conhecido** a priori (0,10; 1/60; 30,5) | rápida e limpa (CV ≈ 0,57) |
| **Contínuo** | Retornos diários da PETR4.SA (`data/retornos.csv`) | **estimado** dos dados | lenta e ruidosa (CV ≈ 18) |

## Estrutura do projeto

```
.
├── README.md                       # este arquivo
├── Dockerfile                      # Python + JupyterLab + LaTeX (texlive)
├── docker-compose.yml              # sobe o ambiente em http://localhost:8888
├── requirements.txt                # dependências Python (versões fixadas)
├── data/
│   ├── sorteios.csv                # Mega-Sena (2.278 sorteios, já incluído)
│   └── retornos.csv                # gerado por scripts/gerar_retornos.py
├── scripts/
│   └── gerar_retornos.py           # baixa preços (yfinance) → retornos.csv
├── notebooks/
│   ├── 01_caso_discreto_megasena.ipynb
│   ├── 02_caso_continuo_retornos.ipynb
│   └── 03_sintese_comparacao.ipynb # síntese + ponte para o TCL
└── trabalho/
    ├── trabalho.tex                # relatório escrito (LaTeX)
    ├── trabalho.pdf                # PDF compilado
    └── figuras/                    # gráficos extraídos dos notebooks
```

## Como usar

Tudo roda dentro do container Docker (Python, JupyterLab e LaTeX já instalados).
Pré-requisito único: **Docker Desktop** (ou Docker Engine + Compose) instalado.

### 1. Subir o ambiente

```bash
docker compose up --build -d
```

Acesse o **JupyterLab** em <http://localhost:8888> (sem senha/token — uso local).
A pasta do projeto é montada como volume, então tudo que você editar persiste no host.
Na primeira vez o build é demorado (instala texlive/LaTeX); nas próximas é instantâneo.

### 2. (Re)gerar os retornos financeiros

```bash
docker compose exec analise python scripts/gerar_retornos.py
```

O script é parametrizável:

```bash
# Outra ação ou índice (B3 usa sufixo .SA; índices usam ^)
docker compose exec analise python scripts/gerar_retornos.py --ticker VALE3.SA
docker compose exec analise python scripts/gerar_retornos.py --ticker ^BVSP --anos 15
```

Ao final, imprime um resumo de sanidade (nº de observações, média, desvio e o
coeficiente de variação dos retornos). **Requer internet** em tempo de execução.

### 3. Rodar os notebooks

Abra-os pelo JupyterLab (pasta `notebooks/`) e use *Run → Run All Cells*. Eles já vêm
com os gráficos embutidos; reexecutar é opcional.

### 4. Compilar o relatório (PDF)

```bash
docker compose exec analise latexmk -pdf -cd trabalho/trabalho.tex
```

O `-cd` entra na pasta do `.tex` (para encontrar `figuras/`) e o latexmk roda quantas
passadas forem necessárias para resolver numeração e referências. Para limpar os
auxiliares (mantendo o PDF): `latexmk -c -cd trabalho/trabalho.tex`.

> Antes de gerar a versão final, preencha os campos de **disciplina** e **instituição**
> no topo de `trabalho/trabalho.tex` (os autores já estão preenchidos).

### 5. Visualizar os resultados

Como o projeto é montado como volume, todos os arquivos gerados aparecem direto na sua
pasta no host:

- **Notebooks (com gráficos):** abra-os no JupyterLab (<http://localhost:8888>), ou em
  qualquer leitor de `.ipynb` (VS Code, nbviewer).
- **Relatório final:** abra `trabalho/trabalho.pdf` em qualquer leitor de PDF.

### 6. Parar o ambiente

```bash
docker compose down
```

Os dados, notebooks e o PDF continuam salvos no host (só o container é encerrado).

## Notas técnicas

- `yfinance` está fixado em `1.5.1`: versões antigas (0.2.x) quebram com a API atual do
  Yahoo (erro `Expecting value: line 1 column 1`).
- Os experimentos de reamostragem usam sementes fixas (`numpy.random.default_rng`), de
  modo que os resultados são **reprodutíveis**.
- A base da Mega-Sena cobre o período de **1996 a 2018** (2.278 sorteios).
